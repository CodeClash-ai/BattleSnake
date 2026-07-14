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


def _reachable(start, goal, blocked, w, h):
    """True if goal is reachable from start via free cells (BFS)."""
    if start == goal:
        return True
    if start in blocked or not _in_bounds(start, w, h):
        return False
    seen = {start}
    stack = [start]
    while stack:
        cx, cy = stack.pop()
        for dx, dy in DIRS.values():
            npp = (cx + dx, cy + dy)
            if npp == goal:
                return True
            if npp in seen or not _in_bounds(npp, w, h) or npp in blocked:
                continue
            seen.add(npp)
            stack.append(npp)
    return False



def _deep_space(np, blocked, w, h, my_len):
    """Estimate worst-case reachable space 2 steps ahead. For each free
    neighbor of np, flood-fill and take the MAX (best continuation). This
    catches corridors that look big now but collapse after one more move:
    an open region keeps a large best-child space, a corridor shrinks fast."""
    best_child = 0
    for dx, dy in DIRS.values():
        nn = (np[0] + dx, np[1] + dy)
        if not _in_bounds(nn, w, h) or nn in blocked:
            continue
        b2 = set(blocked); b2.add(np)
        sp = _flood_fill(nn, b2, w, h, my_len * 4 + 20)
        if sp > best_child:
            best_child = sp
    return best_child


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

            # Corridor-awareness: the best space reachable one more step ahead.
            # An open region keeps a large deep_space; a wall-hugging corridor
            # that will collapse shrinks quickly. Weight this so a tie on raw
            # flood-fill space is broken toward the genuinely open move (this
            # fixes long-game wall-corridor self-traps).
            deep = _deep_space(np, blocked, w, h, my_len)
            score += deep * 40
            if deep < my_len:
                score -= (my_len - deep) * 150

            # Tail-reachability: if from the new head we can still reach our
            # own tail cell, we are guaranteed not to be trapped (we can always
            # follow our tail). Strongly reward this, especially when long.
            # Recompute a flood fill that treats our tail as a target.
            my_tail = me_body[-1]
            # tail becomes free next turn unless we just grew; treat it as a
            # reachable goal cell.
            reach_blocked = set(occupied)
            reach_blocked.add(head)
            reach_blocked.discard(my_tail)
            if _reachable(np, my_tail, reach_blocked, w, h):
                score += 300 + my_len * 8
            else:
                # Cannot reach tail: high risk of self-trap when long.
                score -= my_len * 12

            # Food seeking. Unchanged from the proven bot EXCEPT we stop
            # chasing food once we are extremely long with a decisive length
            # lead (>=25 and >=8 longer than the opponent). This prevents the
            # over-growth self-trap that lost a 364-turn game vs graeme-hill
            # (we reached length 39 and cornered ourselves). At length 25+ we
            # already win every realistic head-to-head, so growth is pure risk.
            if food:
                nearest = min(_manhattan(np, f) for f in food)
                longest_opp = max((ol for _, ol in opp_heads), default=0)
                overgrown = my_len >= 18 and (my_len - longest_opp) >= 5
                hunger = 0.0
                if my_health < 40:
                    hunger = (50 - my_health) * 3.0
                elif not overgrown:
                    hunger = 5.0
                score += hunger * (1.0 / (nearest + 1)) * 20
                if my_health < 40:
                    score -= nearest * 1.5
                elif overgrown:
                    score += nearest * 0.4  # actively avoid food
                else:
                    score -= nearest * 0.3


            # Aggression: when we are strictly longer than an opponent, close
            # distance toward their head to force a winning head-to-head. This
            # secures kills faster and avoids draws in the endgame. Only mild
            # so it never overrides survival/space terms.
            if opp_heads:
                nearest_opp = min(opp_heads, key=lambda oh: _manhattan(head, oh[0]))
                ohead, olen = nearest_opp
                longest_opp_a = max((ol for _, ol in opp_heads), default=0)
                overgrown_a = my_len >= 18 and (my_len - longest_opp_a) >= 5
                if my_len > olen and not overgrown_a:
                    d = _manhattan(np, ohead)
                    # Reward getting closer; stronger when we have big space.
                    # Only mild so it never overrides survival/space terms.
                    score -= d * 6.0
                elif my_len <= olen:
                    # Keep a little distance from a dangerous equal/longer snake.
                    d = _manhattan(np, ohead)
                    if d <= 2:
                        score -= (3 - d) * 40.0

            # 2-ply space check: assume nearest opp moves toward us; recompute
            # our free space with that opp move blocked to catch delayed traps.
            if opp_heads:
                oh, ol = min(opp_heads, key=lambda x: _manhattan(np, x[0]))
                # opp\'s move that gets closest to our new head
                best_op = None; best_opd = 1e9
                for ddx, ddy in DIRS.values():
                    op = (oh[0]+ddx, oh[1]+ddy)
                    if not _in_bounds(op, w, h) or op in occupied:
                        continue
                    d2 = _manhattan(op, np)
                    if d2 < best_opd:
                        best_opd = d2; best_op = op
                if best_op is not None:
                    blk2 = set(blocked); blk2.add(best_op)
                    sp2 = _flood_fill(np, blk2, w, h, my_len * 4 + 20)
                    if sp2 < my_len:
                        score -= (my_len - sp2) * 60

            # Slight preference for staying near center (mobility).
            cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
            score -= (abs(np[0] - cx) + abs(np[1] - cy)) * 0.5

            # Perimeter avoidance (scales with length): when we are long,
            # hugging the walls/edges builds thin corridors that collapse and
            # self-trap us in the endgame. Penalize edge and (worse) corner
            # cells proportionally to our length so the effect only matters
            # once the snake is big enough for coiling to be dangerous.
            if my_len >= 12:
                on_edge = (np[0] == 0 or np[0] == w - 1) + (np[1] == 0 or np[1] == h - 1)
                if on_edge:
                    score -= on_edge * my_len * 1.5

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
        # Defensive fallback: try to pick any in-bounds, non-self move so a
        # freak error never forfeits by walking into a wall.
        try:
            board = game_state["board"]
            w, h = board["width"], board["height"]
            you = game_state["you"]
            body = [(s["x"], s["y"]) for s in you["body"]]
            head = body[0]
            occ = set(body)
            for mv, (dx, dy) in DIRS.items():
                np = (head[0] + dx, head[1] + dy)
                if 0 <= np[0] < w and 0 <= np[1] < h and np not in occ:
                    return {"move": mv}
            for mv, (dx, dy) in DIRS.items():
                np = (head[0] + dx, head[1] + dy)
                if 0 <= np[0] < w and 0 <= np[1] < h:
                    return {"move": mv}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
