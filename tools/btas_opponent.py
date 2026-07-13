import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
Faithful port of rdbrck "BTAS" (Better Than Aleksiy's Snake), 2017 Victoria
Advanced division winner.
Original: https://github.com/rdbrck/battlesnake-2017-btas
  (app/strategy.py, algorithms.py, routes.py, utils.py, entities.py, constants.py)

The original targets the 2017 OLD Battlesnake API: top-left origin, y-DOWN,
snakes carry "coords" and "health_points". In that world:
    neighbours(pos)  -> (x, y+1), (x+1, y), (x, y-1), (x-1, y)
    get_direction    -> "up" means y DECREASES, "down" means y INCREASES.

CodeClash uses the v1 API: bottom-left origin, y-UP, snakes carry "body" and
"health". To preserve the original algorithm byte-for-byte, we translate the
incoming v1 state into the original's y-DOWN internal representation at the
boundary (y_internal = height - 1 - y_v1), run the ORIGINAL logic verbatim,
then translate the chosen direction name back to v1:
    original "up"   (y-down decreases) == v1 "down"
    original "down" (y-down increases) == v1 "up"
    "left"/"right" are unchanged.

Everything else (general_direction scoring, need_food thresholds, flood-fill
danger <=10 with keep-largest, BFS to rated food picking the SHORTEST path else
safest-space picking the LONGEST path, _rate_cell weights, all constants,
tie-breaks) reproduces the original exactly. All is wrapped in try/except that
always returns a legal move.
"""

import collections
import random
from collections import deque
from math import floor
from functools import reduce

# --- constants.py -----------------------------------------------------------
EMPTY = 0
SNAKE = 1
FOOD = 2
SPOILED = 3

DIR_NAMES = ['up', 'down', 'left', 'right']
DIR_VECTORS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # y-down internal


# --- utils.py ---------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dist(a, b):
    """ Returns the 'manhattan distance' between a and b """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def surrounding(pos):
    return [
        (pos[0], pos[1] + 1),
        (pos[0] + 1, pos[1]),
        (pos[0] + 1, pos[1] + 1),
        (pos[0] + 1, pos[1] - 1),
        (pos[0], pos[1] - 1),
        (pos[0] - 1, pos[1]),
        (pos[0] - 1, pos[1] - 1),
        (pos[0] - 1, pos[1] + 1)
    ]


def neighbours(pos):
    """ Gets coordinates of neighbour coordinates to a coordinate. """
    return [
        (pos[0], pos[1] + 1),
        (pos[0] + 1, pos[1]),
        (pos[0], pos[1] - 1),
        (pos[0] + -1, pos[1])
    ]


def get_direction(currPos, nextPos):
    if (currPos[0] == nextPos[0]):
        if (nextPos[1] - currPos[1] < 0):
            return 'up'
        else:
            return 'down'
    elif (currPos[1] == nextPos[1]):
        if (nextPos[0] - currPos[0] < 0):
            return 'left'
        else:
            return 'right'


# --- entities.py ------------------------------------------------------------
class Snake(object):
    ATTRIBUTES = ('id', 'health_points')

    def __init__(self, clone=None, **kwargs):
        if clone:
            self.attributes = clone.attributes.copy()
            self.coords = list(clone.coords)
        else:
            self.attributes = {k: kwargs[k] for k in Snake.ATTRIBUTES}
            self.coords = list(map(tuple, kwargs['coords']))

    def _get_direction(self):
        assert len(self.coords) > 1
        return sub(self.coords[0], self.coords[1])
    direction = property(_get_direction)

    def __len__(self):
        return len(self.coords)

    def _get_head(self):
        return self.coords[0]
    head = property(_get_head)

    def _get_tail(self):
        return self.coords[-1]
    tail = property(_get_tail)

    def potential_positions(self):
        return [add(self.head, d) for d in DIR_VECTORS if d != sub((0, 0), self.direction)]


class Board(object):
    """
    Basically a 2d grid of cells represented by integers.
    A zero cell is unoccupied. 1 is snake. 2 is food.
    """

    def __init__(self, clone=None, **kwargs):
        if clone:
            # NB: the original bfs() uses copy.deepcopy(board), which also copies
            # meta_cells. We mirror that here (the original's clone= branch never
            # copied meta_cells, but bfs never used it either).
            self.width = clone.width
            self.height = clone.height
            self.cells = []
            for x in range(self.width):
                self.cells.append(clone.cells[x][:])
            self.meta_cells = []
            for x in range(self.width):
                self.meta_cells.append(list(clone.meta_cells[x]))
            self.snakes = [Snake(s) for s in clone.snakes]
            self.food = list(clone.food)
        else:
            self.width = kwargs['width']
            self.height = kwargs['height']
            self.cells = []
            self.meta_cells = []
            for x in range(self.width):
                self.cells.append([EMPTY] * self.height)
                self.meta_cells.append([None] * self.height)
            self.snakes = [Snake(**s) for s in kwargs['snakes']]
            self.food = list(map(tuple, kwargs['food']))

            for snake in self.snakes:
                for pos in snake.coords:
                    self.set_cell(pos, SNAKE)

            for fud in self.food:
                if self._contested_food(fud, kwargs['you']):
                    self.set_cell(fud, FOOD)
                else:
                    self.set_cell(fud, SPOILED)

    def _contested_food(self, pos, snake_id):
        current_snake = self.snakes[0]
        for snake in self.snakes:
            if ((dist(snake.head, pos) < dist(current_snake.head, pos)) or
                    ((dist(snake.head, pos) == dist(current_snake.head, pos)) and (len(snake.coords) >= len(current_snake.coords)))):
                current_snake = snake
        return (current_snake.attributes['id'] == snake_id)

    def get_snake(self, snake_id):
        try:
            return next(s for s in self.snakes if s.attributes['id'] == snake_id)
        except StopIteration:
            return None

    def set_cell(self, pos, value, meta=None):
        self.cells[pos[0]][pos[1]] = value
        self.meta_cells[pos[0]][pos[1]] = meta

    def get_cell(self, pos):
        return self.cells[pos[0]][pos[1]]

    def outside(self, pos):
        return pos[0] < 0 or pos[0] >= self.width or pos[1] < 0 or pos[1] >= self.height

    def inside(self, pos):
        return not self.outside(pos)

    def vacant(self, pos):
        return not (pos[0] < 0 or pos[0] >= self.width or pos[1] < 0 or pos[1] >= self.height) and self.cells[pos[0]][pos[1]] != SNAKE

    def has_snake(self, pos):
        return (self.cells[pos[0]][pos[1]] == SNAKE)

    def has_food(self, pos):
        return (self.cells[pos[0]][pos[1]] == FOOD or self.cells[pos[0]][pos[1]] == SPOILED)


# --- strategy.py ------------------------------------------------------------
def general_direction(board, head, health):
    """ Returns the most 'beneficial' direction to move in """

    direction = {
        "up": 5000 / (dist(head, (head[0], 0)) + 1),
        "down": 5000 / (dist(head, (head[0], board.height)) + 1),
        "right": 5000 / (dist((board.width, head[1]), head) + 1),
        "left": 5000 / (dist((0, head[1]), head) + 1)
    }

    if not board.vacant((head[0] - 1, head[1])):
        direction["left"] += 1000000

    if not board.vacant((head[0] + 1, head[1])):
        direction["right"] += 1000000

    if not board.vacant((head[0], head[1] - 1)):
        direction["up"] += 1000000

    if not board.vacant((head[0], head[1] + 1)):
        direction["down"] += 1000000

    for snake in board.snakes:
        for pos in snake.coords:
            if pos == head:
                continue
            if pos[0] > head[0]:
                direction['right'] += 1000 / dist(pos, head)
            elif pos[0] < head[0]:
                direction['left'] += 1000 / dist(pos, head)
            if pos[1] < head[1]:
                direction['up'] += 1000 / dist(pos, head)
            elif pos[1] > head[1]:
                direction['down'] += 1000 / dist(pos, head)

    if health < 75:
        for pos in board.food:
            if board.get_cell(pos) == 3 and (health - dist(pos, head) > 20):
                continue
            if pos[0] > head[0]:
                direction['right'] -= (10000 / ((health / 10) + 1)) / dist(pos, head)
            elif pos[0] < head[0]:
                direction['left'] -= (10000 / ((health / 10) + 1)) / dist(pos, head)
            if pos[1] < head[1]:
                direction['up'] -= (10000 / ((health / 10) + 1)) / dist(pos, head)
            elif pos[1] > head[1]:
                direction['down'] -= (10000 / ((health / 10) + 1)) / dist(pos, head)

    return min(direction.keys(), key=(lambda key: direction[key]))


def need_food(board, head, health):
    food_to_get = []
    num_snakes = len(board.snakes)

    if health < 50:
        for food in board.food:
            if (health + dist(head, food)) < 50:
                food_to_get.append(food)

    if len(food_to_get) > 0:
        return food_to_get

    safe_food = [fud for fud in board.food if board.get_cell(fud) != 3]

    for food in safe_food:
        if dist(food, head) <= 2 and health < (((num_snakes + 1) * 7) + 15):
            food_to_get.append(food)
        elif health < 50:
            food_to_get.append(food)

    return (food_to_get if len(food_to_get) > 0 else None)


# --- algorithms.py ----------------------------------------------------------
def flood_fill(board, start_pos, allow_start_in_occupied_cell=False):
    visited = set()

    if not allow_start_in_occupied_cell and not board.vacant(start_pos):
        return visited

    visited.add(start_pos)
    todo = collections.deque([start_pos])

    while todo:
        current = todo.popleft()
        for p in neighbours(current):
            if p not in visited and board.vacant(p):
                visited.add(p)
                todo.append(p)

    return visited


def _rate_cell(cell, board, recurse=False):
    """ rates a cell based on proximity to other snakes, food, the edge of the board, etc """
    cells = [m_cell for m_cell in surrounding(cell) if board.inside(m_cell)]
    cells = [(m_cell, board.get_cell(m_cell)) for m_cell in cells]
    cell_value = reduce(lambda carry, m_cell: carry + [0.5, -5, 2, 0][m_cell[1]], cells, 0)

    if recurse or cell_value < 2:
        return cell_value
    else:
        return cell_value + sum([
            _rate_cell(m_cell, board) / 10
            for m_cell in surrounding(cell) if board.inside(m_cell)
        ])


def _stable_first3(carry):
    """ Py2 sorted() with a bool-returning cmp is a stable no-op; take first 3. """
    return carry[:3]


def find_safest_position(current_position, direction, board):
    m_bounds = [(0, 0), (board.width, board.height)]
    max_depth = 10

    def _find_safest(bounds=m_bounds, offset=(0, 0), depth=0, carry=[]):
        sector_width = (bounds[1][0] - bounds[0][0])
        sector_height = (bounds[1][1] - bounds[0][1])

        center_point = (
            int(offset[0] + floor(sector_width / 2)),
            int(offset[1] + floor(sector_height / 2))
        )

        if depth == max_depth or (sector_height * sector_width <= 1):
            # Original: sorted(carry, lambda c1, c2: c1[1] < c2[1])[:3]
            # A bool-returning cmp under Py2's stable mergesort is a no-op, so
            # the result preserves insertion order; take the first three.
            return _stable_first3(carry)
        else:
            carry_cells = [cell[0] for cell in carry]
            surrounding_ratings = [
                ((cell[0], cell[1]), _rate_cell((cell[0], cell[1]), board, True))
                for cell in surrounding(center_point)
                if cell not in carry_cells and board.inside(cell) and board.get_cell(cell) != SNAKE
            ]

            random.shuffle(surrounding_ratings)
            position, rating = reduce(
                lambda m_carry, cell: cell if cell[1] > m_carry[1] else m_carry,
                surrounding_ratings, (None, -100000000000))

            new_bounds = bounds
            if position is not None:
                carry = carry + [(position, rating)]
                direction_vector = sub(position, center_point)

                if abs(direction_vector[0]) == abs(direction_vector[1]):
                    direction_vector = list(direction_vector)
                    direction_vector[int(__import__('time').time()) % 2] = 0
                    direction_vector = tuple(direction_vector)

                direction_name = DIR_NAMES[DIR_VECTORS.index(direction_vector)]

                if direction_name == "up":
                    new_bounds = [offset, (bounds[1][0], bounds[1][1])]
                elif direction_name == "down":
                    offset = (offset[0], center_point[1])
                    new_bounds = [offset, (bounds[1][0], bounds[1][1])]
                elif direction_name == "left":
                    new_bounds = [offset, (center_point[0], bounds[1][1])]
                else:  # right
                    offset = (center_point[0], offset[1])
                    new_bounds = [offset, (bounds[0][0], bounds[1][1])]

            return _find_safest(new_bounds, offset, depth + 1, carry=carry)

    if direction == "up":
        bounds = [(0, 0), (board.width, current_position[1])]
    elif direction == "down":
        bounds = [(0, current_position[1]), (board.width, board.height)]
    elif direction == "right":
        bounds = [(current_position[0], 0), (board.width, board.height)]
    else:  # left
        bounds = [(0, 0), (current_position[0], board.height)]

    return _find_safest(bounds, bounds[0])


def find_food(current_position, health_remaining, board, board_food):
    """ finds and rates food positions """
    rated_food = [(food, _rate_cell(food, board, True)) for food in board_food]
    # Original: sorted(rated_food, lambda f1, f2: f1[1] > f2[1])
    # bool-returning cmp -> stable no-op ordering in Py2: preserve input order.
    return list(rated_food)


def bfs(starting_position, target_position, board, exclude, return_list):
    """ BFS implementation to search for path to food """

    def get_path_from_nodes(node):
        path = []
        while (node is not None):
            path.insert(0, (node[0], node[1]))
            node = node[2]
        return return_list.append(path[1:])

    x = starting_position[0]
    y = starting_position[1]
    board_copy = Board(clone=board)
    board_copy.set_cell((x, y), 0)
    for excluded_point in exclude:
        board_copy.set_cell(excluded_point, "B")

    queue = deque([(x, y, None)])
    while len(queue) > 0:
        node = queue.popleft()
        x = node[0]
        y = node[1]

        if board_copy.inside((x, y)) is True:
            if (x, y) == target_position:
                return get_path_from_nodes(node)

            if (board_copy.outside((x, y)) is True or board_copy.get_cell((x, y)) == "B" or board_copy.get_cell((x, y)) == 1) and not (x, y) == starting_position:
                continue

            board_copy.set_cell((x, y), "B")

            for i in neighbours(node):
                if board.inside((i[0], i[1])):
                    queue.append((i[0], i[1], node))

    return None


# --- v1 <-> internal (y-down) translation ----------------------------------
def _flip_y(pt, height):
    return (pt[0], height - 1 - pt[1])


def _build_internal_data(game_state):
    """ Convert a v1 game_state into the kwargs the original Board(**data) expects,
    flipping y from v1 (y-up) into the original's internal y-down space. """
    v_board = game_state["board"]
    width = v_board["width"]
    height = v_board["height"]

    snakes = []
    for s in v_board["snakes"]:
        coords = [(_flip_y((seg["x"], seg["y"]), height)) for seg in s["body"]]
        snakes.append({
            "id": s["id"],
            "health_points": s["health"],
            "coords": coords,
        })

    food = [_flip_y((f["x"], f["y"]), height) for f in v_board["food"]]

    you_id = game_state["you"]["id"]

    return {
        "width": width,
        "height": height,
        "snakes": snakes,
        "food": food,
        "you": you_id,
    }


# original direction (y-down) -> v1 direction (y-up)
_DIR_TO_V1 = {"up": "down", "down": "up", "left": "left", "right": "right"}


# --- routes.py move() logic -------------------------------------------------
def _decide_internal(board, snake):
    """ Reproduces routes.py move() and returns an internal (y-down) direction name. """
    next_move = list()
    thread_pool = list()  # kept for parity; threads run synchronously below
    potential_snake_positions = list()
    path = None

    direction = general_direction(board, snake.head, snake.attributes['health_points'])
    move = direction  # fallback

    for enemy_snake in board.snakes:
        if enemy_snake.attributes['id'] != snake.attributes['id']:
            potential_snake_positions.extend(
                [position for position in enemy_snake.potential_positions() if board.inside(position)])

    number_of_squares = list()
    for cell in neighbours(snake.head):
        if board.inside(cell):
            count = len(flood_fill(board, cell, False))
            number_of_squares.append((cell, count))
            if count <= 10:
                potential_snake_positions.append(cell)

    if (len(number_of_squares) == 4 and number_of_squares[0][1] <= 10 and number_of_squares[1][1] <= 10
            and number_of_squares[2][1] <= 10 and number_of_squares[3][1] <= 10):
        largest = reduce(lambda carry, direction: carry if carry[1] > direction[1] else direction,
                         number_of_squares, number_of_squares[0])
        if largest[0] in potential_snake_positions:
            potential_snake_positions.remove(largest[0])

    food = need_food(board, snake.head, snake.attributes['health_points'])

    if food:
        food_positions = find_food(snake.head, snake.attributes['health_points'], board, food)
        positions = [position[0] for position in food_positions]

        for position in positions:
            bfs(snake.head, position, board, potential_snake_positions, next_move)
            bfs(snake.head, position, board, [], next_move)

        next_move = [p for p in next_move if not len(p) == 0]

        if next_move:
            path = min(next_move, key=len)
            move = get_direction(snake.head, path[0])
    else:
        positions = find_safest_position(snake.head, direction, board)
        positions = [position[0] for position in positions]

        for position in positions:
            bfs(snake.head, position, board, potential_snake_positions, next_move)
            bfs(snake.head, position, board, [], next_move)

        next_move = [p for p in next_move if not len(p) == 0]

        if next_move:
            path = max(next_move, key=len)
            move = get_direction(snake.head, path[0])

    if len(next_move) == 0:
        floods = {
            "up": len(flood_fill(board, (snake.head[0], snake.head[1] - 1))),
            "down": len(flood_fill(board, (snake.head[0], snake.head[1] + 1))),
            "right": len(flood_fill(board, (snake.head[0] + 1, snake.head[1]))),
            "left": len(flood_fill(board, (snake.head[0] - 1, snake.head[1])))
        }
        move = max(floods.keys(), key=(lambda key: floods[key]))

    # don't be stupid
    m_move = add(snake.head, DIR_VECTORS[DIR_NAMES.index(move)])
    if board.inside(m_move) and board.get_cell(m_move) == 1:
        for direction in DIR_NAMES:
            m_move = add(snake.head, DIR_VECTORS[DIR_NAMES.index(direction)])
            if board.inside(m_move) and board.get_cell(m_move) != 1:
                move = direction

    return move


# --- CodeClash v1 API glue --------------------------------------------------
def info():
    # Original start() real values: name 'BETTER THAN ALEKSIY'S SNAKE',
    # color '#ff0000' (hardcoded in the returned dict), head_type 'safe',
    # tail_type 'freckled'. Mapped to v1 head/tail names.
    return {
        "apiversion": "1",
        "author": "rdbrck",
        "color": "#ff0000",
        "head": "safe",
        "tail": "freckled",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _fallback_move(game_state):
    """Guaranteed-legal move: in-bounds and not into any snake body (excluding tails)."""
    try:
        you = game_state["you"]
        board = game_state["board"]
        head = you["body"][0]
        w, h = board["width"], board["height"]
        blocked = set()
        for snake in board["snakes"]:
            b = snake["body"]
            for seg in b[:-1]:
                blocked.add((seg["x"], seg["y"]))
        deltas = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        for mv, (dx, dy) in deltas.items():
            nx, ny = head["x"] + dx, head["y"] + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
                return mv
    except Exception:
        pass
    return "up"


def move(game_state):
    try:
        data = _build_internal_data(game_state)
        board = Board(**data)
        snake = board.get_snake(data["you"])

        chosen = None
        if snake is not None:
            internal_dir = _decide_internal(board, snake)
            chosen = _DIR_TO_V1.get(internal_dir)

        # Validate chosen is legal in v1 space; fall back otherwise.
        if chosen in ("up", "down", "left", "right"):
            you = game_state["you"]
            vboard = game_state["board"]
            head = you["body"][0]
            deltas = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
            dx, dy = deltas[chosen]
            nx, ny = head["x"] + dx, head["y"] + dy
            w, h = vboard["width"], vboard["height"]
            in_bounds = 0 <= nx < w and 0 <= ny < h
            self_hit = (nx, ny) in {(s["x"], s["y"]) for s in you["body"][:-1]}
            if in_bounds and not self_hit:
                return {"move": chosen}

        return {"move": _fallback_move(game_state)}
    except Exception:
        return {"move": _fallback_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
