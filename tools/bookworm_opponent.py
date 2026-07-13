import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
Port of csauve/bookworm (https://github.com/csauve/bookworm) to CodeClash arena format.

Original: Rust, "A BattleSnake bot for 2020". Combines pruned turn-tree exploration,
minimax (worst-case over opponent moves), and heuristic scoring. The snake is given a
time budget to explore the turn tree via a best-first frontier (a priority queue keyed
by heuristic score); the fewer the snakes, the deeper it explores.

FIDELITY: faithful reproduction of bookworm's brain.rs / board.rs strategy:
  - Best-first search: BinaryHeap of frontier boards ordered by heuristic score. Pop the
    best-scoring leaf, expand it, and record its root direction as the current decision.
  - For each of MY 4 directions, take the WORST outcome over the cartesian product of
    opponents' possible moves (minimax pessimism). Opponents beyond the closest
    MAX_PRIORITY_SNAKES are collapsed to their single default move to bound the branching.
  - Node score = min(child_heuristic, parent_heuristic) (a leaf is only as good as its
    worst ancestor step). Death outcomes score negative and are NOT pushed to the frontier;
    HeadToHead (-1) is preferred over Starved (-2) over other collisions (-3).
  - heuristic = h_food * h_head_to_head * h_control * h_snakes^2 where:
      h_control     = my flood-fill territory area / total territory area
      h_food        = 1 - min(1, nearest_food_dist / health), or a spawn-chance estimate
      h_head_to_head= fraction of snakes we don't need to fear a head-to-head against
      h_snakes      = 1 / number_of_snakes  (fewer snakes -> better, squared)
  - Territories via simultaneous multi-source BFS flood fill from all snake heads, with
    tail positions that will have vacated by turn t treated as free (get_free_moves(t)).

NOTE ON COORDINATES: bookworm was written for the 2020 API where the internal model treats
y as top-down (Up=dy-1, Down=dy+1) and reads raw API coords. Its strategy math (manhattan
distance, flood fill, minimax) is entirely direction-agnostic, so this port implements the
identical logic directly in the CURRENT v1 API convention (origin bottom-left, up=y+1,
down=y-1). Direction labels come out correct for v1.

Pure stdlib, self-contained, wall-clock bounded.
"""

import heapq
import itertools
import time

# Direction offsets in CURRENT v1 API convention: origin bottom-left, up = y+1.
DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
ALL_DIRS = ["up", "down", "left", "right"]

FOOD_SPAWN_CHANCE = 15  # of 100, matches bookworm
MAX_PRIORITY_SNAKES = 4  # matches bookworm: prune branching beyond the 4 closest snakes

# Cause-of-death scores (bookworm brain.rs). HeadToHead preferred (we might take a foe out).
DEATH_HEAD_TO_HEAD = -1.0
DEATH_STARVED = -2.0
DEATH_OTHER = -3.0

TIME_BUDGET = 0.30  # wall-clock seconds; keeps us well under 1s on 11x11


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Snake:
    __slots__ = ("health", "body")

    def __init__(self, health, body):
        self.health = health
        # body is a list of (x, y) tuples, head first
        self.body = body

    def clone(self):
        return Snake(self.health, list(self.body))

    def head(self):
        return self.body[0]

    def neck(self):
        return self.body[1] if len(self.body) > 1 else None

    def tail(self):
        return self.body[-1]

    def size(self):
        return len(self.body)

    def starved(self):
        return self.health <= 0

    def find_first_node(self, loc, offset):
        """Index (relative to `offset`) of first body node equal to loc, else None.
        Mirrors bookworm's find_first_node: matching the FIRST occurrence is key for
        handling stacked tail coords correctly."""
        for i in range(offset, len(self.body)):
            if self.body[i] == loc:
                return i - offset
        return None

    def default_move(self):
        """Direction from neck->head; used when a snake has no free move. Defaults up."""
        n = self.neck()
        if n is not None:
            hx, hy = self.head()
            dx, dy = hx - n[0], hy - n[1]
            for d, (ox, oy) in DIRS.items():
                if (ox, oy) == (dx, dy):
                    return d
        return "up"

    def slither(self, direction):
        self.health = max(0, self.health - 1)
        ox, oy = DIRS[direction]
        hx, hy = self.body[0]
        self.body.insert(0, (hx + ox, hy + oy))
        self.body.pop()

    def feed(self, new_health):
        self.health = new_health
        # extend tail by duplicating last node (zero offset), matching feed()
        self.body.append(self.body[-1])


class Board:
    __slots__ = ("snakes", "food", "bound")

    def __init__(self, snakes, food, bound):
        self.snakes = snakes  # index 0 is "you"
        self.food = food  # list of (x,y)
        self.bound = bound  # (max_x, max_y)

    def clone(self):
        return Board([s.clone() for s in self.snakes], list(self.food), self.bound)

    def you(self):
        return self.snakes[0]

    def in_bounds(self, c):
        return 0 <= c[0] <= self.bound[0] and 0 <= c[1] <= self.bound[1]

    def find_food(self, coord):
        try:
            return self.food.index(coord)
        except ValueError:
            return None

    def get_free_moves(self, frm, n_turns):
        """Moves from `frm` that are in-bounds and not obstructed. A snake node is passable
        if it will have vacated within n_turns (tail shrinkage), matching bookworm."""
        out = []
        for d, (ox, oy) in DIRS.items():
            nc = (frm[0] + ox, frm[1] + oy)
            if not self.in_bounds(nc):
                continue
            blocked = False
            for snake in self.snakes:
                if manhattan(nc, snake.head()) > snake.size():
                    continue
                i = snake.find_first_node(nc, 0)
                if i is None:
                    continue
                # safe to enter if that node is gone within n_turns
                if i >= max(0, snake.size() - n_turns):
                    continue
                blocked = True
                break
            if not blocked:
                out.append(d)
        return out

    def enumerate_snake_moves(self):
        """Per-snake list of candidate moves. Trapped snakes still must move -> assume up."""
        result = []
        for snake in self.snakes:
            moves = self.get_free_moves(snake.head(), 1)
            if not moves:
                moves = ["up"]
            result.append(moves)
        return result

    def get_closest_snakes_by_manhattan(self, coord):
        ranked = [(i, manhattan(coord, s.head())) for i, s in enumerate(self.snakes)]
        ranked.sort(key=lambda t: t[1])
        return ranked

    def get_territories(self):
        """Simultaneous multi-source BFS flood fill from every snake head.
        Returns per-snake dict {area, nearest_food}. Ties: the coord goes to whoever
        reached it first (earlier owner in insertion order wins, as in the Rust HashSet
        expansion where a coord is only claimed once)."""
        ownership = {}
        frontier = set()
        for i, snake in enumerate(self.snakes):
            h = snake.head()
            if h not in ownership:
                ownership[h] = i
                frontier.add((h, i))

        turn = 1
        while frontier:
            nxt = set()
            for coord, owner in frontier:
                for d in self.get_free_moves(coord, turn):
                    ox, oy = DIRS[d]
                    nb = (coord[0] + ox, coord[1] + oy)
                    if nb not in ownership:
                        ownership[nb] = owner
                        nxt.add((nb, owner))
            frontier = nxt
            turn += 1

        territories = [{"area": 0, "nearest_food": None} for _ in self.snakes]
        for coord, owner in ownership.items():
            if self.find_food(coord) is not None:
                dist = manhattan(self.snakes[owner].head(), coord)
                cur = territories[owner]["nearest_food"]
                # bookworm keeps the LARGEST such dist due to a `<` bug; replicate faithfully:
                # it sets nearest_food when current is None or current < dist.
                if cur is None or cur < dist:
                    territories[owner]["nearest_food"] = dist
            territories[owner]["area"] += 1
        return territories

    def advance(self, snake_moves):
        """Apply one turn of game rules. Returns {snake_index: cause_of_death}.
        Faithful to bookworm board.rs advance() (no food spawning during search)."""
        eaten = set()
        for i in range(len(self.snakes)):
            d = snake_moves[i] if i < len(snake_moves) else self.snakes[i].default_move()
            self.snakes[i].slither(d)
            fi = self.find_food(self.snakes[i].head())
            if fi is not None:
                self.snakes[i].feed(100)
                eaten.add(fi)

        dead = {}
        for si, snake in enumerate(self.snakes):
            if snake.starved():
                dead[si] = DEATH_STARVED
                continue
            if not self.in_bounds(snake.head()):
                dead[si] = DEATH_OTHER  # OutOfBounds
                continue
            cause = None
            for oi, other in enumerate(self.snakes):
                if oi != si:
                    idx = other.find_first_node(snake.head(), 0)
                    if idx is not None:
                        if idx > 0:
                            cause = DEATH_OTHER  # OtherCollision
                            break
                        elif snake.size() <= other.size():
                            cause = DEATH_HEAD_TO_HEAD
                            break
                else:
                    if other.find_first_node(snake.head(), 1) is not None:
                        cause = DEATH_OTHER  # SelfCollision
                        break
            if cause is not None:
                dead[si] = cause

        if eaten:
            self.food = [f for i, f in enumerate(self.food) if i not in eaten]
        if dead:
            self.snakes = [s for i, s in enumerate(self.snakes) if i not in dead]
        return dead


def board_from_state(game_state):
    board = game_state["board"]
    you_id = game_state["you"]["id"]
    api_snakes = board["snakes"]

    def mk(s):
        body = [(c["x"], c["y"]) for c in s["body"]]
        return Snake(s["health"], body)

    # index 0 must be "you", then the rest (excluding you)
    ordered = [game_state["you"]] + [s for s in api_snakes if s["id"] != you_id]
    snakes = [mk(s) for s in ordered]
    food = [(f["x"], f["y"]) for f in board["food"]]
    bound = (board["width"] - 1, board["height"] - 1)
    return Board(snakes, food, bound)


def heuristic(board):
    """h in [0,1]-ish: 1.0 => winning, 0.0 => losing. Faithful to brain.rs heuristic()."""
    if len(board.snakes) == 1:
        return 1.0
    territories = board.get_territories()
    snake = board.snakes[0]
    terr = territories[0]
    total_area = max(1, sum(t["area"] for t in territories))
    h_control = terr["area"] / total_area

    turns_until_starve = snake.health
    if turns_until_starve == 0:
        h_food = 0.0
    elif terr["nearest_food"] is not None:
        h_food = 1.0 - min(1.0, terr["nearest_food"] / turns_until_starve)
    else:
        p = FOOD_SPAWN_CHANCE / 100.0
        h_food = min(1.0, p * turns_until_starve * len(board.snakes) / total_area)

    my_size = snake.size()
    my_head = snake.head()
    # count snakes we DON'T need to worry about (self / smaller / distant), over total
    safe = 0
    for oi, other in enumerate(board.snakes):
        if oi == 0 or other.size() < my_size or manhattan(other.head(), my_head) > 2:
            safe += 1
    h_head_to_head = safe / len(board.snakes)

    h_snakes = 1.0 / len(board.snakes)

    return h_food * h_head_to_head * h_control * h_snakes * h_snakes


class FrontierBoard:
    __slots__ = ("board", "root_dir", "depth", "h_score", "_seq")

    def __init__(self, board, root_dir, depth, h_score, seq):
        self.board = board
        self.root_dir = root_dir
        self.depth = depth
        self.h_score = h_score
        self._seq = seq

    # max-heap by h_score: invert comparison for Python's min-heap
    def __lt__(self, other):
        if self.h_score != other.h_score:
            return self.h_score > other.h_score
        return self._seq < other._seq


def get_decision(game_state, budget=TIME_BUDGET):
    start = time.monotonic()
    root = board_from_state(game_state)
    seq = itertools.count()

    decision = root.you().default_move()

    frontier = []
    heapq.heappush(frontier, FrontierBoard(root, None, 0, 1.0, next(seq)))

    while frontier:
        leader = heapq.heappop(frontier)

        if leader.root_dir is not None:
            decision = leader.root_dir

        if time.monotonic() - start >= budget:
            break

        snake_moves = leader.board.enumerate_snake_moves()

        # prune branching: collapse all but the closest MAX_PRIORITY_SNAKES to one move
        closest = leader.board.get_closest_snakes_by_manhattan(leader.board.you().head())
        for si, _dist in closest[MAX_PRIORITY_SNAKES:]:
            if si < len(snake_moves):
                dm = leader.board.snakes[si].default_move()
                if dm in snake_moves[si]:
                    snake_moves[si] = [dm]
                else:
                    snake_moves[si] = [snake_moves[si][0]]

        # for each of MY directions, keep the WORST outcome across opponents' joint moves
        worst = {}  # dir -> FrontierBoard
        for combo in itertools.product(*snake_moves):
            nb = leader.board.clone()
            dead = nb.advance(list(combo))
            you_move = combo[0]

            root_dir = leader.root_dir if leader.root_dir is not None else you_move

            if 0 in dead:
                fb = FrontierBoard(nb, root_dir, leader.depth + 1, dead[0], next(seq))
                # overwrite: a death is the definitive worst case for this direction
                cur = worst.get(you_move)
                if cur is None or fb.h_score < cur.h_score:
                    worst[you_move] = fb
            else:
                child_h = heuristic(nb)
                score = min(child_h, leader.h_score)
                cur = worst.get(you_move)
                if cur is None or score < cur.h_score:
                    worst[you_move] = FrontierBoard(nb, root_dir, leader.depth + 1, score, next(seq))

        # push survivable worst-outcomes back to the frontier
        for fb in worst.values():
            if fb.h_score >= 0.0:
                heapq.heappush(frontier, fb)

    return decision


# ---- CodeClash arena API ----

def info():
    return {
        "apiversion": "1",
        "author": "csauve",
        "color": "#800080",
        "head": "bendr",
        "tail": "round-bum",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _safe_fallback(game_state):
    """Guaranteed-legal move: in-bounds and not into a snake body (tails enterable)."""
    board = game_state["board"]
    you = game_state["you"]
    hx, hy = you["head"]["x"], you["head"]["y"]
    w, h = board["width"], board["height"]

    # collect occupied body cells; a tail cell will move so it is enterable (unless the
    # snake just ate, but this is a last-resort fallback so we accept the small risk).
    blocked = set()
    for s in board["snakes"]:
        body = s["body"]
        for c in body[:-1]:
            blocked.add((c["x"], c["y"]))
    food_set = {(f["x"], f["y"]) for f in board["food"]}

    candidates = []
    for d, (ox, oy) in DIRS.items():
        nx, ny = hx + ox, hy + oy
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
            candidates.append(d)
    if candidates:
        return candidates[0]
    # nothing safe: return any in-bounds move
    for d, (ox, oy) in DIRS.items():
        nx, ny = hx + ox, hy + oy
        if 0 <= nx < w and 0 <= ny < h:
            return d
    return "up"


def move(game_state):
    try:
        d = get_decision(game_state)
        # sanity: ensure returned move is one of the four
        if d not in DIRS:
            d = _safe_fallback(game_state)
        return {"move": d}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
