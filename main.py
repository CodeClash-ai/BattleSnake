"""A compact, safety-first Battlesnake for CodeClash.

Strategy notes:
- Never knowingly move out of bounds, into a body, or into a losing head-to-head.
- Prefer moves with the largest flood-fill space (survival beats the starter bot).
- Eat when useful (low health, short/equal length, or food is very close), otherwise keep
  to open central space and let reckless opponents eliminate themselves.
- If longer, modestly pressure the opponent; if not, give their head room.
"""

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


def info():
    return {
        "apiversion": "1",
        "author": "gpt-5-5",
        "color": "#22cc88",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def add(p, d):
    return (p[0] + d[0], p[1] + d[1])


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def pt(obj):
    return (obj["x"], obj["y"])


def inside(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def flood(start, blocked, w, h, limit=9999):
    """Count open cells reachable from start, with a small openness bonus."""
    if start in blocked or not inside(start, w, h):
        return 0
    q = [start]
    seen = {start}
    total = 0
    while q and total < limit:
        p = q.pop(0)
        total += 1
        for d in MOVES.values():
            n = add(p, d)
            if inside(n, w, h) and n not in blocked and n not in seen:
                seen.add(n)
                q.append(n)
    return total


def shortest(start, goals, blocked, w, h, max_depth=200):
    if not goals:
        return None
    goals = set(goals)
    if start in goals:
        return 0
    q = [(start, 0)]
    seen = {start}
    qi = 0
    while qi < len(q):
        p, depth = q[qi]
        qi += 1
        if depth >= max_depth:
            continue
        for d in MOVES.values():
            n = add(p, d)
            if not inside(n, w, h) or n in blocked or n in seen:
                continue
            if n in goals:
                return depth + 1
            seen.add(n)
            q.append((n, depth + 1))
    return None


def _fallback_legal(game_state):
    """Last-ditch legal-ish move; used only if scoring fails."""
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = pt(game_state["you"]["head"])
    occupied = {pt(seg) for s in board.get("snakes", []) for seg in s.get("body", [])}
    for name, d in MOVES.items():
        n = add(head, d)
        if inside(n, w, h) and n not in occupied:
            return name
    for name, d in MOVES.items():
        if inside(add(head, d), w, h):
            return name
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        you = game_state["you"]
        w, h = board["width"], board["height"]
        my_id = you["id"]
        my_body = [pt(x) for x in you["body"]]
        head = my_body[0]
        my_len = len(my_body)
        my_health = you.get("health", 100)
        food = [pt(f) for f in board.get("food", [])]
        hazards = {pt(x) for x in board.get("hazards", [])}
        snakes = board.get("snakes", [])
        enemies = [s for s in snakes if s.get("id") != my_id]

        # Cells occupied after the normal tail pop.  Tails are allowed only when
        # the snake is unlikely to grow this turn; this avoids many false traps
        # while remaining conservative near food.
        blocked = set()
        for s in snakes:
            body = [pt(x) for x in s.get("body", [])]
            if not body:
                continue
            tail = body[-1]
            could_grow = (body[0] in food) or (s.get("health", 100) <= 1)
            for i, cell in enumerate(body):
                if i == len(body) - 1 and not could_grow:
                    continue
                blocked.add(cell)

        enemy_heads = [pt(s["head"]) for s in enemies]
        enemy_lengths = {pt(s["head"]): s.get("length", len(s.get("body", []))) for s in enemies}
        danger_equal_longer = set()
        danger_shorter = set()
        for s in enemies:
            eh = pt(s["head"])
            elen = s.get("length", len(s.get("body", [])))
            for d in MOVES.values():
                n = add(eh, d)
                if inside(n, w, h):
                    if elen >= my_len:
                        danger_equal_longer.add(n)
                    else:
                        danger_shorter.add(n)

        # Avoid reversing into our neck when length has expanded from the start.
        neck = my_body[1] if len(my_body) > 1 else None
        scores = []
        center = ((w - 1) / 2.0, (h - 1) / 2.0)
        max_enemy_len = max([s.get("length", len(s.get("body", []))) for s in enemies] + [0])

        for name, delta in MOVES.items():
            n = add(head, delta)
            if not inside(n, w, h):
                continue
            if n == neck and len(set(my_body[:3])) > 1:
                continue
            if n in blocked:
                continue

            # Never voluntarily take a tie/losing head-to-head if any other move exists.
            h2h_bad = n in danger_equal_longer
            # Moving into a shorter snake's possible head square can be good, but only
            # if there is still room afterwards.
            h2h_good = n in danger_shorter

            sim_blocked = set(blocked)
            sim_blocked.add(head)  # our old head becomes neck
            area = flood(n, sim_blocked, w, h, limit=w * h)
            if area <= 1:
                continue

            score = area * 12.0
            if h2h_bad:
                score -= 10000
            if h2h_good and my_len > max_enemy_len:
                score += 40
            # Prefer cells with multiple exits (less likely to enter a cul-de-sac).
            exits = 0
            for d2 in MOVES.values():
                nn = add(n, d2)
                if inside(nn, w, h) and nn not in sim_blocked:
                    exits += 1
            score += exits * 18
            if exits <= 1 and area < my_len + 4:
                score -= 250

            # Food valuation.  Use BFS distance after making this move, because
            # Manhattan distance often walks through bodies.  Be hungrier when low
            # health or when we need length to win head-to-heads.
            food_dist = shortest(n, food, sim_blocked, w, h, max_depth=60)
            if food_dist is not None:
                hunger = max(0, 70 - my_health) * 1.4
                if my_len <= max_enemy_len:
                    hunger += 45
                if food_dist <= 2:
                    hunger += 25
                score += hunger / (food_dist + 1)
                # Do not bloat forever when healthy and already ahead.
                if my_health > 75 and my_len > max_enemy_len + 2 and food_dist <= 1:
                    score -= 20

            # Stay central/open rather than riding walls.
            score -= (abs(n[0] - center[0]) + abs(n[1] - center[1])) * 2.2
            if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                score -= 12
            if n in hazards:
                score -= 200 + max(0, 25 - my_health) * 10

            # If stronger, squeeze toward the opponent; if weaker, maintain distance.
            if enemy_heads:
                nearest_enemy = min(dist(n, eh) for eh in enemy_heads)
                if my_len > max_enemy_len:
                    score += max(0, 7 - nearest_enemy) * 3
                else:
                    score += min(nearest_enemy, 6) * 4

            scores.append((score, name))

        if not scores:
            return {"move": _fallback_legal(game_state)}
        scores.sort(reverse=True)
        return {"move": scores[0][1]}
    except Exception:
        return {"move": _fallback_legal(game_state)}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
