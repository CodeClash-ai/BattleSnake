"""Local recreation of observed Nettogrof long-game behavior.

The Java opponent in round-1 logs mostly performs a vertical lawnmower sweep:
continue up/down a column, step left at the top/bottom, then reverse.  It eats
food only incidentally.  This tool is for local smoke tests; the true opponent
may still timeout or differ in edge cases.
"""

MOVES = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}

def info():
    return {"apiversion": "1", "author": "lawnmower", "color": "#212161"}

def start(game_state): return None
def end(game_state): return None

def _pt(p): return (p["x"], p["y"])
def _in(p, w, h): return 0 <= p[0] < w and 0 <= p[1] < h

def move(game_state):
    try:
        board = game_state["board"]; w, h = board["width"], board["height"]
        body = [_pt(p) for p in game_state["you"]["body"]]
        head = body[0]; neck = body[1] if len(body) > 1 else head
        blocked = set()
        for sn in board.get("snakes", []):
            b = [_pt(p) for p in sn.get("body", [])]
            blocked.update(b[:-1])
        hx, hy = head
        if neck[0] == hx and neck[1] < hy:
            prefs = ["up", "left", "right", "down"]
        elif neck[0] == hx and neck[1] > hy:
            prefs = ["down", "left", "right", "up"]
        elif hy >= h - 1:
            prefs = ["down", "left", "right", "up"]
        elif hy <= 0:
            prefs = ["up", "left", "right", "down"]
        else:
            prefs = ["up", "down", "left", "right"]
        for m in prefs:
            dx, dy = MOVES[m]; p = (hx + dx, hy + dy)
            if _in(p, w, h) and p not in blocked:
                return {"move": m}
        return {"move": prefs[0]}
    except Exception:
        return {"move": "up"}

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
