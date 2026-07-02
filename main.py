"""
Port of jhawthorn/snek (Ruby Battlesnake) to CodeClash Python arena format.

Original: https://github.com/jhawthorn/snek  (Rails app, pure Ruby, no C ext in
current HEAD -- flood-fill/BFS is implemented in Ruby in board_bfs.rb).

Strategy (faithful reimplementation of the Ruby MoveDecider + GameScorer):
  1. Consider up to 4 living snakes (self + 3 nearest enemies by Manhattan dist).
  2. For each considered snake, enumerate "reasonable" moves = moves not out of
     bounds and not into an occupied cell (all bodies minus their last segment).
  3. Form every combination of those moves and simulate one full game step
     (Battlesnake rules: move heads, decrement health, eat food -> grow+heal,
     resolve out-of-bounds / body / head-to-head collisions, vacate tails).
  4. Score each resulting position with GameScorer (Voronoi flood-fill, reachable
     space, distance to food, length/health, enemy penalties).
  5. For each of the player's own actions, take all combinations where the player
     played that action; the action's value is (min score, avg score). Pick the
     action maximizing that pair (paranoid worst-case, tie-broken by average).

Coordinate system matches Battlesnake v1 (bottom-left origin, up=y+1). The Ruby
source already uses this convention, so no remapping is needed.

FIDELITY: faithful.
"""

import sys
from collections import defaultdict

ACTIONS = ["up", "down", "left", "right"]
_DELTA = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}

SCORE_MIN = -999999999
SCORE_MAX = 999999999


def _move_point(p, direction):
    dx, dy = _DELTA[direction]
    return (p[0] + dx, p[1] + dy)


# ---------------------------------------------------------------------------
# Snake / Board model (mutable copies for simulation)
# ---------------------------------------------------------------------------

class Snake:
    __slots__ = ("id", "name", "health", "body")

    def __init__(self, sid, name, health, body):
        self.id = sid
        self.name = name
        self.health = health
        self.body = body  # list of (x, y) tuples, head first

    def copy(self):
        return Snake(self.id, self.name, self.health, list(self.body))

    def alive(self):
        return self.health > 0

    @property
    def head(self):
        return self.body[0]

    @property
    def length(self):
        return len(self.body)

    def tail(self):
        # Ruby #tail: body excluding leading segments equal to head, i.e. the
        # cells that are truly occupied by the body (stacked head at spawn/grow
        # collapses). Returns the sublist starting from the first non-head cell.
        head = self.body[0]
        i = 1
        n = len(self.body)
        while i < n and self.body[i] == head:
            i += 1
        return self.body[i:]

    def die(self):
        self.health = 0


class Board:
    def __init__(self, width, height, snakes, food, hazards):
        self.width = width
        self.height = height
        self.snakes = snakes
        self.food = set(food)
        self.hazards = set(hazards)

    def living_snakes(self):
        return [s for s in self.snakes if s.alive()]

    def copy(self):
        return Board(self.width, self.height,
                     [s.copy() for s in self.snakes],
                     set(self.food), set(self.hazards))

    def out_of_bounds(self, p):
        x, y = p
        return x < 0 or y < 0 or x >= self.width or y >= self.height

    def simulate(self, actions):
        """Faithful port of Board#simulate! (mutates in place)."""
        living = self.living_snakes()

        # Move heads (or duplicate head if no action given).
        for snake in living:
            action = actions.get(snake.id)
            if action:
                snake.body.insert(0, _move_point(snake.head, action))
            else:
                snake.body.insert(0, snake.head)

        # Health / hazards.
        for snake in living:
            if snake.head in self.hazards:
                snake.health -= 14
            snake.health -= 1

        # Vacate tail.
        for snake in living:
            snake.body.pop()

        # Eat food -> grow + heal.
        eaten = []
        for snake in living:
            if snake.head in self.food:
                eaten.append(snake.head)
                snake.body.append(snake.body[-1])
                snake.health = 100
        for f in eaten:
            self.food.discard(f)

        # Collision resolution.
        heads = defaultdict(list)
        for snake in living:
            heads[snake.head].append(snake)

        walls = set()
        for snake in living:
            for seg in snake.tail():
                walls.add(seg)

        # Faithful replication of Ruby Board#simulate!: the death-resolution
        # loop iterates over @living_snakes while deleting dead snakes from that
        # SAME array. Ruby's Array#each advances a live cursor, so deleting the
        # element at the current index shifts the next element into that slot and
        # then the cursor skips it. That skipped snake never gets its death check
        # and (buggily, but faithfully) survives the turn. We emulate this exact
        # index/deletion behavior over a mutable list.
        alive_list = list(living)
        i = 0
        while i < len(alive_list):
            snake = alive_list[i]
            died = False
            if self.out_of_bounds(snake.head):
                snake.die()
                died = True
            elif snake.head in walls:
                snake.die()
                died = True
            else:
                for other in heads[snake.head]:
                    if other is snake:
                        continue
                    if other.length >= snake.length:
                        snake.die()
                        died = True
                        break
            if died:
                del alive_list[i]
            i += 1


# ---------------------------------------------------------------------------
# Game wrapper
# ---------------------------------------------------------------------------

class Game:
    def __init__(self, self_id, turn, board):
        self.self_id = self_id
        self.turn = turn
        self.board = board

    @property
    def snakes(self):
        return self.board.snakes

    def player(self):
        for s in self.snakes:
            if s.id == self.self_id:
                return s
        return None

    def enemies(self):
        return [s for s in self.snakes if s.id != self.self_id]

    def copy(self):
        return Game(self.self_id, self.turn, self.board.copy())

    def simulate(self, actions):
        g = self.copy()
        g.board.simulate(actions)
        return g


# ---------------------------------------------------------------------------
# BFS / Voronoi flood-fill (port of BoardBFS)
# ---------------------------------------------------------------------------

class BoardBFS:
    """Multi-source BFS. Each free tile is claimed by the nearest snake head
    (ties broken toward longer snakes, matching the sort). Also records the
    distance from each snake head to the nearest food."""

    def __init__(self, board, targets=None):
        self.board = board
        self.tiles = defaultdict(int)          # snake.id -> claimed tile count
        self.distance_to_food = {}             # snake.id -> distance

        snakes = list(board.living_snakes())
        snakes.sort(key=lambda s: -s.length)
        self.snakes = snakes
        self.targets = (sorted(targets, key=lambda s: -s.length)
                        if targets is not None else snakes)
        self._targets_all = targets is None
        self._calculate()

    def _calculate(self):
        board = self.board
        w, h = board.width, board.height

        visited = set()
        # Tail cells of targets are treated as visited (they'll vacate).
        for snake in self.targets:
            for seg in snake.tail():
                visited.add(seg)
        # When only some snakes are targets, other snakes' whole bodies block.
        if not self._targets_all:
            tset = {s.id for s in self.targets}
            for snake in self.snakes:
                if snake.id in tset:
                    continue
                for seg in snake.body:
                    visited.add(seg)

        food = set(board.food)

        next_queue = []
        for snake in self.targets:
            head = snake.head
            if not board.out_of_bounds(head):
                next_queue.append((head[0], head[1], snake))

        distance = 0
        while next_queue:
            queue = next_queue
            next_queue = []
            for x, y, snake in queue:
                cell = (x, y)
                if cell in visited:
                    continue
                visited.add(cell)
                self.tiles[snake.id] += 1
                if cell in food and snake.id not in self.distance_to_food:
                    self.distance_to_food[snake.id] = distance
                if x < w - 1:
                    next_queue.append((x + 1, y, snake))
                if x > 0:
                    next_queue.append((x - 1, y, snake))
                if y < h - 1:
                    next_queue.append((x, y + 1, snake))
                if y > 0:
                    next_queue.append((x, y - 1, snake))

            # Re-open trailing tail segments that have vacated by this distance.
            # Port of the Ruby loop: for snakes with body.length < distance,
            # if length < distance-1 and body[-distance] != body[-distance-1]
            # and no food yet found, un-visit body[-distance].
            for snake in self.snakes:
                length = snake.length
                if length >= distance:
                    continue
                if (length < distance - 1
                        and snake.id not in self.distance_to_food):
                    # body[-distance] / body[-distance-1] must be valid indices
                    if distance <= length and (distance + 1) <= length:
                        if snake.body[-distance] != snake.body[-distance - 1]:
                            visited.discard(snake.body[-distance])
            distance += 1


# ---------------------------------------------------------------------------
# GameScorer (port of GameScorer)
# ---------------------------------------------------------------------------

class GameScorer:
    def __init__(self, game):
        self.game = game
        self.bfs = BoardBFS(game.board)
        player = game.player()
        self.reachable_bfs = BoardBFS(game.board, [player]) if player else None

    def score(self):
        game = self.game
        player = game.player()
        if player is None or not player.alive():
            return SCORE_MIN

        live_enemies = [e for e in game.enemies() if e.alive()]
        any_enemies = len(game.enemies()) > 0

        if not live_enemies and any_enemies:
            return SCORE_MAX

        if self.bfs.tiles[player.id] <= 1:
            return SCORE_MIN + 10

        dist_food = self.bfs.distance_to_food.get(player.id)
        if dist_food is None:
            dist_food = game.board.width * 2
        if dist_food > 10:
            dist_food = dist_food / 100.0 + 10
        if player.health < 20:
            dist_food *= 10

        enemies = live_enemies
        player_voronoi = self.bfs.tiles[player.id]
        player_reachable = self.reachable_bfs.tiles[player.id]
        if player_reachable > 10:
            player_reachable = 10

        enemy_max_length = max((e.length for e in enemies), default=0)
        enemy_total_length = sum(e.length for e in enemies)

        total = 0.0
        total += 25 * player.length
        total += 1 * player.health
        total += -50 * len(enemies)
        total += -1 * enemy_max_length
        total += -1 * enemy_total_length
        total += 1 * player_voronoi
        total += 2 * player_reachable
        total += -1 * dist_food
        return total


# ---------------------------------------------------------------------------
# MoveDecider (port of MoveDecider)
# ---------------------------------------------------------------------------

class MoveDecider:
    def __init__(self, game):
        self.game = game
        self.board = game.board
        self.snakes = game.board.living_snakes()

        # Occupied cells: all bodies except each snake's last segment.
        self.walls = set()
        for snake in self.snakes:
            for seg in snake.body[:-1]:
                self.walls.add(seg)

    def considered_snakes(self):
        if len(self.snakes) <= 4:
            return self.snakes
        player = self.game.player()
        ph = player.head
        return sorted(
            self.snakes,
            key=lambda s: abs(s.head[0] - ph[0]) + abs(s.head[1] - ph[1]),
        )[:4]

    def reasonable_moves(self):
        result = {}
        for snake in self.considered_snakes():
            moves = []
            for move in ACTIONS:
                new_head = _move_point(snake.head, move)
                if self.board.out_of_bounds(new_head) or new_head in self.walls:
                    continue
                moves.append(move)
            if not moves:
                moves = [ACTIONS[0]]  # forced; nowhere safe
            result[snake.id] = moves
        return result

    def all_move_combinations(self, possible_moves):
        if not possible_moves:
            return [{}]
        keys = list(possible_moves.keys())
        snake_id = keys[0]
        my_moves = possible_moves[snake_id]
        remaining = {k: possible_moves[k] for k in keys[1:]}
        others = self.all_move_combinations(remaining)
        combos = []
        for my_move in my_moves:
            for other in others:
                d = {snake_id: my_move}
                d.update(other)
                combos.append(d)
        return combos

    def next_move(self):
        if not self.snakes:
            return ACTIONS[0]

        reasonable = self.reasonable_moves()
        player_id = self.game.player().id
        player_moves = reasonable.get(player_id, ACTIONS[:1])

        combos = self.all_move_combinations(reasonable)
        possibilities = []
        for moves in combos:
            g = self.game.simulate(moves)
            score = GameScorer(g).score()
            possibilities.append((moves.get(player_id), score))

        best_action = None
        best_value = None
        for action in player_moves:
            relevant = [sc for (mv, sc) in possibilities if mv == action]
            if not relevant:
                continue
            value = (min(relevant), sum(relevant) / len(relevant))
            if best_value is None or value > best_value:
                best_value = value
                best_action = action
        return best_action or player_moves[0]


# ---------------------------------------------------------------------------
# Parsing + API entry points
# ---------------------------------------------------------------------------

def _parse_game(game_state):
    b = game_state["board"]
    snakes = []
    for s in b["snakes"]:
        body = [(p["x"], p["y"]) for p in s["body"]]
        snakes.append(Snake(s["id"], s.get("name", s["id"]),
                            s.get("health", 100), body))
    food = [(f["x"], f["y"]) for f in b.get("food", [])]
    hazards = [(hz["x"], hz["y"]) for hz in b.get("hazards", [])]
    board = Board(b["width"], b["height"], snakes, food, hazards)
    return Game(game_state["you"]["id"], game_state.get("turn", 0), board)


def _fallback_move(game_state):
    """Guaranteed-legal move: in bounds and not into a snake body (tails ok)."""
    try:
        b = game_state["board"]
        me = game_state["you"]
        head = (me["head"]["x"], me["head"]["y"])
        w, h = b["width"], b["height"]
        occupied = set()
        for s in b["snakes"]:
            body = s["body"]
            for seg in body[:-1]:
                occupied.add((seg["x"], seg["y"]))
        for move in ACTIONS:
            nx, ny = _move_point(head, move)
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
                return move
        return "down"
    except Exception:
        return "down"


def info():
    return {
        "apiversion": "1",
        "author": "jhawthorn",
        "color": "#cc342d",
        "head": "caffeine",
        "tail": "bolt",
    }


def start(game_state):
    return None


def move(game_state):
    try:
        game = _parse_game(game_state)
        decider = MoveDecider(game)
        result = decider.next_move()
        if result not in ACTIONS:
            return {"move": _fallback_move(game_state)}
        # Safety net: never return a move into a known body segment / OOB.
        head = game.player().head
        nx, ny = _move_point(head, result)
        b = game.board
        bad = False
        if nx < 0 or ny < 0 or nx >= b.width or ny >= b.height:
            bad = True
        else:
            for s in b.living_snakes():
                if (nx, ny) in set(s.body[:-1]):
                    bad = True
                    break
        if bad:
            return {"move": _fallback_move(game_state)}
        return {"move": result}
    except Exception:
        return {"move": _fallback_move(game_state)}


def end(game_state):
    return None


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
