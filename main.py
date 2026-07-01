# TR-8R — winner, Battlesnake Victoria 2016 Advanced Division
# Ported to the CodeClash BattleSnake arena (current API v1) from the original
# old-API bot: https://github.com/noahspriggs/battlesnake-python
#
# Faithful port of the original strategy:
#   - A* to the reachable food closest to the board centre
#   - skip food that an enemy would reach first
#   - self-trap avoidance: only commit to food if a path from the food back to
#     our own tail still exists
#   - head-to-head avoidance: block the cells around any nearby enemy head whose
#     snake is at least as long as us
#   - fall back to chasing our own tail, then to any safe neighbouring cell
#
# Coordinate note: the original used a top-left / y-down board; the v1 API uses a
# bottom-left / y-up board, so all directions are remapped here.

import heapq
import typing

AUTHOR = "noahspriggs"
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": AUTHOR,
        "color": "#00cc44",
        "head": "default",
        "tail": "default",
    }


def start(game_state: typing.Dict):
    pass


def end(game_state: typing.Dict):
    pass


def _cell(c: typing.Dict) -> tuple:
    return (c["x"], c["y"])


def _manhattan(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _dir(a: tuple, b: tuple) -> str:
    delta = (b[0] - a[0], b[1] - a[1])
    for name, vec in DIRS.items():
        if vec == delta:
            return name
    return "up"


def _make_passable(blocked, tails, danger, w, h, allow):
    def passable(p):
        if not (0 <= p[0] < w and 0 <= p[1] < h):
            return False
        if p in allow:
            return True
        if p in danger:
            return False
        if p in blocked and p not in tails:
            return False
        return True

    return passable


def _astar(start_pos, goal, passable, w, h):
    open_heap = [(_manhattan(start_pos, goal), 0, start_pos)]
    came_from = {start_pos: None}
    best_g = {start_pos: 0}
    while open_heap:
        _, g, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = [cur]
            while came_from[cur] is not None:
                cur = came_from[cur]
                path.append(cur)
            return list(reversed(path))
        for vec in DIRS.values():
            nb = (cur[0] + vec[0], cur[1] + vec[1])
            if nb != goal and not passable(nb):
                continue
            if not (0 <= nb[0] < w and 0 <= nb[1] < h):
                continue
            ng = g + 1
            if nb not in best_g or ng < best_g[nb]:
                best_g[nb] = ng
                came_from[nb] = cur
                heapq.heappush(open_heap, (ng + _manhattan(nb, goal), ng, nb))
    return None


def _any_safe(game_state: typing.Dict) -> str:
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = _cell(game_state["you"]["body"][0])
    blocked = set()
    for s in board["snakes"]:
        for c in s["body"][:-1]:  # tails will move
            blocked.add(_cell(c))
    for name, vec in DIRS.items():
        nb = (head[0] + vec[0], head[1] + vec[1])
        if 0 <= nb[0] < w and 0 <= nb[1] < h and nb not in blocked:
            return name
    return "down"


def _decide(game_state: typing.Dict) -> str:
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    body = [_cell(c) for c in you["body"]]
    head = body[0]
    my_len = you["length"]

    blocked = set()
    tails = set()
    for s in board["snakes"]:
        sbody = [_cell(c) for c in s["body"]]
        blocked.update(sbody)
        if len(sbody) >= 2 and sbody[-1] != sbody[-2]:  # tail moves unless just ate
            tails.add(sbody[-1])

    danger = set()
    enemies = [s for s in board["snakes"] if s["id"] != you["id"]]
    for s in enemies:
        eh = _cell(s["body"][0])
        if _manhattan(eh, head) <= 3 and s["length"] >= my_len:
            for vec in DIRS.values():
                danger.add((eh[0] + vec[0], eh[1] + vec[1]))

    foods = [_cell(f) for f in board["food"]]
    center = (w // 2, h // 2)
    foods.sort(key=lambda p: _manhattan(p, center))

    my_tail = body[-1]
    for food in foods:
        passable = _make_passable(blocked, tails, danger, w, h, frozenset([food]))
        path = _astar(head, food, passable, w, h)
        if not path or len(path) < 2:
            continue
        steps = len(path) - 1
        if any(_manhattan(_cell(e["body"][0]), food) < steps for e in enemies):
            continue  # an enemy gets there first
        passable_tail = _make_passable(blocked, tails, danger, w, h, frozenset([food, my_tail]))
        if _astar(food, my_tail, passable_tail, w, h):  # still reach our tail afterwards
            return _dir(head, path[1])

    # no safe food: chase our own tail
    passable_tail = _make_passable(blocked, tails, danger, w, h, frozenset([my_tail]))
    path = _astar(head, my_tail, passable_tail, w, h)
    if path and len(path) >= 2:
        return _dir(head, path[1])

    return _any_safe(game_state)


def move(game_state: typing.Dict) -> typing.Dict:
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return {"move": _any_safe(game_state)}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
