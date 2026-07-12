"""
CodeClash Battlesnake bot (opus-4-8).

Strategy (much stronger than the naive SimpleSnake port):
  - Enumerate legal moves (in bounds, not into any snake body that will persist).
  - Model tails: a tail cell vacates next turn unless that snake just ate.
  - Avoid head-to-head losses: don't step onto a cell an equal/longer enemy
    head could also move to (unless we have no other choice).
  - Prefer head-to-head *wins* against strictly shorter enemies.
  - Score each candidate move by flood-fill reachable space (survival),
    plus a food/health incentive, and closeness to enemy when we are longer.
  - Robust legal fallback so we never crash / return illegal.

Coordinate system (BattleSnake v1 API, y-up, bottom-left origin):
    up = y+1, down = y-1, left = x-1, right = x+1
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
        "color": "#22cc88",
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
    x, y = p
    return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]


def _flood_fill(start_cell, blocked, w, h, limit=None):
    """Count reachable free cells from start_cell (BFS), bounded by limit."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
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
            if nb in blocked:
                continue
            seen.add(nb)
            stack.append(nb)
    return count


def _reachable_with_tails(start_cell, static_blocked, snakes_bodies, w, h, limit=None):
    """BFS where a body cell frees up once the tail has retreated past it.

    static_blocked: cells that never free (e.g. permanent). We instead compute
    per-cell free-time from snake bodies: body cell at index i (0=head) of a
    snake of length L vacates after (L - i) steps (tail=index L-1 vacates at
    step 1, unless the snake just grew). We do a BFS carrying the step count;
    a cell is enterable at step t if it's empty OR its vacate_time <= t.
    """
    # Build vacate-time map: cell -> earliest step it becomes free.
    vacate = {}
    for body, grew in snakes_bodies:
        L = len(body)
        for i, cell in enumerate(body):
            # steps until this cell is vacated by tail retreat
            # tail (i=L-1) vacates after 1 step normally; if grew, +1 delay
            t = (L - i) + (1 if grew else 0)
            # keep the max requirement if overlap
            if cell not in vacate or vacate[cell] > t:
                vacate[cell] = t
    from collections import deque
    dq = deque()
    dq.append((start_cell, 1))
    seen = {start_cell}
    count = 0
    while dq:
        cur, step = dq.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        for nb in _neighbors(cur):
            if nb in seen:
                continue
            if not _in_bounds(nb, w, h):
                continue
            if nb in static_blocked:
                continue
            vt = vacate.get(nb)
            if vt is not None and vt > step + 1:
                # still occupied when we'd arrive
                continue
            seen.add(nb)
            dq.append((nb, step + 1))
    return count


def _can_reach(start_cell, target, static_blocked, snakes_bodies, w, h):
    """Time-aware BFS: can we reach `target` cell from start_cell, treating
    body cells as vacating once their tail retreats past them? Returns bool.
    This is the anti-self-trap signal: if we can still reach our own tail,
    we can keep chasing it and won't box ourselves in."""
    if start_cell == target:
        return True
    vacate = {}
    for body, grew in snakes_bodies:
        L = len(body)
        for i, cell in enumerate(body):
            t = (L - i) + (1 if grew else 0)
            if cell not in vacate or vacate[cell] > t:
                vacate[cell] = t
    from collections import deque
    dq = deque([(start_cell, 1)])
    seen = {start_cell}
    while dq:
        cur, step = dq.popleft()
        for nb in _neighbors(cur):
            if nb == target:
                return True
            if nb in seen or not _in_bounds(nb, w, h):
                continue
            if nb in static_blocked:
                continue
            vt = vacate.get(nb)
            if vt is not None and vt > step + 1:
                continue
            seen.add(nb)
            dq.append((nb, step + 1))
    return False


def _future_safe_moves(cell, blocked, w, h):
    """Count in-bounds, non-blocked neighbors of `cell` (escape options)."""
    n = 0
    for nb in _neighbors(cell):
        if _in_bounds(nb, w, h) and nb not in blocked:
            n += 1
    return n


def move(game_state):
    try:
        return _decide(game_state)
    except Exception:
        return {"move": "up"}


def _decide(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_body = [(s["x"], s["y"]) for s in you["body"]]
    head = my_body[0]
    my_len = you["length"]
    my_health = you["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    # Determine which snakes just ate (tail duplicated => will grow, tail stays).
    # Build set of occupied body cells; tail cells vacate next turn unless grown.
    occupied = set()  # cells blocked next turn (bodies minus vacating tails)
    all_bodies = {}   # snake id -> list of cells
    enemy_heads = []  # (head_cell, length) for enemies
    snakes_bodies = []  # (body_cells_list, grew_bool) for time-aware fill

    for sn in snakes:
        body = [(s["x"], s["y"]) for s in sn["body"]]
        all_bodies[sn["id"]] = body
        # Tail vacates unless the last two cells coincide (just ate / start).
        grew = len(body) >= 2 and body[-1] == body[-2]
        # Add all cells except tail (if it will move away).
        for i, cell in enumerate(body):
            if i == len(body) - 1 and not grew:
                continue  # tail will move away
            occupied.add(cell)
        snakes_bodies.append((body, grew))
        if sn["id"] != you["id"]:
            enemy_heads.append((body[0], sn["length"]))

    # Cells an enemy head could move into next turn (for head-to-head).
    # Map cell -> max enemy length that could reach it.
    enemy_next = {}
    for eh, elen in enemy_heads:
        for nb in _neighbors(eh):
            if not _in_bounds(nb, w, h):
                continue
            enemy_next[nb] = max(enemy_next.get(nb, 0), elen)

    candidates = []
    for mv, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in occupied:
            continue
        # Head-to-head: losing (enemy >= our length) is deadly.
        h2h_len = enemy_next.get(nxt, 0)
        h2h_loss = h2h_len >= my_len
        h2h_win = 0 < h2h_len < my_len  # we'd win if they go there
        candidates.append((mv, nxt, h2h_loss, h2h_win))

    if not candidates:
        # No non-colliding legal move; pick the least-bad in-bounds move.
        # Rank: prefer cells not hit by an equal/longer enemy head, then more
        # flood-fill space (a vacating tail we may survive on), then off-wall.
        best_fb = None
        best_fb_score = None
        for mv, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(nxt, w, h):
                continue
            sc = 0.0
            if enemy_next.get(nxt, 0) >= my_len:
                sc -= 100.0  # likely head-to-head loss
            # Space if we treat all bodies as blocked (conservative).
            sc += _flood_fill(nxt, occupied | {nxt}, w, h, limit=w * h) * 5.0
            if best_fb_score is None or sc > best_fb_score:
                best_fb_score = sc
                best_fb = mv
        return {"move": best_fb or "up"}

    # Prefer moves without head-to-head loss if any exist.
    safe = [c for c in candidates if not c[2]]
    pool = safe if safe else candidates

    # Health-driven food desire.
    want_food = my_health < 40 or my_len < 4
    nearest_food_dist = None
    nearest_food = None
    for f in food:
        d = _manhattan(head, f)
        if nearest_food_dist is None or d < nearest_food_dist:
            nearest_food_dist = d
            nearest_food = f

    best_move = None
    best_score = None
    total_free = w * h
    my_tail = my_body[-1]

    for mv, nxt, h2h_loss, h2h_win in pool:
        # Simulate our body after moving: add new head, drop tail (approx).
        new_blocked = set(occupied)
        new_blocked.add(nxt)
        # Static flood fill (conservative) counts reachable free area now.
        space = _flood_fill(nxt, new_blocked, w, h, limit=total_free)
        # Time-aware reachable area: accounts for tails retreating so we don't
        # over-penalize following our own (or the enemy's) tail. Use the larger
        # of the two so long snakes recognize corridors they can survive.
        static_bl = {nxt}
        space_t = _reachable_with_tails(nxt, static_bl, snakes_bodies, w, h,
                                        limit=total_free)
        space = max(space, space_t)

        # Tail-access check: after this move, can we still reach our own tail's
        # region? If yes we are almost never trapped (we can chase our tail).
        # Use the time-aware fill's reachable set to test tail reachability.
        tail_reach = _can_reach(nxt, my_tail, new_blocked, snakes_bodies, w, h)

        # 1-ply lookahead: how many escape options remain after this move.
        escapes = _future_safe_moves(nxt, new_blocked, w, h)

        # 2-ply space lookahead: after moving to nxt, find the best space we
        # could reach on the FOLLOWING move. If every follow-up is cramped,
        # this move is leading us into a trap even if `space` looks okay now.
        best_next_space = 0
        for nb in _neighbors(nxt):
            if not _in_bounds(nb, w, h):
                continue
            if nb in new_blocked:
                continue
            ns = _reachable_with_tails(nb, {nxt, nb}, snakes_bodies, w, h,
                                       limit=total_free)
            if ns > best_next_space:
                best_next_space = ns

        score = 0.0
        # Space is king: staying alive requires room.
        score += space * 10.0
        # Strong bonus for keeping access to our own tail (anti-coil / anti-trap).
        # If we can chase our tail we can almost always survive indefinitely.
        if tail_reach:
            score += 120.0
        else:
            score -= 200.0
        # Reward keeping a large follow-up region (trap avoidance, 2-ply).
        score += best_next_space * 4.0
        if best_next_space < my_len:
            score -= (my_len - best_next_space) * 20.0

        # Avoid moving into a cell with no follow-up (guaranteed death next turn).
        if escapes == 0:
            score -= 500.0
        elif escapes == 1:
            score -= 40.0

        # Strongly avoid tight spaces relative to our length.
        if space < my_len:
            score -= (my_len - space) * 50.0

        # Head-to-head win bonus (eliminate shorter enemy).
        if h2h_win:
            score += 200.0
        if h2h_loss:
            score -= 1000.0

        # Food incentive.
        if nearest_food is not None:
            d_after = _manhattan(nxt, nearest_food)
            if want_food:
                score -= d_after * 8.0
            else:
                score -= d_after * 1.0
            if nxt == nearest_food and want_food:
                score += 60.0

        # Slight preference to stay away from walls (more mobility) when safe.
        edge_pen = 0
        if nxt[0] == 0 or nxt[0] == w - 1:
            edge_pen += 1
        if nxt[1] == 0 or nxt[1] == h - 1:
            edge_pen += 1
        score -= edge_pen * 2.0

        if best_score is None or score > best_score:
            best_score = score
            best_move = mv

    return {"move": best_move or pool[0][0]}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
