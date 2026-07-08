"""
CodeClash BattleSnake bot.

Strategy (see README_agent.md for details):
  - Never move into walls, own body, or other snake bodies.
  - Treat snake tails correctly (tail vacates unless the snake just ate).
  - Flood-fill each candidate move to avoid trapping ourselves in small pockets.
  - Head-to-head awareness: avoid squares an equal/longer enemy head could also
    reach; actively try to win head-to-heads when we are strictly longer.
  - Seek food when it is safe and especially when health is low; otherwise
    prefer central, high-mobility squares.
"""

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "me",
        "color": "#00ccff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _in_bounds(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def _neighbors(p):
    return [(p[0] + dx, p[1] + dy) for dx, dy in DIRS.values()]


def _build_obstacles(board, exclude_tails=True):
    """Return set of occupied cells. Tails are excluded when the snake will
    move (i.e. did not just eat -> tail moves away next turn)."""
    obstacles = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            # The tail (last segment) usually vacates next turn. But if the
            # snake just ate (health==100 and body has duplicated tail) the
            # tail stays. We approximate: exclude the tail unless the last two
            # segments coincide (freshly grown / just ate).
            if exclude_tails and i == n - 1 and n >= 2:
                tail = body[-1]
                pre = body[-2]
                if (tail["x"], tail["y"]) != (pre["x"], pre["y"]):
                    continue
            obstacles.add(cell)
    return obstacles


def _flood_fill(start_cell, obstacles, w, h, limit=None):
    """Count reachable free cells from start_cell (BFS)."""
    if start_cell in obstacles or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    stack = [start_cell]
    count = 0
    while stack:
        cur = stack.pop()
        count += 1
        if limit is not None and count >= limit:
            return count
        for nb in _neighbors(cur):
            if nb in seen:
                continue
            if not _in_bounds(nb, w, h):
                continue
            if nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return count


def _reachable(start_cell, target, obstacles, w, h):
    """BFS: is target reachable from start_cell through free cells?"""
    if start_cell == target:
        return True
    if start_cell in obstacles or not _in_bounds(start_cell, w, h):
        return False
    seen = {start_cell}
    stack = [start_cell]
    while stack:
        cur = stack.pop()
        for nb in _neighbors(cur):
            if nb == target:
                return True
            if nb in seen or not _in_bounds(nb, w, h) or nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return False


def _bfs_dist(start_cell, targets, obstacles, w, h):
    """BFS shortest path distance from start_cell to nearest of targets
    (a set), through free cells. Returns None if unreachable."""
    if not targets:
        return None
    if start_cell in targets:
        return 0
    from collections import deque
    seen = {start_cell}
    q = deque([(start_cell, 0)])
    while q:
        cur, d = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or not _in_bounds(nb, w, h):
                continue
            if nb in targets:
                return d + 1
            if nb in obstacles:
                continue
            seen.add(nb)
            q.append((nb, d + 1))
    return None


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": _safe_fallback(game_state)}


def _safe_fallback(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head_seg = game_state["you"]["body"][0]
        head = (head_seg["x"], head_seg["y"])
        obstacles = _build_obstacles(board)
        for name, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if _in_bounds(nxt, w, h) and nxt not in obstacles:
                return name
    except Exception:
        pass
    return "up"


def _choose_move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    body = you["body"]
    head = (body[0]["x"], body[0]["y"])
    my_len = len(body)
    health = you["health"]

    obstacles = _build_obstacles(board)

    # Info about other snakes' heads for head-to-head handling.
    enemies = []
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        eh = snake["body"][0]
        enemies.append({
            "head": (eh["x"], eh["y"]),
            "len": len(snake["body"]),
        })

    # Cells an enemy head could move into next turn.
    enemy_next = {}  # cell -> max enemy length that can reach it
    for e in enemies:
        for nb in _neighbors(e["head"]):
            if not _in_bounds(nb, w, h):
                continue
            enemy_next[nb] = max(enemy_next.get(nb, 0), e["len"])

    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    total_cells = w * h
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in obstacles:
            continue

        # Head-to-head risk assessment.
        h2h_len = enemy_next.get(nxt, 0)
        # If an enemy of equal or greater length can also step here, it's
        # dangerous (we'd tie or lose). Mark it but don't always forbid.
        loses_h2h = h2h_len >= my_len
        wins_h2h = h2h_len > 0 and h2h_len < my_len

        # Simulate the board one step ahead: our head advances to nxt and our
        # tail vacates (unless we're about to eat, but ignore that nuance for
        # the space estimate -- being slightly conservative is fine).
        my_tail = (body[-1]["x"], body[-1]["y"])
        sim_obstacles = set(obstacles)
        sim_obstacles.discard(my_tail)   # our tail moves away
        # NOTE: do NOT add nxt to obstacles; flood-fill starts FROM nxt and
        # would otherwise immediately return 0. nxt occupancy is implicit.

        space = _flood_fill(nxt, sim_obstacles, w, h, limit=total_cells)

        # Tail-reachability: if we can still reach our own tail after moving,
        # we are almost never trapped (we can chase our tail indefinitely).
        tail_reachable = _reachable(nxt, my_tail, sim_obstacles, w, h)

        candidates.append({
            "name": name,
            "cell": nxt,
            "loses_h2h": loses_h2h,
            "wins_h2h": wins_h2h,
            "space": space,
            "tail_reachable": tail_reachable,
        })

    if not candidates:
        return _safe_fallback(game_state)

    # Prefer moves that don't lose head-to-heads if any such moves exist.
    safe = [c for c in candidates if not c["loses_h2h"]]
    pool = safe if safe else candidates

    # Strongly prefer moves where we can still reach our own tail (safe loop),
    # then moves with enough space to hold our whole body.
    tail_ok = [c for c in pool if c["tail_reachable"]]
    pool2 = tail_ok if tail_ok else pool
    ample = [c for c in pool2 if c["space"] >= my_len]
    working = ample if ample else pool2

    # Decide whether to chase food.
    want_food = health < 65 or my_len < 5
    food_set = set(food)
    my_tail = (body[-1]["x"], body[-1]["y"])
    best = None
    best_key = None
    for c in working:
        # Obstacle-aware BFS distance to nearest food from this cell. This is
        # crucial vs manhattan: food behind our own body is not "close".
        sim_obstacles = set(obstacles)
        sim_obstacles.discard(my_tail)
        sim_obstacles.discard(c["cell"])
        if food_set:
            bd = _bfs_dist(c["cell"], food_set, sim_obstacles, w, h)
            fdist = bd if bd is not None else (_manhattan(c["cell"], food[0]) + 100)
        else:
            fdist = 0

        # Center attraction (tie-breaker for control).
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        cdist = abs(c["cell"][0] - cx) + abs(c["cell"][1] - cy)

        # Scoring: prioritize space & not-trapping, then food/h2h, then center.
        score = 0.0
        score += c["space"] * 3.0
        # Tail-following bonus keeps us safe, but must not override the need to
        # eat when starving (otherwise we loop in a corner and die).
        if health >= 40:
            tail_bonus = 50.0
        elif health >= 20:
            tail_bonus = 15.0
        else:
            tail_bonus = 2.0
        if c["tail_reachable"]:
            score += tail_bonus
        if c["wins_h2h"]:
            score += 25.0
        if food_set:
            # Urgency ramps up sharply as health drops. When starving, food
            # must dominate the space heuristic to survive. Using BFS distance
            # guarantees we actually move toward reachable food.
            if health < 25:
                score -= fdist * 100.0
            elif health < 40:
                score -= fdist * 40.0
            elif health < 65:
                score -= fdist * 12.0
            elif want_food:
                score -= fdist * 5.0
            elif my_len < 12:
                score -= fdist * 1.0
        score -= cdist * 0.4
        if c["loses_h2h"]:
            score -= 100.0

        key = score
        if best is None or key > best_key:
            best = c
            best_key = key

    return best["name"] if best else working[0]["name"]


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
