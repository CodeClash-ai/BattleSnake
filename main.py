import random
from collections import deque

# Smart Battlesnake (v1 API, bottom-left origin / y-up).
# Strategy overview (documented for teammates):
#   1. Enumerate the 4 legal moves (in-bounds, not into a body segment that
#      will still be there next turn).
#   2. Score each candidate with a layered heuristic:
#        - Hard-avoid: walls, occupied cells, and losing head-to-head squares
#          (a cell an equal-or-longer enemy head can also reach next turn).
#        - Flood-fill reachable free space from the resulting head position
#          (avoid getting trapped in small pockets / dead ends).
#        - Food attraction scaled by hunger (grow to win head-to-heads).
#        - Prefer squares where we could win a head-to-head vs a shorter enemy.
#   3. Pick the highest scoring move; fall back to any legal move.


def info():
    return {
        "apiversion": "1",
        "author": "moxuz",
        "color": "#ffb6c1",
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


def _occupied_next_turn(board, exclude_tails=True):
    """Return a set of cells occupied by snake bodies next turn.

    Tails move away (so are free) *unless* the snake just ate (health==100,
    body has a duplicated tail) meaning the tail stays. We approximate by
    treating a tail as free only when the last two body segments differ.
    """
    occ = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if i == n - 1 and exclude_tails:
                # Tail vacates unless the snake ate (tail stacked on prev seg).
                if n >= 2:
                    prev = body[n - 2]
                    if (prev["x"], prev["y"]) == cell:
                        occ.add(cell)  # stacked tail -> stays
                    # else: tail moves away, treat as free
                continue
            occ.add(cell)
    return occ


def _all_body_cells(board):
    occ = set()
    for snake in board["snakes"]:
        for seg in snake["body"]:
            occ.add((seg["x"], seg["y"]))
    return occ


def _flood_fill(start, blocked, width, height, limit=None):
    """Count reachable free cells from start via BFS."""
    if start in blocked or not (0 <= start[0] < width and 0 <= start[1] < height):
        return 0
    seen = {start}
    q = deque([start])
    count = 0
    while q:
        x, y = q.popleft()
        count += 1
        if limit is not None and count >= limit:
            break
        for dx, dy in DIRS.values():
            nx, ny = x + dx, y + dy
            cell = (nx, ny)
            if (0 <= nx < width and 0 <= ny < height
                    and cell not in blocked and cell not in seen):
                seen.add(cell)
                q.append(cell)
    return count


def move(game_state):
    try:
        return _smart_move(game_state)
    except Exception:
        try:
            return _safe_fallback(game_state)
        except Exception:
            return {"move": "up"}


def _smart_move(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]

    head = you["body"][0]
    hx, hy = head["x"], head["y"]
    my_len = you["length"]
    health = you.get("health", 100)

    occ_next = _occupied_next_turn(board)
    all_bodies = _all_body_cells(board)

    # Enemy heads and their lengths (for head-to-head reasoning).
    enemies = []
    for s in board["snakes"]:
        if s["id"] == you["id"]:
            continue
        enemies.append((s["head"]["x"], s["head"]["y"], s["length"]))

    # Cells an enemy head could move into next turn.
    enemy_next = {}  # cell -> max enemy length that could go there
    for ex, ey, elen in enemies:
        for dx, dy in DIRS.values():
            cell = (ex + dx, ey + dy)
            if 0 <= cell[0] < width and 0 <= cell[1] < height:
                enemy_next[cell] = max(enemy_next.get(cell, 0), elen)

    food = set((f["x"], f["y"]) for f in board.get("food", []))

    def nearest_food_dist(cell):
        if not food:
            return None
        return min(abs(cell[0] - fx) + abs(cell[1] - fy) for fx, fy in food)

    candidates = []
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        cell = (nx, ny)
        # in bounds
        if not (0 <= nx < width and 0 <= ny < height):
            continue
        # not into a body cell that persists
        if cell in occ_next:
            continue
        candidates.append((mv, cell))

    if not candidates:
        return _safe_fallback(game_state)

    best = None
    best_score = None
    for mv, cell in candidates:
        score = 0.0

        # Head-to-head danger: cell reachable by an enemy head.
        if cell in enemy_next:
            other_len = enemy_next[cell]
            if other_len >= my_len:
                score -= 1000.0  # would lose or tie -> avoid strongly
            else:
                score += 60.0    # we would win a head-to-head -> good

        # Flood-fill free space after moving (avoid traps).
        blocked = set(occ_next)
        blocked.discard((hx, hy))
        # our new head occupies the cell
        blocked.add(cell)
        space = _flood_fill(cell, blocked, width, height, limit=my_len * 3 + 10)
        if space <= my_len:
            score -= 500.0  # not enough room, likely trap
        score += min(space, my_len * 3) * 4.0

        # Food seeking: stronger when hungry, mild otherwise (grow to win).
        d = nearest_food_dist(cell)
        if d is not None:
            if health < 35:
                score += (100.0 - d * 5.0)
            elif my_len < 8:
                score += (30.0 - d * 2.0)
            else:
                score += (10.0 - d * 1.0)
        if cell in food:
            if health < 50 or my_len < 6:
                score += 40.0

        # Slight preference to stay away from walls (more escape routes).
        edge_pen = 0
        if nx == 0 or nx == width - 1:
            edge_pen += 1
        if ny == 0 or ny == height - 1:
            edge_pen += 1
        score -= edge_pen * 2.0

        if best_score is None or score > best_score:
            best_score = score
            best = mv

    if best is not None:
        return {"move": best}
    return _safe_fallback(game_state)


def _safe_fallback(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    occ = _occupied_next_turn(board)
    # First: in-bounds and not into persistent body.
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in occ:
            return {"move": mv}
    # Any in-bounds move.
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < width and 0 <= ny < height:
            return {"move": mv}
    return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
