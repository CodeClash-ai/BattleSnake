# BTAS ("Better Than Aleksiy's Snake") — winner, Battlesnake Victoria 2017 Advanced
# Ported to the CodeClash BattleSnake arena (current API v1) from the original
# old-API bot: https://github.com/rdbrck/battlesnake-2017-btas
#
# Faithful port of the original multi-file strategy (strategy.py / algorithms.py /
# routes.py):
#   - general_direction(): heuristic fallback direction that avoids walls & snakes
#     and is pulled toward food when health drops below 75
#   - danger cells: enemy heads' potential next positions, plus any neighbour of our
#     head whose flood-fill area is small (<=10); if every neighbour is small, keep
#     the largest so we never voluntarily trap ourselves
#   - need_food(): health-based thresholds (more aggressive with more snakes on board)
#   - if food is needed: rate food cells by their surroundings, BFS to each candidate
#     avoiding danger cells, and take the SHORTEST path
#   - otherwise: move toward the most open space (largest flood-fill), i.e. the
#     "find_safest_position" behaviour, taking the LONGEST survivable path
#   - final safety net never steps into a snake body
#
# Coordinate note: original used top-left / y-down; v1 API is bottom-left / y-up, so
# the general_direction heuristic is re-derived in y-up coordinates.

import typing
from collections import deque

AUTHOR = "rdbrck"
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}

EMPTY, SNAKE, FOOD = 0, 1, 2


def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": AUTHOR,
        "color": "#ff0000",
        "head": "safe",
        "tail": "freckled",
    }


def start(game_state: typing.Dict):
    pass


def end(game_state: typing.Dict):
    pass


def _cell(c: typing.Dict) -> tuple:
    return (c["x"], c["y"])


def _dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbours(p):
    return [(p[0], p[1] + 1), (p[0] + 1, p[1]), (p[0], p[1] - 1), (p[0] - 1, p[1])]


def _surrounding(p):
    return _neighbours(p) + [
        (p[0] + 1, p[1] + 1),
        (p[0] + 1, p[1] - 1),
        (p[0] - 1, p[1] + 1),
        (p[0] - 1, p[1] - 1),
    ]


class Board:
    def __init__(self, game_state):
        b = game_state["board"]
        self.w, self.h = b["width"], b["height"]
        self.food = {_cell(f) for f in b["food"]}
        self.snake_cells = set()
        for s in b["snakes"]:
            for c in s["body"]:
                self.snake_cells.add(_cell(c))

    def inside(self, p):
        return 0 <= p[0] < self.w and 0 <= p[1] < self.h

    def vacant(self, p):
        return self.inside(p) and p not in self.snake_cells

    def get_cell(self, p):
        if p in self.snake_cells:
            return SNAKE
        if p in self.food:
            return FOOD
        return EMPTY


def _dir(a, b):
    delta = (b[0] - a[0], b[1] - a[1])
    for name, vec in DIRS.items():
        if vec == delta:
            return name
    return "up"


def general_direction(board, head, health, snakes):
    score = {
        "up": 5000.0 / ((board.h - 1 - head[1]) + 1),
        "down": 5000.0 / (head[1] + 1),
        "right": 5000.0 / ((board.w - 1 - head[0]) + 1),
        "left": 5000.0 / (head[0] + 1),
    }
    if not board.vacant((head[0] - 1, head[1])):
        score["left"] += 1_000_000
    if not board.vacant((head[0] + 1, head[1])):
        score["right"] += 1_000_000
    if not board.vacant((head[0], head[1] + 1)):
        score["up"] += 1_000_000
    if not board.vacant((head[0], head[1] - 1)):
        score["down"] += 1_000_000

    for s in snakes:
        for pos in (_cell(c) for c in s["body"]):
            if pos == head:
                continue
            d = _dist(pos, head) or 1
            if pos[0] > head[0]:
                score["right"] += 1000.0 / d
            elif pos[0] < head[0]:
                score["left"] += 1000.0 / d
            if pos[1] > head[1]:
                score["up"] += 1000.0 / d
            elif pos[1] < head[1]:
                score["down"] += 1000.0 / d

    if health < 75:
        for pos in board.food:
            d = _dist(pos, head) or 1
            pull = (10000.0 / ((health / 10.0) + 1)) / d
            if pos[0] > head[0]:
                score["right"] -= pull
            elif pos[0] < head[0]:
                score["left"] -= pull
            if pos[1] > head[1]:
                score["up"] -= pull
            elif pos[1] < head[1]:
                score["down"] -= pull

    return min(score, key=score.get)


def need_food(board, head, health, num_snakes):
    if health < 50:
        urgent = [f for f in board.food if (health + _dist(head, f)) < 50]
        if urgent:
            return urgent
    want = []
    for f in board.food:
        if _dist(f, head) <= 2 and health < (((num_snakes + 1) * 7) + 15):
            want.append(f)
        elif health < 50:
            want.append(f)
    return want or None


def flood_fill(board, start_pos):
    if not board.vacant(start_pos):
        return set()
    visited = {start_pos}
    todo = deque([start_pos])
    while todo:
        cur = todo.popleft()
        for p in _neighbours(cur):
            if p not in visited and board.vacant(p):
                visited.add(p)
                todo.append(p)
    return visited


def bfs(board, start_pos, target, blocked):
    """Shortest path from start to target (excluding start), avoiding snakes and the
    given blocked set. Target itself is always allowed."""
    parent = {start_pos: None}
    todo = deque([start_pos])
    while todo:
        cur = todo.popleft()
        if cur == target:
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return list(reversed(path))[1:]
        for p in _neighbours(cur):
            if p in parent:
                continue
            if p != target and (not board.vacant(p) or p in blocked):
                continue
            if not board.inside(p):
                continue
            parent[p] = cur
            todo.append(p)
    return None


def _rate_cell(board, cell):
    weights = {EMPTY: 0.5, SNAKE: -5, FOOD: 2}
    return sum(weights.get(board.get_cell(m), 0) for m in _surrounding(cell) if board.inside(m))


def _decide(game_state):
    board = Board(game_state)
    you = game_state["you"]
    head = _cell(you["body"][0])
    health = you["health"]
    snakes = game_state["board"]["snakes"]
    enemies = [s for s in snakes if s["id"] != you["id"]]

    fallback = general_direction(board, head, health, snakes)

    danger = set()
    for e in enemies:
        eh = _cell(e["body"][0])
        for p in _neighbours(eh):
            if board.inside(p):
                danger.add(p)

    areas = []
    for nb in _neighbours(head):
        if board.inside(nb):
            areas.append((nb, len(flood_fill(board, nb))))
    small = [nb for nb, a in areas if a <= 10]
    if areas and all(a <= 10 for _, a in areas):
        largest = max(areas, key=lambda t: t[1])[0]
        small = [nb for nb in small if nb != largest]
    danger.update(small)

    food = need_food(board, head, health, len(snakes))
    path = None
    if food:
        rated = sorted(food, key=lambda f: _rate_cell(board, f), reverse=True)
        paths = [bfs(board, head, f, danger) for f in rated]
        paths = [p for p in paths if p]
        if paths:
            path = min(paths, key=len)  # shortest route to food
    if path is None:
        # find the most open space: longest survivable path toward roomy cells
        targets = sorted(
            (c for c in _all_cells(board) if board.vacant(c)),
            key=lambda c: _rate_cell(board, c),
            reverse=True,
        )[:6]
        paths = [bfs(board, head, t, danger) for t in targets]
        paths = [p for p in paths if p]
        if paths:
            path = max(paths, key=len)  # keep our options open

    if path:
        move_name = _dir(head, path[0])
    else:
        move_name = fallback

    # never step directly into a snake; prefer the roomiest legal neighbour
    target_cell = (head[0] + DIRS[move_name][0], head[1] + DIRS[move_name][1])
    if not board.vacant(target_cell):
        floods = {
            name: len(flood_fill(board, (head[0] + vec[0], head[1] + vec[1])))
            for name, vec in DIRS.items()
        }
        move_name = max(floods, key=floods.get)
    return move_name


def _all_cells(board):
    for x in range(board.w):
        for y in range(board.h):
            yield (x, y)


def move(game_state: typing.Dict) -> typing.Dict:
    try:
        return {"move": _decide(game_state)}
    except Exception:
        board = game_state["board"]
        head = _cell(game_state["you"]["body"][0])
        blocked = {(_cell(c)) for s in board["snakes"] for c in s["body"][:-1]}
        for name, vec in DIRS.items():
            nb = (head[0] + vec[0], head[1] + vec[1])
            if 0 <= nb[0] < board["width"] and 0 <= nb[1] < board["height"] and nb not in blocked:
                return {"move": name}
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
