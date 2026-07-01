# beames.ai — Battlesnake 2017 Advanced Division entry (aggressive A* implementation)
# Ported to the CodeClash BattleSnake arena (current API v1) from the original
# old-API bot: https://github.com/kentmacdonald2/battle-snake-2017
#
# Faithful port of the original strategy:
#   - rank food by squared-Euclidean distance to the head
#   - A* (squared-Euclidean heuristic, ~500-node budget) to the nearest food
#   - if no path to the nearest food, fall back to the second-nearest
#   - "desperation" fallback: first safe neighbour in fixed order up/down/left/right
#   - safety = in bounds and not occupied by any snake body cell
#
# Coordinate note: original used top-left / y-down; v1 API is bottom-left / y-up.

import heapq
import typing

AUTHOR = "kentmacdonald2"
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
# original desperation order was up, down, left, right
PRIORITY = ["up", "down", "left", "right"]


def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": AUTHOR,
        "color": "#ff00ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state: typing.Dict):
    pass


def end(game_state: typing.Dict):
    pass


def _cell(c: typing.Dict) -> tuple:
    return (c["x"], c["y"])


def _dir(a: tuple, b: tuple) -> str:
    delta = (b[0] - a[0], b[1] - a[1])
    for name, vec in DIRS.items():
        if vec == delta:
            return name
    return "up"


def _search(start_pos, goal, blocked, w, h, cap=500):
    """A* with a squared-Euclidean heuristic and a node budget (matches the
    original's count>499 bailout)."""

    def heur(p):
        return (p[0] - goal[0]) ** 2 + (p[1] - goal[1]) ** 2

    open_heap = [(heur(start_pos), 0, start_pos)]
    came_from = {start_pos: None}
    best_g = {start_pos: 0}
    count = 0
    while open_heap:
        if count > cap:
            return None
        count += 1
        _, g, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = [cur]
            while came_from[cur] is not None:
                cur = came_from[cur]
                path.append(cur)
            return list(reversed(path))
        for vec in DIRS.values():
            nb = (cur[0] + vec[0], cur[1] + vec[1])
            if not (0 <= nb[0] < w and 0 <= nb[1] < h):
                continue
            if nb in blocked and nb != goal:
                continue
            ng = g + 1
            if nb not in best_g or ng < best_g[nb]:
                best_g[nb] = ng
                came_from[nb] = cur
                heapq.heappush(open_heap, (ng + heur(nb), ng, nb))
    return None


def _safe(pos, blocked, w, h) -> bool:
    return 0 <= pos[0] < w and 0 <= pos[1] < h and pos not in blocked


def _decide(game_state: typing.Dict) -> str:
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = _cell(game_state["you"]["body"][0])

    blocked = set()
    for s in board["snakes"]:
        for c in s["body"]:
            blocked.add(_cell(c))

    foods = [_cell(f) for f in board["food"]]
    if foods:
        foods.sort(key=lambda p: (p[0] - head[0]) ** 2 + (p[1] - head[1]) ** 2)
        path = _search(head, foods[0], blocked, w, h)
        if not path and len(foods) > 1:
            path = _search(head, foods[1], blocked, w, h)
        if path and len(path) >= 2:
            return _dir(head, path[1])

    for name in PRIORITY:
        vec = DIRS[name]
        if _safe((head[0] + vec[0], head[1] + vec[1]), blocked, w, h):
            return name
    return "up"


def move(game_state: typing.Dict) -> typing.Dict:
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
