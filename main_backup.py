"""
Smart Battlesnake bot for CodeClash.

Strategy:
  1. Enumerate legal moves (avoid walls, self body except tail-that-will-move, opponent bodies except their tail when they don't eat).
  2. Head-to-head prediction: for opponent adjacent food-adjacencies, avoid head-cells if opponent >= our length.
     Prefer head-cells if we are strictly longer (potential kill).
  3. Flood-fill from each candidate move; require enough space (>= our length or best available).
  4. Prefer moves that: keep large space, move toward nearest food when health low or shorter than opponent, and avoid getting boxed in.
  5. Head-to-head aggression when longer.

Coordinates: y-up. "up" = y+1, "down" = y-1, "left" = x-1, "right" = x+1.
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
        "author": "opus",
        "color": "#22cc88",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def _neighbors(p):
    x, y = p
    return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]


def _will_eat(snake, food_set):
    """Does this snake's next-turn head land on food this turn (i.e., we consider from current state)."""
    # We don't know their move; used generally when computing occupied for our own snake.
    return False


def _build_occupied(snakes, exclude_tail_ids=None):
    """Build set of blocked cells: all snake body segments.
    exclude_tail_ids: set of snake IDs for which the tail cell should NOT be blocked
    (because their tail will move on the next tick, provided they aren't eating).
    """
    occ = set()
    if exclude_tail_ids is None:
        exclude_tail_ids = set()
    for s in snakes:
        body = [(seg["x"], seg["y"]) for seg in s["body"]]
        if not body:
            continue
        # Tail may vacate unless the snake just ate (last two body segments identical)
        if s["id"] in exclude_tail_ids and len(body) >= 2 and body[-1] != body[-2]:
            for seg in body[:-1]:
                occ.add(seg)
        else:
            for seg in body:
                occ.add(seg)
    return occ


def _flood_fill(start_cell, blocked, w, h, limit=None):
    """BFS count of reachable cells from start_cell (start_cell must NOT be in blocked)."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    q = deque([start_cell])
    count = 1
    while q:
        if limit is not None and count >= limit:
            break
        cur = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or nb in blocked or not _in_bounds(nb, w, h):
                continue
            seen.add(nb)
            count += 1
            q.append(nb)
    return count


def _bfs_distance(src, targets, blocked, w, h):
    """Shortest path length from src to any of the target cells. Returns None if unreachable."""
    if not targets:
        return None
    tset = set(targets)
    if src in tset:
        return 0
    seen = {src}
    q = deque([(src, 0)])
    while q:
        cur, d = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or not _in_bounds(nb, w, h):
                continue
            if nb in blocked and nb not in tset:
                continue
            if nb in tset:
                return d + 1
            seen.add(nb)
            q.append((nb, d + 1))
    return None


def move(game_state):
    try:
        return _move(game_state)
    except Exception:
        return {"move": "up"}


def _move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    me = game_state["you"]
    my_id = me["id"]
    my_body = [(seg["x"], seg["y"]) for seg in me["body"]]
    my_head = my_body[0]
    my_len = me["length"]
    my_health = me["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    food_set = set(food)

    # All snake tails will vacate unless they ate last turn. Approx: allow all tails to move.
    all_ids = {s["id"] for s in snakes}
    occ_now = _build_occupied(snakes, exclude_tail_ids=all_ids)

    # Opponent heads for head-to-head prediction
    opp_snakes = [s for s in snakes if s["id"] != my_id]
    opp_head_moves = {}  # head -> set of possible next head cells
    for s in opp_snakes:
        oh = (s["head"]["x"], s["head"]["y"])
        obody = set((seg["x"], seg["y"]) for seg in s["body"][:-1])
        possible = []
        for d, (dx, dy) in DIRS.items():
            np = (oh[0] + dx, oh[1] + dy)
            if not _in_bounds(np, w, h):
                continue
            if np in obody:
                continue
            possible.append(np)
        opp_head_moves[s["id"]] = {
            "head": oh,
            "length": s["length"],
            "moves": possible,
        }

    # Danger cells: cells an opponent might move into that would kill us (opp length >= my_len)
    danger_h2h = set()
    kill_h2h = set()  # cells where we WIN a head-to-head (strictly longer)
    for oid, info_ in opp_head_moves.items():
        for m_cell in info_["moves"]:
            if info_["length"] >= my_len:
                danger_h2h.add(m_cell)
            if info_["length"] < my_len:
                kill_h2h.add(m_cell)

    # Evaluate each possible move
    candidates = []
    for d, (dx, dy) in DIRS.items():
        np = (my_head[0] + dx, my_head[1] + dy)
        if not _in_bounds(np, w, h):
            continue
        if np in occ_now:
            # Could still be OK if it's my own tail that will move and I'm not eating
            # occ_now already excludes tails that will move
            continue
        # Compute space from that cell
        blocked = set(occ_now)
        # Add my new head; remove my old tail if I don't eat here
        # We're moving TO np. If np is food, tail doesn't move (grows).
        my_new_body = [np] + my_body[:-1]
        if np in food_set:
            my_new_body = [np] + my_body  # grow
        # Rebuild blocked as post-move approximation:
        blocked_post = set()
        for s in snakes:
            if s["id"] == my_id:
                continue
            sb = [(seg["x"], seg["y"]) for seg in s["body"]]
            # Assume tail moves for opponent
            if len(sb) >= 2 and sb[-1] != sb[-2]:
                for seg in sb[:-1]:
                    blocked_post.add(seg)
            else:
                for seg in sb:
                    blocked_post.add(seg)
        for seg in my_new_body:
            blocked_post.add(seg)
        # For flood-fill, exclude np itself since our head occupies it (we count reachable AFTER we move).
        # Flood-fill from np treating np as free start.
        blocked_post.discard(np)
        space = _flood_fill(np, blocked_post, w, h, limit=my_len * 4 + 20)

        # Distance to nearest food from np (in the post-move blocked map)
        food_dist = _bfs_distance(np, food, blocked_post, w, h)

        # H2H flags
        is_h2h_death = np in danger_h2h
        is_h2h_kill = np in kill_h2h and np not in danger_h2h  # only sure if no larger opponent could go there too

        # Adjacent to opponent head (potential H2H)
        near_larger_head = False
        for oid, info_ in opp_head_moves.items():
            oh = info_["head"]
            if abs(np[0] - oh[0]) + abs(np[1] - oh[1]) == 1 and info_["length"] >= my_len:
                near_larger_head = True
                break

        candidates.append({
            "dir": d,
            "cell": np,
            "space": space,
            "food_dist": food_dist,
            "eats": np in food_set,
            "h2h_death": is_h2h_death,
            "h2h_kill": is_h2h_kill,
            "near_larger_head": near_larger_head,
        })

    if not candidates:
        return {"move": "up"}

    # Filter out lethal H2H if any alternative exists
    safe = [c for c in candidates if not c["h2h_death"]]
    if safe:
        candidates = safe

    # Require enough space; prefer moves with space >= my_len, else the one with max space
    good_space = [c for c in candidates if c["space"] >= my_len]
    if good_space:
        candidates = good_space
    else:
        # Choose max space
        max_space = max(c["space"] for c in candidates)
        candidates = [c for c in candidates if c["space"] == max_space]

    # Decide food urgency
    want_food = my_health < 60 or my_len < 5
    # Also want food if we're shorter than the longest opponent
    max_opp_len = max([s["length"] for s in opp_snakes], default=0)
    if my_len <= max_opp_len:
        want_food = True

    def score(c):
        s = 0.0
        s += c["space"] * 1.0
        if c["h2h_kill"]:
            s += 50
        if c["near_larger_head"]:
            s -= 30
        if want_food and c["food_dist"] is not None:
            # Closer food is better
            s += max(0, 40 - c["food_dist"] * 3)
            if c["eats"]:
                s += 15
        elif c["eats"] and my_health < 90:
            s += 5
        # Slight preference for not being on edge to keep options open
        cx, cy = c["cell"]
        if cx == 0 or cx == w - 1 or cy == 0 or cy == h - 1:
            s -= 2
        return s

    candidates.sort(key=score, reverse=True)
    return {"move": candidates[0]["dir"]}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
