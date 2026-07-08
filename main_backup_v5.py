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

    # Prefer moves that don't lose head-to-heads if any exist.
    safe = [c for c in candidates if not c["loses_h2h"]]
    pool = safe if safe else candidates

    # Survival: a move is "safe space" if we can reach our tail OR the reachable
    # space is at least our length (we won't box ourselves in immediately).
    # Require BOTH a decent tail loop or ample space to avoid coiling traps.
    def survivable(c):
        return c["tail_reachable"] or c["space"] >= my_len + 1

    surv = [c for c in pool if survivable(c)]
    pool2 = surv if surv else pool

    # Among survivable, prefer ones with the most space to keep options open.
    max_space = max(c["space"] for c in pool2)

    want_food = health < 65 or my_len < 5
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
        score += c["space"] * 3.0
        # Extra reward for having the most space (avoid corridors).
        if c["space"] == max_space:
            score += 8.0
        # Penalize tight spaces relative to our length (trap risk).
        if c["space"] < my_len + 2:
            score -= (my_len + 2 - c["space"]) * 6.0

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

        if food_set:
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

        if best is None or score > best_key:
            best = c
            best_key = score

    return best["name"] if best else pool2[0]["name"]


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
