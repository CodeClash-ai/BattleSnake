"""Local reference port for coreyja__amphibious-arthur.

Copied from origin/human/coreyja/amphibious-arthur for local testing and
one-ply prediction notes.  It approximates the Rust bot's health/space recursion
and tie order (Up, Down, Left, Right with last max tie winning).
"""

PREFERRED_HEALTH = 80
RECURSION_LIMIT = 5
DIRS = [
    ("up", (0, 1)),
    ("down", (0, -1)),
    ("left", (-1, 0)),
    ("right", (1, 0)),
]


def info():
    return {"apiversion": "1", "author": "coreyja", "color": "#AA66CC", "head": "trans-rights-scarf", "tail": "swirl"}


def start(game_state):
    return None


def end(game_state):
    return None


def _body_set(board):
    occ = set()
    for s in board.get("snakes", []):
        for c in s.get("body", []):
            occ.add((c["x"], c["y"]))
    return occ


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _neighbors(x, y, w, h):
    out = []
    for _mv, (dx, dy) in DIRS:
        nx, ny = x + dx, y + dy
        if _in_bounds(nx, ny, w, h):
            out.append((nx, ny))
    return out


def _score(coor, health, occupied, w, h, times_to_recurse):
    if coor in occupied or health == 0:
        return 0
    current_score = PREFERRED_HEALTH - abs(health - PREFERRED_HEALTH)
    if times_to_recurse == 0:
        return current_score
    recursed_score = 0
    for nb in _neighbors(coor[0], coor[1], w, h):
        recursed_score += _score(nb, health, occupied, w, h, times_to_recurse - 1)
    return current_score + recursed_score // 2


def move(game_state):
    try:
        board = game_state["board"]
        w = board["width"]
        h = board["height"]
        you = game_state["you"]
        hx, hy = you["head"]["x"], you["head"]["y"]
        health = you.get("health", PREFERRED_HEALTH)
        occupied = _body_set(board)
        best_mv = None
        best_score = None
        for mv, (dx, dy) in DIRS:
            nx, ny = hx + dx, hy + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            s = _score((nx, ny), health, occupied, w, h, RECURSION_LIMIT)
            if best_score is None or s >= best_score:
                best_score = s
                best_mv = mv
        return {"move": best_mv or "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
