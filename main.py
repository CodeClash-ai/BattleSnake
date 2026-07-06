import random

# Improved Battlesnake for 1v1 standard (11x11).
# Strategy:
#   - Enumerate legal moves (in-bounds, not into any snake body that will remain).
#   - Avoid losing head-to-head collisions vs equal/larger opponents.
#   - Score each candidate move by flood-fill reachable space (avoid trapping self)
#     plus food-seeking bias (stronger when health is low), plus aggression toward
#     smaller enemy heads for winning head-to-heads.
# Kept the v1 API (bottom-left origin, y-up). Robust fallbacks preserved.


def info():
    return {
        "apiversion": "1",
        "author": "moxuz",
        "color": "#ff69b4",
        "head": "safe",
        "tail": "round-bum",
    }


def start(game_state):
    return


def end(game_state):
    return


DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _neighbors(x, y):
    return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]


def _build_occupied(board, exclude_tails=True):
    """Return set of cells occupied by snake bodies.
    If exclude_tails, tail cells are excluded (they move away next turn),
    unless the snake just ate (tail duplicated -> body will not shrink)."""
    occ = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        # Detect if the snake just ate: last two body coords equal.
        just_ate = n >= 2 and body[-1] == body[-2]
        for i, seg in enumerate(body):
            if exclude_tails and i == n - 1 and not just_ate:
                continue
            occ.add((seg["x"], seg["y"]))
    return occ


def _flood_fill(start, occupied, w, h, limit=None):
    """Count reachable empty cells from start using BFS."""
    if start in occupied or not _in_bounds(start[0], start[1], w, h):
        return 0
    seen = {start}
    stack = [start]
    count = 0
    while stack:
        cx, cy = stack.pop()
        count += 1
        if limit is not None and count >= limit:
            return count
        for nx, ny in _neighbors(cx, cy):
            if (nx, ny) in seen:
                continue
            if not _in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in occupied:
                continue
            seen.add((nx, ny))
            stack.append((nx, ny))
    return count


def _safe_fallback(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]
    occ = _build_occupied(board, exclude_tails=True)
    for mv, (dx, dy) in DIRS.items():
        x, y = hx + dx, hy + dy
        if _in_bounds(x, y, w, h) and (x, y) not in occ:
            return {"move": mv}
    # any in-bounds
    for mv, (dx, dy) in DIRS.items():
        x, y = hx + dx, hy + dy
        if _in_bounds(x, y, w, h):
            return {"move": mv}
    return {"move": "up"}


def move(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        you = game_state["you"]
        head = you["body"][0]
        hx, hy = head["x"], head["y"]
        my_len = you["length"]
        health = you.get("health", 100)

        occ = _build_occupied(board, exclude_tails=True)

        # Opponent heads and their lengths (for head-to-head logic).
        enemy_heads = []
        for snake in board["snakes"]:
            if snake["id"] == you["id"]:
                continue
            eh = snake["body"][0]
            enemy_heads.append(((eh["x"], eh["y"]), snake["length"]))

        # Cells an equal/larger enemy could move into next turn (dangerous HTH).
        hth_danger = set()
        for (ex, ey), elen in enemy_heads:
            if elen >= my_len:
                for nx, ny in _neighbors(ex, ey):
                    hth_danger.add((nx, ny))
        # Cells where we could WIN a head-to-head (smaller enemy).
        hth_win = set()
        for (ex, ey), elen in enemy_heads:
            if elen < my_len:
                for nx, ny in _neighbors(ex, ey):
                    hth_win.add((nx, ny))

        food = [(f["x"], f["y"]) for f in board.get("food", [])]

        def nearest_food_dist(cell):
            if not food:
                return None
            return min(abs(cell[0] - fx) + abs(cell[1] - fy) for fx, fy in food)

        candidates = []
        for mv, (dx, dy) in DIRS.items():
            nx, ny = hx + dx, hy + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in occ:
                continue
            candidates.append((mv, (nx, ny)))

        if not candidates:
            return _safe_fallback(game_state)

        best_mv = None
        best_score = None
        for mv, cell in candidates:
            # Occupancy after we move: add our new head, remove our tail (it moves)
            # -- occ already excludes tails, so use it plus the new head cell for
            # opponents; for our own flood-fill we simulate.
            sim_occ = set(occ)
            sim_occ.add((hx, hy))  # our old head becomes body
            # our tail moves away already handled by exclude_tails
            sim_occ.discard(cell)  # we occupy this now; flood-fill starts here

            space = _flood_fill(cell, sim_occ, w, h, limit=my_len * 3 + 5)

            score = space * 10.0

            # Head-to-head handling
            if cell in hth_danger:
                score -= 1000.0
            if cell in hth_win:
                score += 60.0

            # Food seeking: stronger when hungry
            fd = nearest_food_dist(cell)
            if fd is not None:
                if health < 40:
                    score -= fd * 6.0
                elif health < 70:
                    score -= fd * 1.5
                else:
                    score -= fd * 0.4
                if cell in food:
                    score += 15.0 if health < 60 else 5.0

            # Slight preference to avoid edges/corners early (more room).
            edge_pen = 0
            if cell[0] == 0 or cell[0] == w - 1:
                edge_pen += 1
            if cell[1] == 0 or cell[1] == h - 1:
                edge_pen += 1
            score -= edge_pen * 1.0

            if best_score is None or score > best_score:
                best_score = score
                best_mv = mv

        if best_mv is not None:
            return {"move": best_mv}
        return _safe_fallback(game_state)
    except Exception:
        try:
            return _safe_fallback(game_state)
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
