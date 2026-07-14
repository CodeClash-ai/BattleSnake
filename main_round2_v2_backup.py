"""
CodeClash BattleSnake bot (opus-4-8).

Strategy: survival-first with flood-fill space evaluation, safe food seeking,
and opportunistic head-to-head aggression against smaller/equal opponents.

Coordinate system: y-up, bottom-left origin. up=y+1, down=y-1, left=x-1, right=x+1.

The opponent (pambrose SimpleSnake) has NO collision avoidance and blindly
moves toward the farthest food (x dominates y). We simply need to survive
longer and avoid handing it easy head-to-heads we'd lose.
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
        "color": "#ff00ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": "up"}


def _choose_move(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    my_body = [(s["x"], s["y"]) for s in you["body"]]
    head = my_body[0]
    my_len = you["length"]
    my_health = you["health"]

    hazards = set((h["x"], h["y"]) for h in board.get("hazards", []))

    snakes = board["snakes"]

    # All currently occupied cells (bodies). Tails will move away next turn
    # unless the snake just ate; we approximate by treating tails as free
    # unless health==100 (just ate).
    occupied = set()
    tails = set()
    for s in snakes:
        body = [(seg["x"], seg["y"]) for seg in s["body"]]
        # Body except tail is definitely occupied next turn.
        for seg in body[:-1]:
            occupied.add(seg)
        tail = body[-1]
        # If snake just ate (health 100 and length>1 with doubled tail), tail stays.
        if s["health"] == 100:
            occupied.add(tail)
        else:
            tails.add(tail)

    # Opponent snakes and their possible next-head positions (for head-to-head).
    opponents = [s for s in snakes if s["id"] != you["id"]]

    # Cells threatened by an opponent head next turn (they could move there).
    enemy_next = {}  # cell -> max opponent length that could occupy it
    for s in opponents:
        oh = (s["body"][0]["x"], s["body"][0]["y"])
        olen = s["length"]
        for dx, dy in DIRS.values():
            c = (oh[0] + dx, oh[1] + dy)
            if c in enemy_next:
                enemy_next[c] = max(enemy_next[c], olen)
            else:
                enemy_next[c] = olen

    def in_bounds(c):
        return 0 <= c[0] < width and 0 <= c[1] < height

    def is_blocked(c):
        # Blocked by wall or a body segment that will still be there.
        if not in_bounds(c):
            return True
        if c in occupied:
            return True
        return False

    # Evaluate candidate moves.
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nc = (head[0] + dx, head[1] + dy)
        if is_blocked(nc):
            continue
        # Head-to-head danger: an enemy could also move here.
        h2h_len = enemy_next.get(nc, 0)
        # We lose or tie a head-to-head unless strictly longer.
        lose_h2h = h2h_len >= my_len
        candidates.append((name, nc, lose_h2h, h2h_len))

    if not candidates:
        # No non-blocked move; try tail cells (may open up).
        for name, (dx, dy) in DIRS.items():
            nc = (head[0] + dx, head[1] + dy)
            if in_bounds(nc) and nc not in occupied:
                return name
        return "up"

    # Flood-fill reachable free space from a cell, to avoid trapping ourselves.
    def flood_fill(start_cell, blocked_set, limit=None):
        seen = set()
        stack = [start_cell]
        seen.add(start_cell)
        count = 0
        while stack:
            cur = stack.pop()
            count += 1
            if limit and count >= limit:
                break
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn in seen:
                    continue
                if not in_bounds(nn):
                    continue
                if nn in blocked_set:
                    continue
                seen.add(nn)
                stack.append(nn)
        return count

    # Build a blocked set for flood fill: bodies (excluding our tail which moves).
    def score_candidate(cand):
        name, nc, lose_h2h, h2h_len = cand
        # blocked set for flood fill from nc: all occupied cells + our new head.
        blocked = set(occupied)
        blocked.add(nc)
        # our tail cell frees up (already excluded from occupied unless ate)
        space = flood_fill(nc, blocked, limit=width * height)

        score = 0.0
        # Heavily penalize potential losing head-to-heads.
        if lose_h2h:
            score -= 1000.0
        else:
            # winning/no h2h - if enemy could be there and we're longer, chance to kill.
            if h2h_len > 0:
                score += 30.0

        # Space is critical: reward available room. Need at least my_len space.
        score += space * 6.0
        if space < my_len:
            score -= (my_len - space) * 60.0
        # Extra danger: a very tight pocket (< half my length) is near-fatal.
        if space < my_len // 2 + 1:
            score -= 300.0

        # Hazard avoidance: entering a hazard costs 14hp/turn. Penalize unless
        # we have plenty of health or it's needed. Strong penalty when low.
        if nc in hazards:
            # Cost of a hazard step is ~14hp. Penalize proportionally so we
            # avoid it when healthy but can still chase essential food when
            # starving (food logic breaks ties among equal-scored moves).
            score -= 60.0

        return score, space, name, nc

    scored = [score_candidate(c) for c in candidates]
    scored.sort(reverse=True)

    best_score = scored[0][0]
    best = [s for s in scored if s[0] >= best_score - 1e-9]

    # Among the best-scoring safe moves, pick by food strategy.
    food = [(f["x"], f["y"]) for f in board["food"]]

    # Decide whether to chase food: chase if hungry OR to grow advantage.
    want_food = my_health < 60 or my_len <= _max_opp_len(opponents) + 1

    def food_dist(nc):
        if not food:
            return 9999
        return min(_manhattan(nc, f) for f in food)

    if food and want_food:
        # Prefer the move that most reduces distance to nearest food.
        best.sort(key=lambda s: (food_dist(s[3]), -s[1]))
    else:
        # We are clearly longer than every opponent: hunt to force a
        # favorable head-to-head, while keeping space priority.
        clearly_longer = my_len > _max_opp_len(opponents) + 1
        if clearly_longer and opponents:
            opp_heads = [(o["body"][0]["x"], o["body"][0]["y"]) for o in opponents]

            def opp_dist(nc):
                return min(_manhattan(nc, oh) for oh in opp_heads)

            # Keep ample space, then close distance to the enemy head.
            best.sort(key=lambda s: (-s[1], opp_dist(s[3])))
        else:
            # Prefer more space, then move toward center for safety.
            center = (width // 2, height // 2)
            best.sort(key=lambda s: (-s[1], _manhattan(s[3], center)))

    return best[0][2]


def _max_opp_len(opponents):
    if not opponents:
        return 0
    return max(s["length"] for s in opponents)


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
