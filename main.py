import random

# BattleSnake bot (standard 1v1 / multiplayer, v1 API, bottom-left origin y-up).
#
# Strategy (much stronger than the naive pinky-snek port it replaces):
#   1. Enumerate the 4 candidate moves for our head.
#   2. Hard-filter moves that are certainly fatal: off-board, into a
#      snake body segment that will still be there next turn (tails handled),
#      or a losing/tied head-to-head collision.
#   3. Among surviving moves, score each with:
#        - flood-fill reachable free space from the resulting head (avoid
#          trapping ourselves in a small pocket). This is the dominant term.
#        - winning head-to-head opportunities vs strictly-smaller enemies.
#        - food proximity (weighted higher when health is low).
#   4. Pick the highest-scoring move. Robust fallbacks guarantee a legal move.
#
# Notes for teammates:
#   - main_v1_backup.py holds the original naive port.
#   - analyze_logs.py summarizes /logs/rounds results.
#   - See README_agent.md for details.

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "moxuz",
        "color": "#ff5fa2",
        "head": "smart-caterpillar",
        "tail": "bolt",
    }


def start(game_state):
    return


def end(game_state):
    return


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _occupied_next_turn(game_state):
    """Set of cells that will be blocked next turn.

    Every snake body cell blocks EXCEPT the tail cell, which will move away
    UNLESS that snake just ate (health == 100 -> tail stays / grows).
    We conservatively keep the tail if the snake ate last turn.
    """
    board = game_state["board"]
    blocked = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        ate = snake.get("health", 0) == 100
        for i, seg in enumerate(body):
            if i == n - 1 and not ate and n > 1:
                # tail vacates unless the snake grew
                continue
            blocked.add((seg["x"], seg["y"]))
    return blocked


def _flood_fill(start, blocked, w, h, limit=None):
    """Count reachable free cells from start (start assumed free-ish)."""
    if limit is None:
        limit = w * h
    seen = set()
    stack = [start]
    seen.add(start)
    count = 0
    while stack and count < limit:
        cx, cy = stack.pop()
        count += 1
        for dx, dy in DIRS.values():
            nx, ny = cx + dx, cy + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in blocked or (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            stack.append((nx, ny))
    return count


def _nearest_food_dist(pos, foods):
    if not foods:
        return None
    px, py = pos
    return min(abs(px - fx) + abs(py - fy) for fx, fy in foods)


def move(game_state):
    try:
        return _move_impl(game_state)
    except Exception:
        try:
            return _safe_fallback(game_state)
        except Exception:
            return {"move": "up"}


def _move_impl(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]
    my_len = you["length"]
    health = you.get("health", 100)

    foods = [(f["x"], f["y"]) for f in board.get("food", [])]

    blocked = _occupied_next_turn(game_state)

    # Enemy heads and their lengths for head-to-head reasoning.
    enemies = []
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        eh = snake["body"][0]
        enemies.append(((eh["x"], eh["y"]), snake["length"]))

    # Cells an enemy head could move into next turn.
    enemy_next = {}  # cell -> max enemy length that could arrive there
    for (ex, ey), elen in enemies:
        for dx, dy in DIRS.values():
            nx, ny = ex + dx, ey + dy
            if _in_bounds(nx, ny, w, h):
                enemy_next[(nx, ny)] = max(enemy_next.get((nx, ny), 0), elen)

    candidates = []
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if not _in_bounds(nx, ny, w, h):
            continue
        if (nx, ny) in blocked:
            continue

        # Head-to-head: if an enemy of length >= ours could also move here,
        # it's a loss or tie -> avoid unless no other option.
        hh_penalty = 0
        hh_bonus = 0
        contested_len = enemy_next.get((nx, ny), 0)
        if contested_len:
            if contested_len >= my_len:
                hh_penalty = 1  # dangerous
            else:
                hh_bonus = 1    # we'd win this head-to-head (they're smaller)

        # Flood fill from the new head position.
        new_blocked = set(blocked)
        new_blocked.add((nx, ny))
        space = _flood_fill((nx, ny), new_blocked, w, h)

        # Food scoring.
        fdist = _nearest_food_dist((nx, ny), foods)
        food_score = 0.0
        if fdist is not None:
            # Stronger pull when hungry.
            if health < 35:
                food_score = 12.0 / (fdist + 1)
            elif health < 60:
                food_score = 4.0 / (fdist + 1)
            else:
                food_score = 1.0 / (fdist + 1)

        candidates.append({
            "move": mv,
            "space": space,
            "hh_penalty": hh_penalty,
            "hh_bonus": hh_bonus,
            "food_score": food_score,
        })

    if not candidates:
        return _safe_fallback(game_state)

    # Prefer moves without deadly head-to-head risk if any exist.
    safe = [c for c in candidates if not c["hh_penalty"]]
    pool = safe if safe else candidates

    # If space is very tight, prioritize space above all (survival first).
    def score(c):
        s = c["space"] * 3.0
        s += c["hh_bonus"] * 8.0
        s += c["food_score"]
        # small tie-break randomness handled outside
        return s

    best = max(pool, key=score)
    # Guard: never pick a move that traps us into < my_len space if a
    # roomier alternative exists (avoid self-trap deaths).
    roomy = [c for c in pool if c["space"] >= my_len]
    if roomy and best["space"] < my_len:
        best = max(roomy, key=score)

    return {"move": best["move"]}


def _safe_fallback(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]
    blocked = _occupied_next_turn(game_state)
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if _in_bounds(nx, ny, w, h) and (nx, ny) not in blocked:
            return {"move": mv}
    for mv, (dx, dy) in DIRS.items():
        nx, ny = hx + dx, hy + dy
        if _in_bounds(nx, ny, w, h):
            return {"move": mv}
    return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
