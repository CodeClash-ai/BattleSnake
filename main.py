"""
Strong Battlesnake bot for CodeClash (standard 11x11, 1v1).

Strategy overview:
  - Enumerate the 4 possible moves.
  - Filter out immediately-lethal moves (walls, self, opponent bodies).
  - For each surviving candidate, simulate the resulting board state and score
    it using:
      * flood-fill of reachable free space (avoid getting trapped)
      * head-to-head safety (only contest a H2H if we're strictly longer)
      * food proximity / health management
  - Pick the highest-scoring move.

Coordinate system: BattleSnake v1 API, y-up, bottom-left origin.
  up = y+1, down = y-1, left = x-1, right = x+1.
"""

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "opus-4-8",
        "color": "#2266ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _neighbors(pos, w, h):
    x, y = pos
    for dx, dy in MOVES.values():
        nx, ny = x + dx, y + dy
        if _in_bounds(nx, ny, w, h):
            yield (nx, ny)


def _flood_fill(start_pos, blocked, w, h, limit=None):
    """Count reachable free cells from start_pos (start not counted as blocked)."""
    if start_pos in blocked or not _in_bounds(start_pos[0], start_pos[1], w, h):
        return 0
    seen = {start_pos}
    stack = [start_pos]
    count = 0
    while stack:
        cur = stack.pop()
        count += 1
        if limit is not None and count >= limit:
            break
        for nb in _neighbors(cur, w, h):
            if nb not in seen and nb not in blocked:
                seen.add(nb)
                stack.append(nb)
    return count


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": "up"}


def _choose_move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = (you["head"]["x"], you["head"]["y"])
    my_len = you["length"]
    my_health = you["health"]

    snakes = board["snakes"]

    # Set of all body cells currently occupied. A tail moves away next turn
    # (unless the snake just ate), but treating tails as blocked is safest and
    # only mildly conservative. We keep tails blocked unless the snake is at
    # full health-ish / just grew; simplest robust approach: block all bodies
    # except tails that will move.
    occupied = set()
    tails = set()
    opp_heads = []  # (pos, length) of opponents
    for s in snakes:
        body = [(p["x"], p["y"]) for p in s["body"]]
        for i, seg in enumerate(body):
            occupied.add(seg)
        # tail will vacate next turn unless the snake just ate (health==100 &
        # length grew). Approximate: tail vacates unless health == 100.
        if len(body) >= 2 and s["health"] != 100:
            tails.add(body[-1])
        if s["id"] != you["id"]:
            opp_heads.append((body[0], s["length"]))

    # Cells opponents could move into (their next head positions) — dangerous
    # for head-to-head. Map each such cell to the max opponent length that
    # threatens it.
    opp_next = {}
    for (ohead, olen) in opp_heads:
        for nb in _neighbors(ohead, w, h):
            opp_next[nb] = max(opp_next.get(nb, 0), olen)

    # Candidate moves
    candidates = []
    for mv, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        npos = (nx, ny)
        if not _in_bounds(nx, ny, w, h):
            continue
        # blocked if occupied and not a vacating tail
        if npos in occupied and npos not in tails:
            continue
        candidates.append((mv, npos))

    if not candidates:
        # No safe move; try any in-bounds move (least bad)
        for mv, (dx, dy) in MOVES.items():
            nx, ny = head[0] + dx, head[1] + dy
            if _in_bounds(nx, ny, w, h):
                return mv
        return "up"

    # Nearest food target (Manhattan)
    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    best_mv = candidates[0][0]
    best_score = float("-inf")

    for mv, npos in candidates:
        score = 0.0

        # Build blocked set for flood-fill from the new head position.
        # After we move: our head goes to npos, our tail vacates (unless we eat).
        blocked = set(occupied)
        # our tail moves away
        my_body = [(p["x"], p["y"]) for p in you["body"]]
        if len(my_body) >= 2 and npos not in food:
            blocked.discard(my_body[-1])
        # remaining opponent tails vacate
        for t in tails:
            blocked.discard(t)
        # the new head cell is now occupied
        blocked.add(npos)

        space = _flood_fill(npos, blocked, w, h)

        # Space is the dominant factor: getting trapped = death.
        score += space * 10.0

        # Strongly prefer having at least as much room as our body length.
        if space < my_len:
            score -= (my_len - space) * 20.0

        # Head-to-head handling
        if npos in opp_next:
            threat_len = opp_next[npos]
            if my_len > threat_len:
                # We win the H2H — big bonus (kill opportunity)
                score += 60.0
            elif my_len == threat_len:
                score -= 200.0  # mutual death, avoid
            else:
                score -= 400.0  # we lose, avoid strongly

        # Food / health
        if food:
            dists = [abs(npos[0] - fx) + abs(npos[1] - fy) for fx, fy in food]
            nearest = min(dists)
            # Hunger urgency scales as health drops.
            if my_health < 40:
                score -= nearest * 4.0
            elif my_health < 70:
                score -= nearest * 1.5
            else:
                score -= nearest * 0.4
            if npos in food and my_health < 90:
                score += 15.0

        # Slight preference to stay away from walls (more escape routes)
        edge_pen = 0
        if npos[0] == 0 or npos[0] == w - 1:
            edge_pen += 1
        if npos[1] == 0 or npos[1] == h - 1:
            edge_pen += 1
        score -= edge_pen * 1.0

        # Prefer central control for map dominance
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        score -= (abs(npos[0] - cx) + abs(npos[1] - cy)) * 0.15

        if score > best_score:
            best_score = score
            best_mv = mv

    return best_mv
