"""Reference re-implementation of the opponent's known baseline strategy
(pambrose-kotlin SimpleSnake) for local testing purposes only."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import run_server


def info():
    return {"apiversion": "1", "author": "opp", "color": "#00ffff", "head": "beluga", "tail": "bolt"}


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _board_center(width, height):
    center_x = (width // 2 if width % 2 == 0 else (width + 1) // 2) - 1
    center_y = (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1
    return (center_x, center_y)


def _move_to(head, target):
    hx, hy = head
    tx, ty = target
    if hx > tx:
        return "left"
    if hx < tx:
        return "right"
    if hy > ty:
        return "down"
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        head_seg = game_state["you"]["body"][0]
        head = (head_seg["x"], head_seg["y"])
        food = board.get("food", [])
        if food:
            target = None
            best = -1
            for f in food:
                fp = (f["x"], f["y"])
                d = _manhattan(head, fp)
                if d > best:
                    best = d
                    target = fp
        else:
            target = _board_center(width, height)
        return {"move": _move_to(head, target)}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    run_server({"info": info, "start": start, "move": move, "end": end})
