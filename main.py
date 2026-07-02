"""
Port of pambrose/battlesnake-examples -> SimpleSnake (Kotlin) into CodeClash v1.

Chosen example: SimpleSnake, the most advanced *reactive* snake in the
pambrose Kotlin examples. It reacts to live game state every turn:
  - If food is available, move toward a target food.
  - Otherwise, move toward the board center.

Faithful reproduction notes:
  - Original moves "toward a target position" one axis at a time (x first,
    then y), preferring horizontal correction when x differs, else vertical.
  - Original nearestFood() uses maxByOrNull(Manhattan distance) -- i.e. it
    actually selects the *farthest* food. We reproduce that quirk.
  - The Kotlin framework uses a top-left / y-down coordinate system. CodeClash
    v1 uses a bottom-left / y-up system. We express the "move toward target"
    intent directly in v1 geometry (a move that reduces distance to target),
    which is the faithful behavioral equivalent.

Robustness (required by arena): we never return a move that is out of bounds
or into an occupied snake body (tails are enterable). If the strategy's
preferred move is unsafe, we fall back to any safe move.
"""


def info():
    return {
        "apiversion": "1",
        "author": "pambrose",
        "color": "#ff00ff",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _board_center(width, height):
    # Matches Kotlin Board.center formula.
    cx = (width // 2 if width % 2 == 0 else (width + 1) // 2) - 1
    cy = (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1
    return (cx, cy)


def _move_toward(head, target):
    """Reproduce SimpleSnake.moveTo intent in v1 geometry: correct x first,
    then y. Returns an ordered preference list of directions."""
    hx, hy = head
    tx, ty = target
    prefs = []
    if hx < tx:
        prefs.append("right")
    elif hx > tx:
        prefs.append("left")
    if hy < ty:
        prefs.append("up")
    elif hy > ty:
        prefs.append("down")
    return prefs


def _occupied_cells(game_state, allow_tails=True):
    """Set of cells occupied by snake bodies. Tails are enterable (they move
    on the next turn) unless that snake just ate (health == 100)."""
    blocked = set()
    for snake in game_state["board"]["snakes"]:
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            is_tail = i == n - 1
            if is_tail and allow_tails and n > 1:
                # Tail vacates unless the snake ate this turn (full health).
                if snake.get("health", 0) != 100:
                    continue
            blocked.add(cell)
    return blocked


def _safe_moves(game_state):
    board = game_state["board"]
    width, height = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    blocked = _occupied_cells(game_state, allow_tails=True)

    safe = []
    for move, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        if (nx, ny) in blocked:
            continue
        safe.append(move)
    return safe


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        you = game_state["you"]
        head_seg = you["body"][0]
        head = (head_seg["x"], head_seg["y"])

        # --- SimpleSnake strategy ---
        food = board.get("food", [])
        if food:
            # nearestFood: maxByOrNull(Manhattan) -> farthest food (faithful quirk)
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

        prefs = _move_toward(head, target)

        safe = _safe_moves(game_state)

        # Prefer the strategy's move if it is safe.
        for p in prefs:
            if p in safe:
                return {"move": p}

        # Otherwise any safe move.
        if safe:
            return {"move": safe[0]}

        # No safe move: still return something in-bounds if possible, else up.
        hx, hy = head
        for m, (dx, dy) in DIRS.items():
            nx, ny = hx + dx, hy + dy
            if 0 <= nx < width and 0 <= ny < height:
                return {"move": m}
        return {"move": "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
