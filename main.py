"""
Port of OliverMKing/Battlesnake (Python3) to CodeClash BattleSnake v1 arena format.

Original strategy (faithfully reproduced):
  - Builds a symbolic grid board:
      '.' empty, 'F' food, 'Y' your body, 'H' your head, 'T' your tail,
      'o' enemy body, 'h' enemy head, 't' enemy tail,
      '*' cells adjacent to a head of an enemy that is >= your size (predicted danger),
      '!' cells that flood-fill to a dead-end smaller than your body (avoid).
  - decide_move() picks a behavior based on health & whether a bigger/equal enemy exists:
      * health >= 55 and no enemy >= your size can-chase-tail -> favor_chase_tail
      * health <= 15                                          -> heavily_favor_get_food
      * otherwise                                             -> favor_get_food
    Each behavior is a cascade of A* (chase tail / get food) and flood-fill
    (move_to_space) / random-safe fallbacks with progressively looser "safe" sets.
  - A* (BFS-style) searches for target symbol ('T' tail or 'F' food) over safe cells,
    returns the first move of the path.

Coordinate remap:
  Original API is top-left / y-down; board[y][x] with y-1 == "up", y+1 == "down".
  CodeClash v1 is bottom-left / y-up: "up" == y+1, "down" == y-1.
  We keep the original board[y][x] indexing (v1 y as row) and only swap the
  direction *labels* emitted for vertical neighbors so the returned move string
  is correct in v1 semantics. All heuristic logic is otherwise byte-for-byte.
"""

import random
import collections


# ---------------------------------------------------------------------------
# Variables (equivalent to variables.py)
# ---------------------------------------------------------------------------
class Variables:
    def __init__(self, data):
        self.height = data["board"]["height"]
        self.width = data["board"]["width"]
        self.food = data["board"]["food"]
        self.you_health = data["you"]["health"]
        self.you_id = data["you"]["id"]
        self.you_body = data["you"]["body"]
        self.you_x = self.you_body[0]["x"]
        self.you_y = self.you_body[0]["y"]
        self.snakes = data["board"]["snakes"]
        self.board = None


# ---------------------------------------------------------------------------
# Point (equivalent to point.py) -- with v1 direction remap for vertical moves
# ---------------------------------------------------------------------------
class Point:
    def __init__(self, variables, x, y, safe=('F', '.', 'T', 't'),
                 rank=0, direction="none", parent='none'):
        self.variables = variables
        self.board = variables.board
        self.x = x
        self.y = y
        self.width = variables.width
        self.height = variables.height
        self.rank = rank
        self.direction = direction
        self.parent = parent
        self.safe = safe

    def get_symbol(self):
        return self.board[self.y][self.x]

    def check_safe(self):
        return self.get_symbol() in self.safe

    def get_neighbors(self):
        neighbors = []

        # Original used y-1 == "up". In v1, decreasing y is "down".
        if self.y > 0:
            down = Point(self.variables, self.x, self.y - 1,
                         self.safe, self.rank + 1, "down", self)
            if down.check_safe():
                neighbors.append(down)
        # Original used y+1 == "down". In v1, increasing y is "up".
        if self.y < (self.height - 1):
            up = Point(self.variables, self.x, self.y + 1,
                       self.safe, self.rank + 1, "up", self)
            if up.check_safe():
                neighbors.append(up)
        if self.x < (self.width - 1):
            right = Point(self.variables, self.x + 1, self.y,
                          self.safe, self.rank + 1, "right", self)
            if right.check_safe():
                neighbors.append(right)
        if self.x > 0:
            left = Point(self.variables, self.x - 1, self.y,
                         self.safe, self.rank + 1, "left", self)
            if left.check_safe():
                neighbors.append(left)

        return neighbors

    def get_move(self, prev_move="none"):
        if self.direction == "none":
            return prev_move
        else:
            return self.parent.get_move(self.direction)

    def __eq__(self, other):
        if isinstance(other, Point):
            return (self.x == other.x) and (self.y == other.y)
        return NotImplemented

    def __hash__(self):
        return hash((self.x, self.y))


# ---------------------------------------------------------------------------
# Board (equivalent to board.py)
# ---------------------------------------------------------------------------
class Board:
    def __init__(self, variables):
        self.variables = variables
        self.create_empty_board()
        self.add_food()
        self.add_you()
        self.add_others()
        self.flood_flow_get_deadends()

        if variables.you_health < 10:
            self.add_food()

    def create_empty_board(self):
        height = self.variables.height
        width = self.variables.width
        board = []
        for _ in range(height):
            board.append(['.'] * width)
        self.variables.board = board

    def add_food(self):
        food = self.variables.food
        board = self.variables.board
        for f in food:
            board[f['y']][f['x']] = 'F'

    def add_you(self):
        you_body = self.variables.you_body
        board = self.variables.board
        coords = set()
        duplicates = False

        for b in you_body:
            x_coord = b['x']
            y_coord = b['y']
            if (x_coord, y_coord) in coords:
                duplicates = True
            coords.add((x_coord, y_coord))
            board[y_coord][x_coord] = 'Y'

        head = you_body[0]
        board[head['y']][head['x']] = 'H'

        if (len(you_body) > 3) and not duplicates:
            tail = you_body[-1]
            board[tail['y']][tail['x']] = 'T'

    def add_others(self):
        snakes = self.variables.snakes
        you_body = self.variables.you_body
        you_id = self.variables.you_id
        board = self.variables.board
        you_size = len(you_body)

        for snake in snakes:
            if snake["id"] == you_id:
                continue

            coords = set()
            duplicates = False

            for b in snake["body"]:
                x_coord = b['x']
                y_coord = b['y']
                if (x_coord, y_coord) in coords:
                    duplicates = True
                coords.add((x_coord, y_coord))
                board[y_coord][x_coord] = 'o'

            head = snake["body"][0]
            head_x_coord = head['x']
            head_y_coord = head['y']
            board[head_y_coord][head_x_coord] = 'h'

            if not duplicates:
                tail = snake["body"][-1]
                board[tail['y']][tail['x']] = 't'

            if len(snake["body"]) >= you_size:
                for neighbor in Point(self.variables, head_x_coord,
                                      head_y_coord).get_neighbors():
                    board[neighbor.y][neighbor.x] = '*'

    def flood_flow_get_deadends(self):
        you_x = self.variables.you_x
        you_y = self.variables.you_y
        you_size = len(self.variables.you_body)
        safe = ['F', '.', 'T', 't', '!', 'h']
        point = Point(self.variables, you_x, you_y, safe)

        for possible_move in point.get_neighbors():
            points = collections.deque([possible_move])
            free_space = 0
            checked = list()
            distance_away = 0
            while len(points) > 0:
                current = points.popleft()
                distance_away += 1
                free_space += 1
                checked.append(current)
                neighbors = current.get_neighbors()
                if (not 'h' in neighbors) or (distance_away == 1):
                    for neighbor in neighbors:
                        if (not neighbor in checked) and (not neighbor in points) \
                                and (not neighbor.get_symbol() == 'h'):
                            points.append(neighbor)
                else:
                    free_space -= 1
            if free_space < (you_size + 1):
                if not self.variables.board[possible_move.y][possible_move.x] in ['T', 't']:
                    self.variables.board[possible_move.y][possible_move.x] = '!'


# ---------------------------------------------------------------------------
# A* / BFS search (equivalent to a_star.py)
# ---------------------------------------------------------------------------
def a_star(variables, target, safe):
    you_x = variables.you_x
    you_y = variables.you_y
    _open = collections.deque([Point(variables, you_x, you_y, safe)])
    closed = set()

    while True:
        try:
            top = _open.popleft()
        except IndexError:
            return []
        if top.get_symbol() == target:
            break
        closed.add(top)
        neighbors = top.get_neighbors()
        for neighbor in neighbors:
            in_open, in_closed = False, False
            for value in tuple(_open):
                if value == neighbor:
                    if value.rank > neighbor.rank:
                        _open.remove(value)
                    else:
                        in_open = True
            for value in tuple(closed):
                if value == neighbor:
                    if value.rank > neighbor.rank:
                        closed.remove(value)
                    else:
                        in_closed = True
            if (not in_open) and (not in_closed):
                _open.append(neighbor)
    return top.get_move()


def get_food(variables, safe=('F', '.')):
    return a_star(variables, 'F', safe)


def chase_tail(variables, safe=('F', '.', 'T', '!')):
    return a_star(variables, 'T', safe)


# ---------------------------------------------------------------------------
# Logic / behaviors (equivalent to logic.py)
# ---------------------------------------------------------------------------
def move_to_space(variables, safe=('F', '.', 'T')):
    you_x = variables.you_x
    you_y = variables.you_y
    point = Point(variables, you_x, you_y, safe)
    moves = dict()

    for possible_move in point.get_neighbors():
        points = collections.deque([possible_move])
        free_space = 0
        checked = list()
        while len(points) > 0:
            current = points.popleft()
            free_space += 1
            checked.append(current)
            for neighbor in current.get_neighbors():
                if (not neighbor in checked) and (not neighbor in points):
                    points.append(neighbor)
        moves[possible_move.direction] = free_space

    best_move = list()
    best = 0
    for value in moves.values():
        if value > best:
            best = value
    for key in moves.keys():
        if moves[key] == best:
            best_move.append(key)
    if len(best_move) == 0:
        return best_move
    return random.choice(best_move)


def avoid_self_and_borders_randomly(variables, safe=('F', '.', 'T', 't')):
    you_x = variables.you_x
    you_y = variables.you_y
    point = Point(variables, you_x, you_y, safe)
    directions = list()

    for neighbor in point.get_neighbors():
        directions.append(neighbor.direction)

    if len(directions) == 0:
        return directions
    return random.choice(directions)


def favor_chase_tail(variables):
    move = chase_tail(variables)
    if len(move) == 0:
        move = chase_tail(variables, ['F', '.', 'T', 't', '!'])
        if len(move) == 0:
            move = move_to_space(variables)
            if len(move) == 0:
                move = get_food(variables)
                if len(move) == 0:
                    move = get_food(variables, ['F', '.', 'T', 't', '!'])
                    if len(move) == 0:
                        move = avoid_self_and_borders_randomly(variables)
                        if len(move) == 0:
                            move = chase_tail(variables, ['F', '.', 'T', 't', '!', '*'])
                            if len(move) == 0:
                                move = move_to_space(variables, ['F', '.', 'T', 't', '!', '*'])
                                if len(move) == 0:
                                    move = get_food(variables, ['F', '.', 'T', 't', '!', '*'])
                                    if len(move) == 0:
                                        move = avoid_self_and_borders_randomly(
                                            variables, ['F', '.', 'T', 't', '!', '*'])
    return move


def heavily_favor_get_food(variables):
    move = get_food(variables)
    if len(move) == 0:
        move = get_food(variables, ['F', '.', 'T', 't', '!', '*'])
        if len(move) == 0:
            move = chase_tail(variables)
            if len(move) == 0:
                move = move_to_space(variables)
                if len(move) == 0:
                    move = chase_tail(variables, ['F', '.', 'T', 't', '!', '*'])
                    if len(move) == 0:
                        move = avoid_self_and_borders_randomly(variables)
                        if len(move) == 0:
                            move = move_to_space(variables, ['F', '.', 'T', 't', '!', '*'])
                            if len(move) == 0:
                                move = avoid_self_and_borders_randomly(
                                    variables, ['F', '.', 'T', 't', '!', '*'])
    return move


def favor_get_food(variables):
    move = get_food(variables)
    if len(move) == 0:
        move = chase_tail(variables)
        if len(move) == 0:
            move = move_to_space(variables)
            if len(move) == 0:
                move = avoid_self_and_borders_randomly(variables)
                if len(move) == 0:
                    move = get_food(variables, ['F', '.', 'T', 't', '!', '*'])
                    if len(move) == 0:
                        move = chase_tail(variables, ['F', '.', 'T', 't', '!', '*'])
                        if len(move) == 0:
                            move = move_to_space(variables, ['F', '.', 'T', 't', '!', '*'])
                            if len(move) == 0:
                                move = avoid_self_and_borders_randomly(
                                    variables, ['F', '.', 'T', 't', '!', '*'])
    return move


def decide_move(variables):
    you_health = variables.you_health
    you_body = variables.you_body
    snakes = variables.snakes
    you_id = variables.you_id
    you_size = len(you_body)

    can_chase_tail = True
    for snake in snakes:
        if len(snake["body"]) >= you_size:
            if snake["id"] != you_id:
                can_chase_tail = False
                break

    if (you_health >= 55) and can_chase_tail:
        move = favor_chase_tail(variables)
        if move in ['up', 'down', 'left', 'right']:
            return move
    elif you_health <= 15:
        move = heavily_favor_get_food(variables)
        if move in ['up', 'down', 'left', 'right']:
            return move
    else:
        move = favor_get_food(variables)
        if move in ['up', 'down', 'left', 'right']:
            return move

    return random.choice(['up', 'down', 'left', 'right'])


# ---------------------------------------------------------------------------
# Robust legal-move fallback
# ---------------------------------------------------------------------------
def _legal_fallback(game_state):
    """Return any move that stays in bounds and does not hit a snake body
    (tail cells allowed since tails move). Prefers non-tail empty cells."""
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    # Occupied body cells (exclude each snake's tail, which moves next turn,
    # unless the snake likely just ate -- keep it simple/safe: allow tails).
    occupied = set()
    tails = set()
    for snake in board["snakes"]:
        body = snake["body"]
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if i == len(body) - 1 and len(body) > 1:
                tails.add(cell)
            else:
                occupied.add(cell)

    candidates = {
        "up": (hx, hy + 1),
        "down": (hx, hy - 1),
        "left": (hx - 1, hy),
        "right": (hx + 1, hy),
    }

    def in_bounds(c):
        return 0 <= c[0] < width and 0 <= c[1] < height

    # First choice: in bounds, not occupied, not a tail.
    for d, c in candidates.items():
        if in_bounds(c) and c not in occupied and c not in tails:
            return d
    # Second: allow tails.
    for d, c in candidates.items():
        if in_bounds(c) and c not in occupied:
            return d
    # Last resort: just stay in bounds.
    for d, c in candidates.items():
        if in_bounds(c):
            return d
    return "up"


# ---------------------------------------------------------------------------
# v1 API entry points
# ---------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "OliverMKing",
        "color": "#4584B6",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def move(game_state):
    try:
        variables = Variables(game_state)
        Board(variables)
        chosen = decide_move(variables)

        # Validate the chosen move is actually legal in v1; if not, fall back.
        if chosen in ("up", "down", "left", "right"):
            board = game_state["board"]
            head = game_state["you"]["body"][0]
            hx, hy = head["x"], head["y"]
            delta = {"up": (0, 1), "down": (0, -1),
                     "left": (-1, 0), "right": (1, 0)}[chosen]
            nx, ny = hx + delta[0], hy + delta[1]

            if 0 <= nx < board["width"] and 0 <= ny < board["height"]:
                # Not into own non-tail body.
                own = game_state["you"]["body"]
                own_bad = set()
                for i, seg in enumerate(own):
                    if i == len(own) - 1 and len(own) > 1:
                        continue  # tail moves
                    own_bad.add((seg["x"], seg["y"]))
                if (nx, ny) not in own_bad:
                    return {"move": chosen}

        return {"move": _legal_fallback(game_state)}
    except Exception:
        try:
            return {"move": _legal_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
