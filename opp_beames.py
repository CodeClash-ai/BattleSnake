# beames.ai — Battlesnake 2017 Advanced Division entry (aggressive A* implementation)
# Ported to the CodeClash BattleSnake arena (current API v1) from the original
# old-API bot: https://github.com/kentmacdonald2/battle-snake-2017
#
# Faithful port of the original strategy (app/main.py + app/a_star.py):
#   - rank food by squared-Euclidean distance to the head (get_food_list)
#   - A* (squared-Euclidean, accumulated heuristic; count>499 bailout) to nearest food
#   - the original's second-food fallback control flow is reproduced verbatim,
#     including its quirk that get_food_list(first_food) returns first_food itself
#     as its nearest element (distance 0), so new_list[0] == first_food.
#   - "desperation" fallback: first safe neighbour in fixed order up/down/left/right
#   - if_safe = on the board AND not occupied by any snake body cell
#
# Coordinate note: the original used a top-left / y-down board (up = y-1).
# The v1 API is bottom-left / y-up, so the direction->delta table is remapped
# accordingly (up = y+1) to preserve the visual meaning of each move name.

import typing

AUTHOR = "kentmacdonald2"

# v1 (bottom-left, y-up) direction deltas.  Original was top-left/y-down.
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
# original move()/a_star successor + desperation order: up, down, left, right
PRIORITY = ["up", "down", "left", "right"]


def info() -> typing.Dict:
    # Original /start returned color '#FF00FF', a custom head_url image (no named
    # head), no tail, name 'beames.ai'.  v1 needs named head/tail; the original
    # had none, so keep neutral defaults rather than invent cosmetic values.
    return {
        "apiversion": "1",
        "author": AUTHOR,
        "color": "#FF00FF",
        "head": "default",
        "tail": "default",
    }


def start(game_state: typing.Dict):
    pass


def end(game_state: typing.Dict):
    pass


def _cell(c: typing.Dict) -> tuple:
    return (c["x"], c["y"])


# ---- board helpers (mirror original a_star up/down/left/right on [x, y]) ----
# Directions here operate in v1 (y-up) space; names match the original.
def _step(pos, name):
    vec = DIRS[name]
    return (pos[0] + vec[0], pos[1] + vec[1])


def _if_safe(pos, blocked, w, h) -> bool:
    # original if_safe: not in any snake's coords, and on the board
    if pos in blocked:
        return False
    if pos[0] < 0 or pos[0] > w - 1:
        return False
    if pos[1] < 0 or pos[1] > h - 1:
        return False
    return True


class _Node:
    __slots__ = ("pos", "parent", "f", "g", "h")

    def __init__(self, pos, parent=None, f=0, g=0, h=0):
        self.pos = pos
        self.parent = parent
        self.f = f
        self.g = g
        self.h = h


def _reconstruct(successor):
    # original reconstruct: from goal-neighbour back to (but excluding) start
    out = []
    tmp = successor
    while tmp.parent is not None:
        out.append(tmp.pos)
        tmp = tmp.parent
    return out


def _search(start_pos, blocked, w, h, goal):
    """Faithful port of a_star.search: min-f open list, accumulated squared-
    Euclidean h (h = parent.h + sld), count>499 bailout, returns the reversed
    path list (goal-neighbour first, start excluded) or None."""
    open_list = []
    closed_list = []
    open_list.append(_Node(start_pos, f=0))
    count = 0
    while len(open_list) > 0:
        if count > 499:
            return None
        q = min(open_list, key=lambda n: n.f)
        open_list.remove(q)

        successors = []
        for name in PRIORITY:  # up, down, left, right
            nxt = _step(q.pos, name)
            if _if_safe(nxt, blocked, w, h):
                successors.append(_Node(nxt, parent=q))

        count += 1
        for succ in successors:
            if succ.pos == goal:
                return _reconstruct(succ)
            succ.g = q.g + 1
            sld = (succ.pos[0] - goal[0]) ** 2 + (succ.pos[1] - goal[1]) ** 2
            succ.h = q.h + sld
            succ.f = succ.g + succ.h
            add = True
            for item in open_list:
                if item.pos == succ.pos and item.f < succ.f:
                    add = False
            for item in closed_list:
                if item.pos == succ.pos and item.f < succ.f:
                    add = False
            if add:
                open_list.append(succ)
        closed_list.append(q)
    return None


def _food_list(origin, foods):
    """Mirror get_food_list: every food scored by squared-Euclidean distance
    from origin, sorted ascending.  Returns list of (score, loc)."""
    scored = []
    for f in foods:
        dx = origin[0] - f[0]
        dy = origin[1] - f[1]
        scored.append((dx * dx + dy * dy, f))
    scored.sort(key=lambda t: t[0])
    return scored


def _dir_of_step(head, first_move) -> str:
    for name in PRIORITY:
        if _step(head, name) == first_move:
            return name
    return "up"


def _decide(game_state: typing.Dict) -> str:
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = _cell(game_state["you"]["body"][0])

    blocked = set()
    for s in board["snakes"]:
        for c in s["body"]:
            blocked.add(_cell(c))

    foods = [_cell(f) for f in board["food"]]
    if not foods:
        # original would crash (sorted_list[0]); fall straight to desperation.
        return _desperation(head, blocked, w, h)

    sorted_list = _food_list(head, foods)
    first_food = sorted_list[0][1]

    primary_path = _search(head, blocked, w, h, first_food)
    sec_path = None

    if len(sorted_list) > 1:
        sec_food = sorted_list[1][1]
        new_list = _food_list(first_food, foods)      # nearest to first_food == first_food
        sec_path = _search(first_food, blocked, w, h, new_list[0][1])
        new_path = _search(head, blocked, w, h, new_list[0][1])

        if not primary_path and sec_path:
            primary_path = new_path

        if not sec_path:
            primary_path = _search(head, blocked, w, h, sec_food)

    if not primary_path:
        return _desperation(head, blocked, w, h)

    first_move = primary_path[-1]  # step adjacent to head (original primary_path[-1])
    return _dir_of_step(head, first_move)


def _desperation(head, blocked, w, h) -> str:
    for name in PRIORITY:  # up, down, left, right
        if _if_safe(_step(head, name), blocked, w, h):
            return name
    return "up"  # original returns default 'up' if nothing safe


def move(game_state: typing.Dict) -> typing.Dict:
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
