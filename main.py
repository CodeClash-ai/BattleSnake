"""
Smart Battlesnake for CodeClash v1 (standard 11x11, y-up coords).

Strategy overview (see README_agent.md for details):
  - Full collision avoidance: walls, self-body, opponent bodies.
  - Flood-fill space evaluation to avoid trapping ourselves.
  - Head-to-head handling: avoid squares an equal/longer enemy head could
    reach; actively contest squares where we're longer (can win H2H).
  - Food seeking weighted by health & distance, but never at the cost of space.
  - Tail-chasing safety: a snake's tail square is safe to enter next turn
    (unless it just ate), so we treat tails as passable when appropriate.

Opponent in this matchup (pambrose SimpleSnake) has NO collision avoidance
and targets the FARTHEST food, so it suicides quickly. We just need to stay
alive longer andavoid head-to-head losses.
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
    """Count reachable empty cells from start_cell (BFS)."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    stack = [start_cell]
    count = 0
    if limit is None:
        limit = w * h
    while stack and count < limit:
        cur = stack.pop()
        count += 1
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


def _open_neighbors(cell, blocked, w, h):
    """Number of passable neighbor cells (open escape routes)."""
    n = 0
    for nb in _neighbors(cell):
        if _in_bounds(nb, w, h) and nb not in blocked:
            n += 1
    return n


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": "up"}


def _choose_move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    me = game_state["you"]
    head = (me["head"]["x"], me["head"]["y"])
    my_len = me["length"]
    my_health = me["health"]

    snakes = board["snakes"]

    # Build occupied set. A snake's tail will move away next turn unless it
    # ate (health==100 after eating -> body has duplicate tail). We treat the
    # last body segment as free when the snake didn't just eat.
    occupied = set()
    for s in snakes:
        body = [(b["x"], b["y"]) for b in s["body"]]
        # If the last two segments coincide, the snake grew/just spawned:
        # tail won't vacate, so keep it. Otherwise, tail vacates.
        n = len(body)
        for i, seg in enumerate(body):
            if i == n - 1:
                # tail: skip (passable) unless it overlaps the pre-tail
                # (meaning it isn't moving away this turn)
                if n >= 2 and body[-1] == body[-2]:
                    occupied.add(seg)
                # else: leave passable
            else:
                occupied.add(seg)

    # Enemy heads and their possible next moves (for head-to-head avoidance).
    enemy_heads = []
    for s in snakes:
        if s["id"] == me["id"]:
            continue
        eh = (s["head"]["x"], s["head"]["y"])
        enemy_heads.append((eh, s["length"]))

    # Danger squares: cells an equal-or-longer enemy head could move into.
    # Cells where a shorter enemy could move are "attack" opportunities.
    h2h_lose = set()
    h2h_win = set()
    for eh, elen in enemy_heads:
        for nb in _neighbors(eh):
            if not _in_bounds(nb, w, h):
                continue
            if elen >= my_len:
                h2h_lose.add(nb)
            else:
                h2h_win.add(nb)

    # Our own tail cell (target for tail-chasing survival).
    my_body = [(b["x"], b["y"]) for b in me["body"]]
    my_tail = my_body[-1] if my_body else None
    # If we just ate (tail duplicated), tail won't vacate; treat as blocked.
    if len(my_body) >= 2 and my_body[-1] == my_body[-2]:
        my_tail = None

    # Candidate moves ranked.
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in occupied:
            continue
        # Space available after moving there.
        blocked = set(occupied)
        blocked.add(nxt)
        space = _flood_fill(nxt, blocked, w, h)

        # Open escape routes from the new head cell (dead-end detection).
        openn = _open_neighbors(nxt, blocked, w, h)

        # Can we still reach our own tail after this move? If so we can keep
        # chasing it indefinitely (strong survival signal).
        tail_reachable = False
        if my_tail is not None and my_tail not in blocked:
            # BFS from nxt looking for tail
            seen = {nxt}
            stack = [nxt]
            while stack:
                cur = stack.pop()
                if cur == my_tail:
                    tail_reachable = True
                    break
                for nb in _neighbors(cur):
                    if nb in seen or not _in_bounds(nb, w, h) or nb in blocked:
                        continue
                    seen.add(nb)
                    stack.append(nb)

        # Head-to-head risk classification.
        risky = nxt in h2h_lose
        winnable = nxt in h2h_win

        candidates.append({
            "name": name,
            "pos": nxt,
            "space": space,
            "openn": openn,
            "tail_reachable": tail_reachable,
            "risky": risky,
            "winnable": winnable,
        })

    if not candidates:
        return "up"

    # Food targeting (nearest food).
    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    nearest_food = None
    if food:
        nearest_food = min(food, key=lambda f: _manhattan(head, f))

    # We need enough space to fit our body; treat space < my_len as trap-ish.
    def score(c):
        s = 0.0
        # Massive penalty for definite head-to-head loss.
        if c["risky"]:
            s -= 1000.0
        # Bonus for winnable head-to-head (eat smaller opponent).
        if c["winnable"]:
            s += 500.0
        # Space is critical: prefer more room. Heavily penalize traps.
        if c["space"] < my_len:
            s -= (my_len - c["space"]) * 60.0
        s += c["space"] * 4.0
        # Dead-end avoidance: cells with only one open neighbor are risky.
        if c["openn"] <= 1:
            s -= 40.0
        # Strong bonus if we can still reach our own tail (guaranteed loop).
        if c["tail_reachable"]:
            s += 30.0
        # Food attraction, stronger when hungry. Keep weak when healthy so we
        # stay short & nimble (avoids self-trapping from overgrowth).
        if nearest_food is not None:
            d = _manhattan(c["pos"], nearest_food)
            if my_health < 25:
                hunger = 12.0
            elif my_health < 50:
                hunger = 5.0
            else:
                hunger = 0.4
            s += (w + h - d) * hunger
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[0]["name"]


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
