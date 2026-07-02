"""Port of amphibious_arthur (coreyja/battlesnake-rs) to CodeClash v1 API.

FIDELITY: approximate. The original recursively scores moves with a
health-based heuristic (PREFERRED_HEALTH=80), returning 0 for moves into a
snake body or that kill you, and otherwise `PREFERRED_HEALTH - |health - 80|`
plus half the summed recursive neighbor scores (recursion limit 5). It also
simulates you moving forward each ply ("opponent sprawl"). We reproduce the
health-scoring recursion and body/bounds avoidance, but simplify the
opponent-sprawl clone and cap recursion depth for the <1s time budget.
"""

PREFERRED_HEALTH = 80
RECURSION_LIMIT = 4  # original default 5; capped for time budget

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#AA66CC",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _body_set(board, exclude_tails=True):
    """Set of occupied cells. Tails are enterable (excluded) unless the snake
    just ate (health==100 heuristic -> tail stays)."""
    occ = set()
    for s in board.get("snakes", []):
        body = s.get("body", [])
        n = len(body)
        for i, c in enumerate(body):
            if exclude_tails and i == n - 1 and n > 1:
                # tail vacates next turn unless snake just ate
                if s.get("health", 0) != 100:
                    continue
            occ.add((c["x"], c["y"]))
    return occ


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _neighbors(x, y, w, h):
    out = []
    for dx, dy in DIRS.values():
        nx, ny = x + dx, y + dy
        if _in_bounds(nx, ny, w, h):
            out.append((nx, ny))
    return out


def _score(coor, health, occupied, w, h, depth):
    """Faithful reimplementation of the Rust `score` function.

    - coor into a snake body -> 0
    - health<=0 (dead) -> 0
    - current = PREFERRED_HEALTH - |health - PREFERRED_HEALTH|
    - depth 0 -> current
    - else current + (sum of neighbor scores) / 2
    """
    if coor in occupied:
        return 0
    if health <= 0:
        return 0

    current = PREFERRED_HEALTH - abs(health - PREFERRED_HEALTH)

    if depth == 0:
        return current

    # moving costs 1 health (food handled loosely; keeps recursion bounded)
    next_health = health - 1
    recursed = 0
    for nb in _neighbors(coor[0], coor[1], w, h):
        recursed += _score(nb, next_health, occupied, w, h, depth - 1)

    return current + recursed // 2


def move(game_state):
    try:
        board = game_state["board"]
        w = board["width"]
        h = board["height"]
        you = game_state["you"]
        head = you["head"]
        hx, hy = head["x"], head["y"]
        health = you.get("health", PREFERRED_HEALTH)

        occupied = _body_set(board, exclude_tails=True)

        # possible moves: in-bounds neighbors of the head
        candidates = []
        for mv, (dx, dy) in DIRS.items():
            nx, ny = hx + dx, hy + dy
            if _in_bounds(nx, ny, w, h):
                candidates.append((mv, (nx, ny)))

        if not candidates:
            return {"move": "up"}  # stuck_response

        best_mv = None
        best_score = None
        for mv, coor in candidates:
            s = _score(coor, health, occupied, w, h, RECURSION_LIMIT)
            if best_score is None or s > best_score:
                best_score = s
                best_mv = mv

        # If every real candidate scored 0 (all into bodies / death), still
        # prefer one that at least isn't an occupied cell if possible.
        if best_score == 0:
            for mv, coor in candidates:
                if coor not in occupied:
                    best_mv = mv
                    break

        return {"move": best_mv or "up"}
    except Exception:
        # robust fallback: any in-bounds, non-body move
        try:
            board = game_state["board"]
            w = board["width"]
            h = board["height"]
            you = game_state["you"]
            hx, hy = you["head"]["x"], you["head"]["y"]
            occupied = _body_set(board, exclude_tails=True)
            for mv, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h) and (nx, ny) not in occupied:
                    return {"move": mv}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
