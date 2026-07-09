"""
CodeClash BattleSnake bot (v5).

Strategy (see README_agent.md):
  - Never move into walls, own body, or other snake bodies.
  - Correct tail handling (tail vacates unless the snake just ate).
  - Flood-fill each candidate move for reachable space AND a "survival" check:
    the reachable space must comfortably exceed our body length or we treat it
    as a trap. This prevents coiling ourselves into a dead pocket (the failure
    mode that lost round-2 games vs csauve__bookworm).
  - Tail-reachability as a strong secondary safety.
  - Head-to-head: avoid squares an equal/longer enemy head can reach; win them
    when strictly longer.
  - Aggression: when longer, pressure the enemy toward walls / losing H2H.
  - Seek food when it is safe and especially when health is low.
"""

from collections import deque

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
    x, y = p
    return ((x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y))


def _build_obstacles(board, exclude_tails=True):
    """Occupied cells. Tails excluded when the snake will move (didn't just eat)."""
    obstacles = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if exclude_tails and i == n - 1 and n >= 2:
                tail = body[-1]
                pre = body[-2]
                if (tail["x"], tail["y"]) != (pre["x"], pre["y"]):
                    continue
            obstacles.add(cell)
    return obstacles


def _flood_fill(start_cell, obstacles, w, h, limit=None):
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
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return count


def _timed_space(start_cell, board, you, w, h, food_set, limit=None):
    """Flood-fill that accounts for our OWN body vacating over time.

    We BFS from start_cell (the move destination). A cell occupied by our
    body segment `i` (0=head) frees up after `my_len - i` steps (the tail
    end vacates first). We can enter such a cell only if we reach it at a
    step >= the time it frees. Enemy bodies are treated as static obstacles
    (conservative). This detects shrinking-corridor self-traps that a plain
    flood-fill misses.
    """
    body = you["body"]
    my_len = len(body)
    # Map our body cell -> time it becomes free (steps from now).
    # Segment i (0=head) vacates at step (my_len - i) roughly, since tail
    # moves each turn. Eating extends body; ignore that (conservative).
    my_free = {}
    for i, seg in enumerate(body):
        c = (seg["x"], seg["y"])
        # earliest step this cell is free
        my_free[c] = my_len - i
    # Enemy bodies static (their tails vacate too but treat as blocked = safe).
    enemy_block = set()
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        for seg in snake["body"]:
            enemy_block.add((seg["x"], seg["y"]))

    from collections import deque as _dq
    # We arrive at start_cell at step 1.
    if not _in_bounds(start_cell, w, h):
        return 0
    if start_cell in enemy_block:
        return 0
    # start_cell might be our own tail freeing; check free time.
    sc_free = my_free.get(start_cell, 0)
    if sc_free > 1:
        return 0
    seen = {start_cell}
    q = _dq([(start_cell, 1)])
    count = 0
    while q:
        cur, t = q.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in enemy_block:
                continue
            nt = t + 1
            free = my_free.get(nb, 0)
            if free > nt:
                # cell still occupied by our body when we'd arrive
                continue
            seen.add(nb)
            q.append((nb, nt))
    return count



def _forced_trap(start_cell, board, you, w, h, food_set, steps=6):
    """Simulate our snake advancing `steps` turns from start_cell, greedily
    keeping the most open space each turn, with our own body vacating (tail
    moves) each step. Enemy bodies treated as static (conservative). Returns
    True if within `steps` turns we get FORCED into a dead end (no legal move)
    or into a space smaller than our body length -> a multi-step self-trap that
    one-step flood/timed_space cannot see.
    """
    body = you["body"]
    my_len = len(body)
    # our body as a list of (x,y), head first
    seg = [(s["x"], s["y"]) for s in body]
    # enemy static obstacles
    enemy = set()
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        for s in snake["body"]:
            enemy.add((s["x"], s["y"]))

    # Precompute the earliest step each cell can be reached by ANY enemy head
    # (BFS from all enemy heads over the enemy's current bodies as obstacles).
    # Used to block cells the enemy will contest as our simulation advances.
    enemy_reach = {}
    if enemy:
        eq = deque()
        my_head0 = start_cell
        for snake in board["snakes"]:
            if snake["id"] == you["id"]:
                continue
            # only consider enemies reasonably close (they can cut a corridor
            # even if shorter — the loss in game 96055754 was a shorter enemy).
            eh = snake["body"][0]
            hc = (eh["x"], eh["y"])
            if _manhattan(hc, my_head0) > 5:
                continue
            enemy_reach[hc] = 0
            eq.append((hc, 0))
        while eq:
            cc, dd = eq.popleft()
            if dd >= steps + 1:
                continue
            cxx, cyy = cc
            for nb2 in ((cxx, cyy + 1), (cxx, cyy - 1), (cxx - 1, cyy), (cxx + 1, cyy)):
                nxx, nyy = nb2
                if nxx < 0 or nxx >= w or nyy < 0 or nyy >= h:
                    continue
                if nb2 in enemy:
                    continue
                if nb2 in enemy_reach and enemy_reach[nb2] <= dd + 1:
                    continue
                enemy_reach[nb2] = dd + 1
                eq.append((nb2, dd + 1))

    ate = start_cell in food_set
    # advance body: new head = start_cell, drop tail unless we ate
    cur = [start_cell] + seg
    if not ate:
        cur.pop()
    for step in range(steps):
        head = cur[0]
        occ = set(cur[:-1])  # tail will vacate next move; body minus tail blocks
        occ |= enemy
        # Block cells an enemy head could already occupy by this step (they
        # move toward us and can cut off an escape corridor).
        arrive = step + 2  # our head arrives at a neighbor at this game-step
        for cell2, et in enemy_reach.items():
            if et <= arrive:
                occ.add(cell2)
        best_nb = None
        best_sp = -1
        legal = []
        hx, hy = head
        for nb in ((hx, hy + 1), (hx, hy - 1), (hx - 1, hy), (hx + 1, hy)):
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in occ:
                continue
            legal.append(nb)
            # measure open space from nb (obstacles = current body minus tail + enemy)
            sp = _flood_fill(nb, occ, w, h, limit=my_len + 4)
            if sp > best_sp:
                best_sp = sp
                best_nb = nb
        if not legal:
            return True  # forced dead end
        if best_sp < min(my_len, (w * h)):
            # not enough room to hold our body -> trap
            if best_sp < my_len:
                return True
        head = best_nb
        ate = head in food_set
        cur = [head] + cur
        if not ate:
            cur.pop()
    return False


def _reachable(start_cell, target, obstacles, w, h):
    if start_cell == target:
        return True
    if start_cell in obstacles or not _in_bounds(start_cell, w, h):
        return False
    seen = {start_cell}
    stack = [start_cell]
    while stack:
        cur = stack.pop()
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb == target:
                return True
            nx, ny = nb
            if nb in seen or nx < 0 or nx >= w or ny < 0 or ny >= h or nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return False


def _bfs_dist(start_cell, targets, obstacles, w, h):
    if not targets:
        return None
    if start_cell in targets:
        return 0
    seen = {start_cell}
    q = deque([(start_cell, 0)])
    while q:
        cur, d = q.popleft()
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
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
        best = None
        best_space = -1
        for name, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if _in_bounds(nxt, w, h) and nxt not in obstacles:
                sp = _flood_fill(nxt, obstacles, w, h, limit=w * h)
                if sp > best_space:
                    best_space = sp
                    best = name
        if best:
            return best
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

    # Other snakes' heads for head-to-head handling.
    enemies = []
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        eh = snake["body"][0]
        enemies.append({
            "head": (eh["x"], eh["y"]),
            "len": len(snake["body"]),
            "body": [(s["x"], s["y"]) for s in snake["body"]],
        })

    # Cells an enemy head could move into next turn -> max enemy length there.
    enemy_next = {}
    for e in enemies:
        for nb in _neighbors(e["head"]):
            if not _in_bounds(nb, w, h):
                continue
            enemy_next[nb] = max(enemy_next.get(nb, 0), e["len"])

    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    food_set = set(food)

    total_cells = w * h
    my_tail = (body[-1]["x"], body[-1]["y"])
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in obstacles:
            continue

        h2h_len = enemy_next.get(nxt, 0)
        loses_h2h = h2h_len >= my_len
        wins_h2h = h2h_len > 0 and h2h_len < my_len

        sim_obstacles = set(obstacles)
        eating_now = nxt in food_set
        if not eating_now:
            sim_obstacles.discard(my_tail)

        space = _flood_fill(nxt, sim_obstacles, w, h, limit=total_cells)
        tail_reachable = _reachable(nxt, my_tail, sim_obstacles, w, h)

        contested_obstacles = set(sim_obstacles)
        for ec in enemy_next:
            if ec != nxt:
                contested_obstacles.add(ec)
        contested_space = _flood_fill(nxt, contested_obstacles, w, h, limit=total_cells)

        # Time-aware space: simulate our body vacating as we advance. Detects
        # shrinking-corridor self-traps that plain flood-fill misses.
        timed_space = _timed_space(nxt, board, you, w, h, food_set, limit=total_cells)

        # Multi-step self-trap: greedily advance our body a few turns and see
        # if we get FORCED into a dead-end / collapsing coil that one-step
        # metrics miss (the exact loss mode in game 96055754: we were len 13 vs
        # opp 8 but walked into our own coil pocket).
        forced_trap = _forced_trap(nxt, board, you, w, h, food_set, steps=6)

        candidates.append({
            "name": name,
            "cell": nxt,
            "loses_h2h": loses_h2h,
            "wins_h2h": wins_h2h,
            "space": space,
            "contested_space": contested_space,
            "timed_space": timed_space,
            "forced_trap": forced_trap,
            "tail_reachable": tail_reachable,
        })

    if not candidates:
        return _safe_fallback(game_state)

    # Prefer moves that don't lose head-to-heads if any exist.
    safe = [c for c in candidates if not c["loses_h2h"]]
    pool = safe if safe else candidates

    # Survival: a move is "safe space" if we can reach our tail OR the reachable
    # space is at least our length (we won't box ourselves in immediately).
    # Require BOTH a decent tail loop or ample space to avoid coiling traps.
    def survivable(c):
        # Time-aware: the space we can actually occupy as our body advances
        # must hold our length. This is the real self-trap guard. Fall back
        # to tail-reachability + ample plain space for edge cases.
        if c["timed_space"] >= my_len:
            return True
        return c["tail_reachable"] and c["space"] >= my_len + 2

    surv = [c for c in pool if survivable(c)]
    pool2 = surv if surv else pool
    # Among survivable, strongly prefer moves that don't lead to a multi-step
    # forced self-trap (collapsing coil). Only filter if some non-trap remains.
    non_trap = [c for c in pool2 if not c["forced_trap"]]
    if non_trap:
        pool2 = non_trap

    # Among survivable, prefer ones with the most space to keep options open.
    max_space = max(c["space"] for c in pool2)
    max_timed = max(c["timed_space"] for c in pool2)

    # Length race: being longer wins head-to-heads and lets us trap the enemy.
    # Seek food unless we are already comfortably longer than the nearest enemy.
    _enemy_max_len = max((e["len"] for e in enemies), default=0)
    _length_lead = my_len - _enemy_max_len
    want_food = health < 75 or my_len < 7 or _length_lead < 3
    best = None
    best_key = None
    for c in pool2:
        sim_obstacles = set(obstacles)
        sim_obstacles.discard(my_tail)
        sim_obstacles.discard(c["cell"])
        if food_set:
            bd = _bfs_dist(c["cell"], food_set, sim_obstacles, w, h)
            fdist = bd if bd is not None else (_manhattan(c["cell"], food[0]) + 100)
        else:
            fdist = 0

        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        cdist = abs(c["cell"][0] - cx) + abs(c["cell"][1] - cy)

        score = 0.0
        # Space is the primary survival driver.
        score += c["space"] * 2.0
        # Time-aware space: strongly reward room that survives body advance.
        score += c["timed_space"] * 3.0
        # Reward space we still control even if the enemy pushes toward us.
        score += c["contested_space"] * 1.0
        # Extra reward for having the most space (avoid corridors).
        if c["space"] == max_space:
            score += 6.0
        if c["timed_space"] == max_timed:
            score += 10.0
        # Penalize tight spaces relative to our length (trap risk).
        if c["space"] < my_len + 2:
            score -= (my_len + 2 - c["space"]) * 5.0
        # STRONG penalty when time-aware space can't hold our body (self-trap).
        if c["timed_space"] < my_len:
            score -= (my_len - c["timed_space"]) * 12.0
        # STRONG penalty for a multi-step forced self-trap (collapsing coil that
        # one-step space metrics miss). Big enough to override food/space ties.
        if c["forced_trap"]:
            score -= 200.0

        # ANTI-SQUEEZE: avoid walking onto a wall/corner cell whose perpendicular
        # escape can be sealed by a nearby enemy. This is the exact failure mode
        # of every match loss (small snake chases edge food into a corner, enemy
        # walls off the exit). Count open, non-losing escape cells from `cell`
        # (excluding where we came from); if few AND an enemy head is close,
        # penalize. Scaled harder when we are small.
        cxn, cyn = c["cell"]
        on_edge = (cxn == 0 or cxn == w - 1 or cyn == 0 or cyn == h - 1)
        if on_edge and enemies:
            walls = (cxn == 0) + (cxn == w - 1) + (cyn == 0) + (cyn == h - 1)
            # open escape cells from this cell (not obstacles, in bounds)
            open_escapes = 0
            for nb in _neighbors(c["cell"]):
                if not _in_bounds(nb, w, h):
                    continue
                if nb == head:
                    continue
                if nb in obstacles and nb != my_tail:
                    continue
                # a cell an enemy of >= our len could take next turn is not a safe escape
                if enemy_next.get(nb, 0) >= my_len:
                    continue
                open_escapes += 1
            nearest_e = min(enemies, key=lambda e: _manhattan(c["cell"], e["head"]))
            edist_e = _manhattan(c["cell"], nearest_e["head"])
            # only worry when an enemy is close enough to seal us (within 4)
            if edist_e <= 4:
                proximity = (5 - edist_e)  # 1..4, bigger when closer
                if walls >= 2:  # corner cell
                    score -= proximity * 8.0
                    if my_len < 8:
                        score -= proximity * 4.0
                elif open_escapes <= 1:  # edge cell with <=1 safe escape
                    score -= proximity * 6.0
                    if my_len < 8:
                        score -= proximity * 3.0

        # WALL-PIN penalty: when moving ALONG a wall toward a nearby equal/longer
        # enemy that shares that wall-side, we risk being cut off & squeezed into
        # the corner (the exact loss mode vs nbw-crystal, game a2115842). Detect a
        # move parallel to a wall whose direction heads toward such an enemy.
        if on_edge and enemies:
            mdx = cxn - head[0]
            mdy = cyn - head[1]
            # moving parallel along a horizontal wall (top/bottom)?
            horiz_wall = (cyn == 0 or cyn == h - 1) and mdx != 0 and mdy == 0
            vert_wall = (cxn == 0 or cxn == w - 1) and mdy != 0 and mdx == 0
            for e in enemies:
                if e["len"] < my_len:
                    continue
                ex, ey = e["head"]
                ed = _manhattan(c["cell"], e["head"])
                if ed > 6:
                    continue
                if horiz_wall:
                    # enemy is in the direction we're moving AND near this wall
                    toward = (mdx > 0 and ex >= cxn) or (mdx < 0 and ex <= cxn)
                    near_wall = abs(ey - cyn) <= 3
                    if toward and near_wall:
                        score -= (7 - ed) * 2.0
                        if my_len < 10:
                            score -= (7 - ed) * 2.0
                elif vert_wall:
                    toward = (mdy > 0 and ey >= cyn) or (mdy < 0 and ey <= cyn)
                    near_wall = abs(ex - cxn) <= 3
                    if toward and near_wall:
                        score -= (7 - ed) * 2.0
                        if my_len < 10:
                            score -= (7 - ed) * 2.0

        if health >= 40:
            tail_bonus = 50.0
        elif health >= 20:
            tail_bonus = 15.0
        else:
            tail_bonus = 2.0
        if c["tail_reachable"]:
            score += tail_bonus

        if c["wins_h2h"]:
            score += 30.0

        # Aggression: when clearly longer, close on the enemy head to pressure
        # it toward walls / losing head-to-heads. Only when we have room.
        if enemies:
            nearest = min(enemies, key=lambda e: _manhattan(head, e["head"]))
            if my_len > nearest["len"] + 1 and health >= 35 and c["space"] >= my_len + 2:
                edist = _manhattan(c["cell"], nearest["head"])
                score -= edist * 2.0

        # TAIL-FOLLOW tie-breaker: for a very large, healthy snake, gently
        # prefer staying near our own tail so the body stays a compact,
        # unwind-able coil (mitigates long-game self-trap). Small weight so it
        # only breaks ties, never overriding space/survival decisions.
        if my_len >= 15 and health >= 50 and not want_food:
            tdist = _manhattan(c["cell"], my_tail)
            score -= tdist * 0.35

        if food_set:
            if health < 25:
                score -= fdist * 100.0
            elif health < 40:
                score -= fdist * 40.0
            elif health < 65:
                score -= fdist * 12.0
            elif _length_lead < 0:
                # We are SHORTER than the enemy: strongly race for food to catch up.
                score -= fdist * 14.0
            elif _length_lead < 1:
                # Roughly even length: still race hard so we don't get outgrown.
                score -= fdist * 10.0
            elif want_food:
                # Not comfortably longer (lead < 3) or moderate health: pursue food.
                score -= fdist * 7.0
            elif my_len < 12:
                score -= fdist * 2.0

        # Center pull: base weak pull, but stronger when we are short and
        # behind on length. Camping the perimeter keeps us safe but starves us
        # of the central food the enemy uses to outgrow us -> we lose H2H.
        cpull = 0.4
        if want_food and _length_lead < 2:
            cpull = 1.2
        score -= cdist * cpull
        if c["loses_h2h"]:
            score -= 100.0

        if best is None or score > best_key:
            best = c
            best_key = score

    return best["name"] if best else pool2[0]["name"]


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
