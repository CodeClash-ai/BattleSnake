# TR-8R — winner, Battlesnake Victoria 2016 Advanced Division
# Ported to the CodeClash BattleSnake arena (current API v1) from the original
# old-API bot: https://github.com/noahspriggs/battlesnake-python
#
# Faithful port of the original strategy:
#   - A* to the reachable food closest to the board centre
#   - skip food that an enemy would reach first (enemy_dist <= path steps)
#   - self-trap avoidance: only commit to food if a path from the food back to
#     our own tail still exists
#   - head-to-head avoidance ("SAFTEY"): block the orthogonal cells around any
#     nearby (<= SNEK_BUFFER) enemy head whose snake is at least as long as us
#   - time-aware own-tail model: the last `score` segments of our own tail are
#     treated passable once we are `score` steps into the path (they will have
#     vacated by then); enemy bodies are always solid
#   - fall back to chasing our own tail, then two "despair" tiers: first avoid
#     danger zones, then ignore them entirely, then any legal cell
#
# Coordinate note: the original used a top-left / y-down board; the v1 API uses a
# bottom-left / y-up board. The port operates natively in v1 coordinates, so the
# direction names map to v1 deltas directly (up=y+1, down=y-1, left=x-1,
# right=x+1); no board flip is required because A* is coordinate-agnostic.

import typing

AUTHOR = "noahspriggs"
SNEK_BUFFER = 3  # original constant
DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info() -> typing.Dict:
    return {
        "apiversion": "1",
        "author": AUTHOR,
        "color": "#00ff00",  # original index() color
        "head": "default",   # original used a gif image (no named v1 type)
        "tail": "default",   # original set no tail
    }


def start(game_state: typing.Dict):
    pass


def end(game_state: typing.Dict):
    pass


def _cell(c: typing.Dict) -> tuple:
    return (c["x"], c["y"])


def _dist(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _direction(from_cell: tuple, to_cell: tuple) -> str:
    dx = to_cell[0] - from_cell[0]
    dy = to_cell[1] - from_cell[1]
    if dx == 1:
        return "right"
    elif dx == -1:
        return "left"
    elif dy == 1:
        return "up"
    elif dy == -1:
        return "down"
    return "up"


def _neighbours(node, blocked, danger, w, h, own_tail, score, ignore_danger):
    """Faithful port of AStar.neighbours.

    `own_tail` is our own body head->tail. As with the original, the last
    `score` segments of it are considered passable (subtail) because they will
    have vacated by the time we arrive `score` steps into the path.
    """
    if score >= len(own_tail):
        subtail = set(own_tail)
    else:
        subtail = set(own_tail[len(own_tail) - score:]) if score > 0 else set()

    result = []
    for vec in DIRS.values():
        p = (node[0] + vec[0], node[1] + vec[1])
        if not (0 <= p[0] < w and 0 <= p[1] < h):
            continue
        # cell is passable if it is not blocked (and not a danger cell when we
        # are avoiding danger) OR it is a soon-to-vacate segment of our own tail
        is_blocked = p in blocked or (not ignore_danger and p in danger)
        if (not is_blocked) or (p in subtail):
            result.append(p)
    return result


def _a_star(start_pos, goal, blocked, danger, w, h, own_tail, ignore_danger=False):
    start_pos = tuple(start_pos)
    goal = tuple(goal)

    closed_set = set()
    open_set = [start_pos]
    came_from = {}

    g_score = {start_pos: 0}
    f_score = {start_pos: _dist(start_pos, goal)}

    while open_set:
        current = min(open_set, key=lambda p: f_score.get(p, 10000))
        if current == goal:
            # reconstruct
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        open_set.remove(current)
        closed_set.add(current)

        score = g_score[current]
        for nb in _neighbours(current, blocked, danger, w, h, own_tail, score, ignore_danger):
            # the goal is always reachable even if it sits on a blocked cell
            # (matches original: food/tail goals are found by equality first)
            if nb in closed_set and nb != goal:
                continue
            tentative_g = g_score[current] + 1
            if nb not in open_set:
                open_set.append(nb)
            elif tentative_g >= g_score.get(nb, 10000):
                continue
            came_from[nb] = current
            g_score[nb] = tentative_g
            f_score[nb] = tentative_g + _dist(nb, goal)

    return None


def _build_grid(game_state: typing.Dict):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_id = you["id"]

    blocked = set()  # all snake body cells (SNAKE / WALL equivalent) - always solid
    for s in board["snakes"]:
        for c in s["body"]:
            blocked.add(_cell(c))

    # SAFTEY danger zones around nearby, >= length enemy heads
    head = _cell(you["body"][0])
    my_len = you["length"]
    danger = set()
    for s in board["snakes"]:
        if s["id"] == my_id:
            continue
        eh = _cell(s["body"][0])
        if _dist(head, eh) > SNEK_BUFFER:
            continue
        if s["length"] >= my_len:  # len(enemy) > len(snek)-1
            for vec in DIRS.values():
                p = (eh[0] + vec[0], eh[1] + vec[1])
                if 0 <= p[0] < w and 0 <= p[1] < h:
                    danger.add(p)
    return w, h, blocked, danger


def _decide(game_state: typing.Dict) -> str:
    board = game_state["board"]
    you = game_state["you"]
    w, h, blocked, danger = _build_grid(game_state)

    own_body = [_cell(c) for c in you["body"]]
    head = own_body[0]
    my_tail = own_body[-1]

    center = (w // 2, h // 2)
    foods = sorted((_cell(f) for f in board["food"]), key=lambda p: _dist(p, center))

    enemies = [s for s in board["snakes"] if s["id"] != you["id"]]

    path = None
    for food in foods:
        tentative = _a_star(head, food, blocked, danger, w, h, own_body)
        if not tentative:
            continue

        path_length = len(tentative)  # includes start node

        # enemy reaches food first? (original: path_length > enemy_dist)
        dead = False
        for e in enemies:
            if path_length > _dist(_cell(e["body"][0]), food):
                dead = True
                break
        if dead:
            continue

        # self-trap check: can we still reach our own tail from the food?
        food_to_tail = _a_star(food, my_tail, blocked, danger, w, h, own_body)
        if food_to_tail:
            path = tentative
            break

    # no safe food -> chase our own tail
    if not path:
        path = _a_star(head, my_tail, blocked, danger, w, h, own_body)

    # despair tier 1: any neighbour, avoiding danger zones
    if not (path and len(path) > 1):
        for nb in _neighbours(head, blocked, danger, w, h, own_body, 0, False):
            path = _a_star(head, nb, blocked, danger, w, h, own_body)
            break

    # despair tier 2: any neighbour, ignoring danger zones
    if not (path and len(path) > 1):
        for nb in _neighbours(head, blocked, danger, w, h, own_body, 0, True):
            path = _a_star(head, nb, blocked, danger, w, h, own_body, ignore_danger=True)
            break

    if path and len(path) > 1:
        return _direction(path[0], path[1])

    return _any_safe(game_state)


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


def move(game_state: typing.Dict) -> typing.Dict:
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return {"move": _any_safe(game_state)}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
