"""
CodeClash Battlesnake bot (opus-4-8).

Strategy: safe, greedy, space-aware.
  - Never move into a wall, our own body, or another snake's body (accounting
    for tails that will move away next turn).
  - Avoid losing head-to-head collisions (only take one if we are strictly
    longer; avoid ties unless forced).
  - Prefer moves that keep the most reachable open space (flood fill), so we
    don't trap ourselves.
  - Seek food when it is safe, prioritizing nearby food (and prioritizing it
    more strongly when health is low).
  - Try to dominate: when we are longer, we may aggressively cut off the
    opponent by aiming near squares it could move into.

The opponent (pambrose SimpleSnake) has NO collision avoidance and walks
straight lines toward the farthest food, so it self-eliminates often. We just
need to reliably survive and pick up wins.
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
        "author": "opus-4-8",
        "color": "#22aa66",
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


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": "up"}


def _choose_move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = (you["body"][0]["x"], you["body"][0]["y"])
    my_len = len(you["body"])
    my_health = you["health"]

    snakes = board["snakes"]

    # Build set of all occupied body cells. Tails will vacate next turn unless
    # the snake just ate (its body has a duplicated tail), so we treat a tail
    # as passable only when the snake is not about to grow.
    occupied = set()          # cells blocked next turn
    tail_cells = set()        # tails that will move (passable)
    opp_heads = []            # (pos, length) of other snakes' heads

    for s in snakes:
        body = s["body"]
        blen = len(body)
        sid = s["id"]
        for i, seg in enumerate(body):
            occupied.add((seg["x"], seg["y"]))
        # tail handling
        tail = (body[-1]["x"], body[-1]["y"])
        neck = (body[-2]["x"], body[-2]["y"]) if blen >= 2 else tail
        ate = (tail == neck)  # duplicated tail => grew/just spawned
        if not ate:
            tail_cells.add(tail)
        if sid != you["id"]:
            opp_heads.append(((body[0]["x"], body[0]["y"]), blen))

    # Predict opponent next-head cells (danger for head-to-head).
    # A cell adjacent to an opponent head is dangerous if that opponent is
    # equal or longer than us (we'd tie or lose).
    danger_h2h = set()
    for hpos, hlen in opp_heads:
        if hlen >= my_len:
            for dx, dy in DIRS.values():
                danger_h2h.add((hpos[0] + dx, hpos[1] + dy))

    def is_blocked(cell):
        if not _in_bounds(cell, w, h):
            return True
        if cell in occupied and cell not in tail_cells:
            return True
        return False

    # Flood fill available space from a cell, given a blocked set.
    def flood_space(start_cell, blocked):
        if start_cell in blocked or not _in_bounds(start_cell, w, h):
            return 0
        seen = {start_cell}
        stack = [start_cell]
        count = 0
        limit = w * h
        while stack and count < limit:
            cx, cy = stack.pop()
            count += 1
            for dx, dy in DIRS.values():
                nc = (cx + dx, cy + dy)
                if nc in seen:
                    continue
                if not _in_bounds(nc, w, h):
                    continue
                if nc in blocked:
                    continue
                seen.add(nc)
                stack.append(nc)
        return len(seen)

    # Candidate moves.
    candidates = []
    for mv, (dx, dy) in DIRS.items():
        cell = (head[0] + dx, head[1] + dy)
        if is_blocked(cell):
            continue
        candidates.append((mv, cell))

    if not candidates:
        # No "safe" move. Last-ditch: prefer a cell that a snake tail is
        # vacating (survivable) over a solid body cell; else any in-bounds
        # cell; else up. This maximizes our chance to survive one more turn.
        fallback = None
        for mv, (dx, dy) in DIRS.items():
            cell = (head[0] + dx, head[1] + dy)
            if not _in_bounds(cell, w, h):
                continue
            if cell in tail_cells:
                return mv  # tail will move away -> best chance
            if fallback is None:
                fallback = mv
        return fallback if fallback is not None else "up"

    # Static blocked set for flood fill (bodies minus vacating tails).
    blocked_base = (occupied - tail_cells)

    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    def nearest_food_dist(cell):
        if not food:
            return None
        return min(_manhattan(cell, f) for f in food)

    # Score each candidate.
    best = None
    best_score = None
    for mv, cell in candidates:
        # Space after moving into this cell.
        blocked = set(blocked_base)
        blocked.add(head)  # our new neck blocks
        space = flood_space(cell, blocked)

        score = 0.0
        # Space is paramount; if space < my length we risk getting trapped.
        score += space * 10.0
        # Strong extra penalty when the reachable space is smaller than our
        # body length: we could get boxed in and die.
        if space <= my_len:
            score -= (my_len - space + 1) * 60.0

        # Head-to-head danger: penalize heavily unless we can win.
        if cell in danger_h2h:
            score -= 1000.0

        # Head-to-head we can WIN: if an opponent shorter than us could move
        # into this cell, moving here could kill them. Reward moderately.
        for hpos, hlen in opp_heads:
            if _manhattan(cell, hpos) == 1 and hlen < my_len:
                score += 60.0

        # Aggression: when we are longer, prefer moving toward the opponent's
        # head to pressure it (helps set up cut-offs and H2H kills), but only
        # if we keep plenty of space.
        if opp_heads and space > my_len + 2:
            longest_gap = min(
                (_manhattan(cell, hp) for hp, hl in opp_heads if my_len > hl),
                default=None,
            )
            if longest_gap is not None:
                score += (8.0 - longest_gap * 0.6)

        # Food seeking. We want to be longer than the opponent (wins H2H) and
        # avoid starving, but not so long that we trap ourselves.
        fd = nearest_food_dist(cell)
        if fd is not None:
            max_opp = max((l for _, l in opp_heads), default=0)
            want_length = my_len <= max_opp  # be at least as long as rivals
            if my_health < 30:
                # Urgent: must eat.
                score += (120.0 - fd * 4.0)
            elif want_length or my_health < 55:
                score += (40.0 - fd * 2.0)
            else:
                # Comfortable and long enough; mild pull only.
                score += (10.0 - fd * 0.5)

        # Prefer staying away from walls a bit (more escape routes) as a mild
        # tiebreaker via number of open neighbors.
        open_nbrs = 0
        for ddx, ddy in DIRS.values():
            nc = (cell[0] + ddx, cell[1] + ddy)
            if _in_bounds(nc, w, h) and nc not in blocked_base:
                open_nbrs += 1
        score += open_nbrs * 1.5

        if best_score is None or score > best_score:
            best_score = score
            best = mv

    return best


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
