"""
Port of tim-hub/awesome-snake (Python/Flask) to CodeClash Battlesnake v1 arena format.

Original strategy (bot.py -> make_a_decision / get_map / survive):
  - Build a map of every cell on the board and flag it:
        'b' = occupied by any snake body segment
        'f' = food
        ' ' = empty
    Cells off the board are absent from the map (lookup returns False).
  - Look only at the 4 tiles immediately around our head ("survive" strategy)
    and score each candidate destination cell:
        off-board  -> -100
        food ('f') ->   +1
        body ('b') ->   -1
        empty (' ')->    0
    Pick the direction with the highest score, using a random tiebreak
    (max over key of score + random.random()).

The original used the OLD Battlesnake API (top-left origin, y increasing
downward). Its direction labels were chosen for that system. Here we
reimplement the identical scoring logic against the CURRENT v1 API
(bottom-left origin, y increasing upward): up=y+1, down=y-1,
left=x-1, right=x+1. The scoring semantics are preserved faithfully;
only the direction labeling is remapped to v1 so moves are correct.
"""
import random


def info():
    return {
        "apiversion": "1",
        "author": "tim-hub",
        "color": "#800000",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return


def end(game_state):
    return


def _build_map(board):
    """Reproduce get_map(): flag every cell as body/food/empty.

    Returns a dict keyed by (x, y). Cells absent from the dict are
    off-board (equivalent to the original's the_map_dict.get(..., False)).
    """
    width = board.get("width", 0)
    height = board.get("height", 0)
    snakes = board.get("snakes", [])
    food = board.get("food", [])

    # All body segments across all snakes (matches reduce of all bodies).
    body_cells = set()
    for s in snakes:
        for seg in s.get("body", []):
            body_cells.add((seg.get("x"), seg.get("y")))

    food_cells = set((f.get("x"), f.get("y")) for f in food)

    the_map = {}
    for y in range(height):
        for x in range(width):
            if (x, y) in body_cells:
                the_map[(x, y)] = "b"
            elif (x, y) in food_cells:
                the_map[(x, y)] = "f"
            else:
                the_map[(x, y)] = " "
    return the_map


def _survive(head, the_map):
    """Reproduce survive(): score the 4 neighbor cells and pick the best.

    Remapped to v1 coordinates (bottom-left origin, y up):
        up    -> (x, y + 1)
        down  -> (x, y - 1)
        left  -> (x - 1, y)
        right -> (x + 1, y)
    Scoring identical to the original.
    """
    x = head.get("x")
    y = head.get("y")

    candidates = {
        "up": (x, y + 1),
        "down": (x, y - 1),
        "left": (x - 1, y),
        "right": (x + 1, y),
    }

    scores = {}
    for direction, cell in candidates.items():
        flag = the_map.get(cell, False)
        if flag is False:
            scores[direction] = -100
        elif flag == "f":
            scores[direction] = 1
        elif flag == "b":
            scores[direction] = -1
        else:
            scores[direction] = 0

    # max over score + random tiebreak, exactly as the original.
    best = max(scores.keys(), key=lambda d: scores[d] + random.random())
    return best


def _safe_fallback(game_state):
    """Guaranteed-legal fallback: in-bounds and not into a snake body
    (tails are enterable)."""
    board = game_state.get("board", {})
    you = game_state.get("you", {})
    width = board.get("width", 11)
    height = board.get("height", 11)
    head = you.get("body", [{}])[0]
    hx = head.get("x", 0)
    hy = head.get("y", 0)

    # Occupied cells = all snake bodies except each snake's tail (tail moves).
    blocked = set()
    for s in board.get("snakes", []):
        body = s.get("body", [])
        for i, seg in enumerate(body):
            # Tail (last segment) is enterable unless the snake just ate
            # (health == 100 implies tail will not move). Be conservative
            # only about the plain tail case; still block if health full.
            if i == len(body) - 1 and s.get("health", 0) != 100 and len(body) > 1:
                continue
            blocked.add((seg.get("x"), seg.get("y")))

    options = {
        "up": (hx, hy + 1),
        "down": (hx, hy - 1),
        "left": (hx - 1, hy),
        "right": (hx + 1, hy),
    }
    for direction, (nx, ny) in options.items():
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
            return direction
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        you = game_state["you"]
        the_map = _build_map(board)
        head = you["body"][0]
        chosen = _survive(head, the_map)

        # Safety net: the original scoring can still pick a wall (-100) or
        # a body (-1) when all four options are bad. Guarantee the returned
        # move is in-bounds and not into a body if any such move exists.
        width = board.get("width", 11)
        height = board.get("height", 11)
        hx, hy = head.get("x"), head.get("y")
        cell_of = {
            "up": (hx, hy + 1),
            "down": (hx, hy - 1),
            "left": (hx - 1, hy),
            "right": (hx + 1, hy),
        }
        nx, ny = cell_of[chosen]
        in_bounds = 0 <= nx < width and 0 <= ny < height
        into_body = the_map.get((nx, ny)) == "b"
        if not in_bounds or into_body:
            return {"move": _safe_fallback(game_state)}
        return {"move": chosen}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
