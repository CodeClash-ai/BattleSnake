"""
Strong Battlesnake bot for CodeClash 1v1 standard 11x11.

Strategy:
  - Enumerate the 4 possible moves.
  - Simulate the board one step ahead (bodies shift, tails move).
  - Avoid walls, self, and opponent bodies.
  - Avoid losing head-to-head collisions; seek winning ones.
  - Use flood-fill to estimate reachable free space for each candidate move,
    strongly preferring moves that don't trap us.
  - Seek food when health is low or when it's safe/close, targeting NEAREST food.
  - Score each move with a weighted combination and pick the best.

Coordinate system: BattleSnake v1 (y-up, bottom-left origin).
  up = y+1, down = y-1, left = x-1, right = x+1.
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


def _flood_fill(start, blocked, w, h, limit):
    """Count reachable free cells from start, up to limit (BFS)."""
    if start in blocked or not _in_bounds(start, w, h):
        return 0
    seen = {start}
    stack = [start]
    count = 0
    while stack and count < limit:
        cx, cy = stack.pop()
        count += 1
        for dx, dy in DIRS.values():
            np = (cx + dx, cy + dy)
            if np in seen:
                continue
            if not _in_bounds(np, w, h):
                continue
            if np in blocked:
                continue
            seen.add(np)
            stack.append(np)
    return count


def move(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        you = game_state["you"]
        me_body = [(s["x"], s["y"]) for s in you["body"]]
        head = me_body[0]
        my_len = len(me_body)
        my_health = you["health"]

        snakes = board["snakes"]
        food = [(f["x"], f["y"]) for f in board.get("food", [])]

        # Build set of occupied cells that will persist next turn.
        # Each snake's tail moves away unless the snake just ate (health==100
        # after eating -> body has duplicate tail). We conservatively treat the
        # tail as free if the snake did NOT eat (i.e. body[-1] != body[-2]).
        occupied = set()
        opp_heads = []  # (head_pos, length)
        for s in snakes:
            body = [(seg["x"], seg["y"]) for seg in s["body"]]
            # tail will move; keep it blocked only if the snake likely grows
            grows = (len(body) >= 2 and body[-1] == body[-2]) or s["health"] == 100
            cells = body if grows else body[:-1]
            for c in cells:
                occupied.add(c)
            if s["id"] != you["id"]:
                opp_heads.append((body[0], len(body)))

        # Opponent's possible next head positions (for head-to-head handling).
        opp_next = {}  # cell -> max opp length that could arrive there
        for ohead, olen in opp_heads:
            for dx, dy in DIRS.values():
                np = (ohead[0] + dx, ohead[1] + dy)
                if _in_bounds(np, w, h):
                    if np not in opp_next or olen > opp_next[np]:
                        opp_next[np] = olen

        best_move = None
        best_score = -1e18

        for mv, (dx, dy) in DIRS.items():
            np = (head[0] + dx, head[1] + dy)

            # Hard constraints
            if not _in_bounds(np, w, h):
                continue
            if np in occupied:
                continue

            score = 0.0

            # Head-to-head danger evaluation
            hh_len = opp_next.get(np, 0)
            if hh_len:
                if hh_len >= my_len:
                    # We'd lose or tie the head-to-head: very bad
                    score -= 10000
                else:
                    # We'd win it: bonus
                    score += 500

            # Flood fill: space available after moving here.
            blocked = set(occupied)
            blocked.add(head)  # our new neck occupies head cell
            space = _flood_fill(np, blocked, w, h, my_len * 4 + 20)
            score += space * 100

            # Prefer not to shrink into a space smaller than our body.
            if space < my_len:
                score -= (my_len - space) * 200

            # Food seeking
            if food:
                nearest = min(_manhattan(np, f) for f in food)
                # Weight food by hunger. Always mildly attractive.
                hunger = 0.0
                if my_health < 40:
                    hunger = (50 - my_health) * 3.0
                else:
                    hunger = 5.0
                score += hunger * (1.0 / (nearest + 1)) * 20
                score -= nearest * (1.5 if my_health < 40 else 0.3)


            # Aggression: when we are strictly longer than an opponent, close
            # distance toward their head to force a winning head-to-head. This
            # secures kills faster and avoids draws in the endgame. Only mild
            # so it never overrides survival/space terms.
            if opp_heads:
                nearest_opp = min(opp_heads, key=lambda oh: _manhattan(head, oh[0]))
                ohead, olen = nearest_opp
                if my_len > olen:
                    d = _manhattan(np, ohead)
                    # Reward getting closer; stronger when we have big space.
                    score -= d * 6.0
                elif my_len <= olen:
                    # Keep a little distance from a dangerous equal/longer snake.
                    d = _manhattan(np, ohead)
                    if d <= 2:
                        score -= (3 - d) * 40.0

            # Slight preference for staying near center (mobility).
            cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
            score -= (abs(np[0] - cx) + abs(np[1] - cy)) * 0.5

            if score > best_score:
                best_score = score
                best_move = mv

        if best_move is None:
            # No hard-safe move; pick the least-bad option instead of blindly
            # walking into a wall/self. Rank by: in-bounds, then not into an
            # occupied body cell, then most flood-fill space (may still be a
            # forced H2H, but survival odds are higher).
            best_fb = None
            best_fb_score = -1e18
            for mv, (dx, dy) in DIRS.items():
                np = (head[0] + dx, head[1] + dy)
                sc = 0.0
                if not _in_bounds(np, w, h):
                    sc -= 100000
                if np in occupied:
                    sc -= 50000
                blocked = set(occupied); blocked.add(head)
                sc += _flood_fill(np, blocked, w, h, my_len * 4 + 20) * 10
                if sc > best_fb_score:
                    best_fb_score = sc
                    best_fb = mv
            best_move = best_fb or "up"

        return {"move": best_move}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
