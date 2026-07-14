"""
CodeClash BattleSnake bot (opus-4-8 team).

Strategy: greedy survival + space-aware + food-seeking + head-to-head aware.

The opponent (pambrose-kotlin SimpleSnake) has NO collision avoidance and
moves greedily toward the FARTHEST food (or center if none). It is easily
beaten by any bot that avoids collisions and keeps its options open.

Core decision logic per turn:
  1. Enumerate the 4 candidate moves from the head.
  2. Discard immediately-lethal moves (walls, snake bodies).
  3. Score remaining moves by:
       - reachable free space (flood fill) -> avoid getting trapped
       - head-to-head safety: avoid squares an equal/longer enemy head could
         also move into; seek them if we are strictly longer (kill).
       - food proximity, weighted by hunger (health).
  4. Pick the highest scoring move; fall back to any non-lethal move; else "up".

Coordinate system: BattleSnake API is y-up, bottom-left origin.
  up = y+1, down = y-1, left = x-1, right = x+1.

See README_agent.md for notes.
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
        "color": "#1f8fff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _cells(body):
    return [(p["x"], p["y"]) for p in body]


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _flood_fill(start, blocked, w, h, limit):
    """Count reachable free cells from start (start assumed free), capped."""
    if start in blocked:
        return 0
    seen = {start}
    stack = [start]
    count = 0
    while stack and count < limit:
        cx, cy = stack.pop()
        count += 1
        for dx, dy in DIRS.values():
            nx, ny = cx + dx, cy + dy
            np = (nx, ny)
            if not _in_bounds(nx, ny, w, h):
                continue
            if np in blocked or np in seen:
                continue
            seen.add(np)
            stack.append(np)
    return count


def move(game_state):
    try:
        return {"move": _choose(game_state)}
    except Exception:
        return {"move": "up"}


def _choose(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_body = _cells(you["body"])
    head = my_body[0]
    my_len = you["length"]
    health = you["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    # Occupied cells: all snake bodies. A tail moves away next turn UNLESS the
    # snake just ate (body has a duplicated tail) so it will grow. Treat tails
    # as free only if that snake didn't just eat.
    blocked = set()
    enemy_heads = []  # (head_pos, length)
    for s in snakes:
        cells = _cells(s["body"])
        # tail vacates unless snake ate (last two segments equal => grew)
        grew = len(cells) >= 2 and cells[-1] == cells[-2]
        body_to_block = cells if grew else cells[:-1]
        for c in body_to_block:
            blocked.add(c)
        if s["id"] != you["id"]:
            enemy_heads.append((cells[0], s["length"]))

    # Squares an enemy head could move into next turn.
    enemy_next = {}  # pos -> max enemy length that can reach it
    for (ehx, ehy), elen in enemy_heads:
        for dx, dy in DIRS.values():
            np = (ehx + dx, ehy + dy)
            if _in_bounds(np[0], np[1], w, h):
                enemy_next[np] = max(enemy_next.get(np, 0), elen)

    total_free = w * h
    best_move = None
    best_score = None
    fallback = None

    for name, (dx, dy) in DIRS.items():
        nx, ny = head[0] + dx, head[1] + dy
        np = (nx, ny)

        if not _in_bounds(nx, ny, w, h):
            continue
        if np in blocked:
            continue

        fallback = name  # any legal (non-immediately-lethal) move

        # Space via flood fill from the new head position.
        # Remove our own tail from blocked for the fill (it will move).
        space = _flood_fill(np, blocked, w, h, total_free)

        score = 0.0
        # Space is king: strongly prefer moves that don't trap us.
        score += space * 10.0
        # Prefer having room to fit our whole body.
        if space < my_len:
            score -= 500.0

        # Head-to-head handling.
        if np in enemy_next:
            other_len = enemy_next[np]
            if my_len > other_len:
                score += 60.0   # we win the H2H -> kill opportunity
            else:
                score -= 1000.0  # we lose or tie -> avoid

        # Food seeking, weighted by hunger.
        if food:
            nearest = min(abs(nx - fx) + abs(ny - fy) for fx, fy in food)
            # Hungrier -> care more about getting closer to food.
            hunger = (100 - health)
            food_weight = 1.0 + hunger * 0.15
            score -= nearest * food_weight
            if health < 30:
                # urgent: heavily favor approaching food
                score -= nearest * 4.0
            if (nx, ny) in food:
                score += 40.0

        if best_score is None or score > best_score:
            best_score = score
            best_move = name

    if best_move is not None:
        return best_move
    if fallback is not None:
        return fallback
    return "up"


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
