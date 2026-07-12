"""
CodeClash BattleSnake bot.

Strategy overview
------------------
This bot replaces the previous "faithful SimpleSnake port" (which had *no*
collision avoidance and greedily targeted the *farthest* food -- a
deliberate quirk of the original Kotlin example bot) with a real survival
+ food-seeking heuristic bot:

  1. Compute the set of currently-occupied ("blocked") cells from every
     snake's body (every segment except each snake's tail, since a tail
     vacates its cell on the next turn as long as that snake doesn't eat
     this turn -- we accept this small inaccuracy since it is the standard
     conservative-but-still-mobile heuristic used by most simple bots).
  2. Generate the legal candidate moves from our head (in bounds, not
     blocked).
  3. Avoid stepping onto a cell that an equal-or-longer opponent could also
     move onto this turn (avoids losing / tying a head-to-head collision).
     Stepping onto a cell only a *shorter* opponent could reach is fine
     (we'd win that collision).
  4. Score every remaining candidate using:
       - flood-fill reachable area from the resulting head position
         (encourages staying in open space / not trapping ourselves),
       - BFS distance to the nearest food (encourages eating, weighted
         more heavily when health is low),
       - a small bonus for eating food immediately when safe.
  5. Pick the highest-scoring candidate. Falls back to "up" (or any
     in-bounds move) if somehow no candidate exists.

This is intentionally simple (no full minimax / opponent modeling) but
should heavily outperform a bot with zero collision avoidance.
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
        "color": "#ff00ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(p, width, height):
    return 0 <= p[0] < width and 0 <= p[1] < height


def _build_blocked(snakes):
    """All body segments except each snake's tail cell (the tail vacates
    next turn as long as that snake doesn't eat this turn).

    Special case: if a snake just ate (detectable statelessly because its
    last two body segments occupy the same cell -- the classic "duplicate
    tail" produced by growth), then even after this move the vacated
    tail's cell is still covered by the new tail (the former second-to-last
    segment, which shares that same coordinate). So in that case we must
    NOT exclude the tail cell -- it stays blocked."""
    blocked = set()
    for s in snakes:
        body = s["body"]
        n = len(body)
        just_ate = n >= 2 and body[-1]["x"] == body[-2]["x"] and body[-1]["y"] == body[-2]["y"]
        for i, seg in enumerate(body):
            if i == n - 1 and not just_ate:
                continue  # tail - assume it vacates next turn
            blocked.add((seg["x"], seg["y"]))
    return blocked


def _flood_fill_size(start, blocked, width, height, cap):
    """BFS reachable-area size from `start`, avoiding `blocked` cells.
    Stops early once `cap` cells are found (cap = enough, e.g. our length*2)
    to keep this cheap."""
    if start in blocked:
        return 0
    seen = {start}
    q = deque([start])
    count = 0
    while q and count < cap:
        cur = q.popleft()
        count += 1
        for dx, dy in DIRS.values():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in seen:
                continue
            if not _in_bounds(nxt, width, height):
                continue
            if nxt in blocked:
                continue
            seen.add(nxt)
            q.append(nxt)
    return count


def _bfs_nearest_food_dist(start, blocked, width, height, food_set):
    """Shortest-path distance (BFS) from start to nearest food, avoiding
    blocked cells. Returns None if unreachable."""
    if not food_set:
        return None
    if start in food_set:
        return 0
    seen = {start}
    q = deque([(start, 0)])
    while q:
        cur, d = q.popleft()
        for dx, dy in DIRS.values():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in seen:
                continue
            if not _in_bounds(nxt, width, height):
                continue
            if nxt in blocked and nxt not in food_set:
                continue
            seen.add(nxt)
            if nxt in food_set:
                return d + 1
            q.append((nxt, d + 1))
    return None


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        you = game_state["you"]
        my_id = you["id"]
        my_body = you["body"]
        head = (my_body[0]["x"], my_body[0]["y"])
        my_length = len(my_body)
        my_health = you.get("health", 100)

        snakes = board["snakes"]
        food = board.get("food", [])
        food_set = {(f["x"], f["y"]) for f in food}

        blocked = _build_blocked(snakes)

        # Cells an equal-or-longer opponent could move into this turn.
        # Cells only a strictly-shorter opponent could reach (a winnable
        # head-to-head for us) are tracked separately for a small
        # aggression bonus.
        risky_cells = set()
        winnable_cells = set()
        for s in snakes:
            if s["id"] == my_id:
                continue
            ohx, ohy = s["head"]["x"], s["head"]["y"]
            target_set = risky_cells if s["length"] >= my_length else winnable_cells
            for dx, dy in DIRS.values():
                np_ = (ohx + dx, ohy + dy)
                if _in_bounds(np_, width, height):
                    target_set.add(np_)

        candidates = []
        for name, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(nxt, width, height):
                continue
            if nxt in blocked:
                continue
            candidates.append((name, nxt))

        if not candidates:
            # Nothing safe - take any in-bounds move as a last resort.
            for name, (dx, dy) in DIRS.items():
                nxt = (head[0] + dx, head[1] + dy)
                if _in_bounds(nxt, width, height):
                    candidates.append((name, nxt))
            if not candidates:
                return {"move": "up"}

        cap = width * height  # full-board flood fill; cheap enough at these sizes for accurate space eval

        best_name = None
        best_score = float("-inf")
        for name, nxt in candidates:
            score = 0.0

            area = _flood_fill_size(nxt, blocked, width, height, cap)
            # Heavily penalize getting trapped in a space smaller than our body.
            if area < my_length:
                score -= (my_length - area) * 50
            score += area * 5

            if nxt in risky_cells:
                score -= 1000

            dist = _bfs_nearest_food_dist(nxt, blocked, width, height, food_set)
            if dist is not None:
                weight = 4 if my_health < 50 else 1.5
                score -= dist * weight
                if dist == 0:
                    score += 20  # immediate food bonus

            # Slight preference to stay away from edges/corners (more escape routes)
            x, y = nxt
            edge_dist = min(x, width - 1 - x, y, height - 1 - y)
            score += edge_dist * 0.5

            # Small aggression bonus: stepping toward a cell only a
            # strictly-shorter opponent could also reach this turn is a
            # winnable head-to-head for us (kills them), so nudge toward
            # it when it doesn't otherwise hurt our safety/space score.
            if nxt in winnable_cells:
                score += 15

            if score > best_score:
                best_score = score
                best_name = name

        return {"move": best_name or "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
