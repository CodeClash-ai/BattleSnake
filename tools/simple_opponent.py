"""Local recreation of pambrose Kotlin SimpleSnake opponent for testing."""

def info():
    return {"apiversion": "1", "author": "opp", "color": "#ff00ff", "head": "beluga", "tail": "bolt"}

def start(game_state): return None
def end(game_state): return None

def _manhattan(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
def _board_center(width, height): return ((width // 2 if width % 2 == 0 else (width + 1) // 2) - 1, (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1)
def _move_to(head, target):
    hx, hy = head; tx, ty = target
    if hx > tx: return "left"
    if hx < tx: return "right"
    if hy > ty: return "down"
    return "up"

def move(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        hs = game_state["you"]["body"][0]
        head = (hs["x"], hs["y"])
        food = board.get("food", [])
        if food:
            target, best = None, -1
            for f in food:
                fp = (f["x"], f["y"]); d = _manhattan(head, fp)
                if d > best:
                    best, target = d, fp
        else:
            target = _board_center(w, h)
        return {"move": _move_to(head, target)}
    except Exception:
        return {"move": "up"}

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
