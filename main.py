"""
Battlesnake bot: safety-first with heuristic evaluation.

Strategy:
- Enumerate legal moves (in-bounds, avoid our body except tail if not growing,
  avoid other snake bodies except their tails if they're not growing).
- Avoid head-to-head losses (opponent head could reach same square and is >=
  our length). If we're longer, we consider such moves as good.
- Score remaining moves by:
    * flood-fill space we can reach (must be >= our length ideally),
    * distance to nearest food (weighted more when health low),
    * center-tropism (mild),
    * penalty for edges/corners,
    * bonus for cutting off shorter opponents (head-to-head kill option).
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
        "author": "opus-4-7",
        "color": "#8A2BE2",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def _occupied(board_state, p):
    return p in board_state


def _build_occupancy(snakes, ignore_tails_of=None):
    """Return set of occupied cells. If a snake's tail is going to move (didn't
    just eat), we can (optionally) treat it as free. ignore_tails_of is a set
    of snake ids whose tail should be considered free."""
    if ignore_tails_of is None:
        ignore_tails_of = set()
    occ = set()
    for s in snakes:
        body = s["body"]
        # If snake just ate (health==100 AND length grew this turn), tail stays.
        # Approximation: if body last two segments overlap, tail is duplicated
        # -> won't move.
        tail_stays = len(body) >= 2 and body[-1] == body[-2]
        for i, seg in enumerate(body):
            if i == len(body) - 1 and not tail_stays and s["id"] in ignore_tails_of:
                continue
            occ.add((seg["x"], seg["y"]))
    return occ


def _flood_fill(start, blocked, w, h, limit=None):
    if start in blocked or not _in_bounds(start, w, h):
        return 0
    seen = {start}
    q = deque([start])
    count = 0
    while q:
        x, y = q.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        for dx, dy in DIRS.values():
            n = (x + dx, y + dy)
            if n in seen:
                continue
            if not _in_bounds(n, w, h):
                continue
            if n in blocked:
                continue
            seen.add(n)
            q.append(n)
    return count


def _bfs_distance(start, targets, blocked, w, h, max_dist=None):
    """Shortest path length from start to any target avoiding blocked cells."""
    if not targets:
        return None
    if start in targets:
        return 0
    seen = {start}
    q = deque([(start, 0)])
    while q:
        (x, y), d = q.popleft()
        if max_dist is not None and d >= max_dist:
            continue
        for dx, dy in DIRS.values():
            n = (x + dx, y + dy)
            if n in seen:
                continue
            if not _in_bounds(n, w, h):
                continue
            if n in blocked and n not in targets:
                continue
            if n in targets:
                return d + 1
            seen.add(n)
            q.append((n, d + 1))
    return None


def move(game_state):
    try:
        return _decide(game_state)
    except Exception:
        return {"move": "up"}


def _decide(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_id = you["id"]
    my_head = (you["head"]["x"], you["head"]["y"])
    my_len = you["length"]
    my_health = you["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board["food"]]
    food_set = set(food)

    # Occupancy: all snake bodies. Tails will move (usually) so we can pass
    # through where a tail is, IF the snake didn't just eat.
    hard_blocked = set()      # walls of any snake body, treating tails as movable
    body_blocked = set()      # includes tails (for stricter checks)
    for s in snakes:
        body = s["body"]
        tail_stays = len(body) >= 2 and body[-1] == body[-2]
        for i, seg in enumerate(body):
            p = (seg["x"], seg["y"])
            body_blocked.add(p)
            if i == len(body) - 1 and not tail_stays:
                # tail will move away next turn; still blocked THIS step because
                # the tail is currently there and other snakes'/our new head
                # collides. But when we step, tail also moves, so it's free.
                continue
            hard_blocked.add(p)

    # Opponents info
    opponents = [s for s in snakes if s["id"] != my_id]

    # For each direction, evaluate.
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nx, ny = my_head[0] + dx, my_head[1] + dy
        np = (nx, ny)
        if not _in_bounds(np, w, h):
            continue
        if np in hard_blocked:
            continue

        # Head-to-head check: any opponent whose head is adjacent to np and
        # length >= mine will kill us (or tie if equal length).
        h2h_loss = False
        h2h_kill = False
        for opp in opponents:
            oh = (opp["head"]["x"], opp["head"]["y"])
            # opponent could move to np
            if abs(oh[0] - nx) + abs(oh[1] - ny) == 1:
                if opp["length"] >= my_len:
                    h2h_loss = True
                else:
                    h2h_kill = True

        # Compute flood fill available from np, treating our new head as blocked.
        blocked_for_ff = set(hard_blocked)
        blocked_for_ff.add(np)
        # Add our current head as blocked (we no longer occupy it; but our body
        # segments minus tail remain).
        # Actually, hard_blocked already contains all our body except tail.
        # Our head is in body[0] which is in hard_blocked. Good.

        # Also treat cells adjacent to bigger opponent heads as risky (they
        # might step there). Not strictly blocked but reduce score.

        space = _flood_fill(np, blocked_for_ff, w, h, limit=my_len * 4 + 20)

        # Distance to nearest food from np
        food_dist = None
        if food_set:
            fd = _bfs_distance(np, food_set, blocked_for_ff, w, h, max_dist=w + h)
            food_dist = fd

        candidates.append({
            "move": name,
            "pos": np,
            "h2h_loss": h2h_loss,
            "h2h_kill": h2h_kill,
            "space": space,
            "food_dist": food_dist,
        })

    if not candidates:
        # No legal moves; try to at least stay in bounds
        for name, (dx, dy) in DIRS.items():
            nx, ny = my_head[0] + dx, my_head[1] + dy
            if _in_bounds((nx, ny), w, h):
                return {"move": name}
        return {"move": "up"}

    # Filter out obvious death (h2h loss) if we have alternatives
    safe = [c for c in candidates if not c["h2h_loss"]]
    # Filter out moves with tiny space (self-trap) if alternatives with more
    # space exist.
    if safe:
        max_space = max(c["space"] for c in safe)
        # Prefer moves where space >= our length (won't trap)
        big_enough = [c for c in safe if c["space"] >= my_len]
        pool = big_enough if big_enough else [c for c in safe if c["space"] == max_space]
    else:
        # All moves are h2h losses; pick the one with most space
        max_space = max(c["space"] for c in candidates)
        pool = [c for c in candidates if c["space"] == max_space]

    # Score remaining candidates
    def score(c):
        s = 0.0
        # Space is most important
        s += c["space"] * 2.0
        # Prefer moves that don't die
        if c["h2h_loss"]:
            s -= 1000
        # Head-to-head kill opportunity
        if c["h2h_kill"]:
            s += 30
        # Food consideration - stronger when health low
        if c["food_dist"] is not None:
            # want food dist small
            # weight scales with hunger
            weight = 1.5
            if my_health < 40:
                weight = 6.0
            elif my_health < 60:
                weight = 3.0
            # If we're the shortest, prefer to eat (grow)
            if opponents:
                max_opp_len = max(o["length"] for o in opponents)
                if my_len <= max_opp_len:
                    weight += 1.5
            s -= weight * c["food_dist"]
        else:
            # No reachable food
            if my_health < 30:
                s -= 20  # discourage moves with no food access when starving
        # Center-tropism (mild)
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        px, py = c["pos"]
        s -= 0.2 * (abs(px - cx) + abs(py - cy))
        # Wall adjacency penalty
        if px == 0 or px == w - 1:
            s -= 1.0
        if py == 0 or py == h - 1:
            s -= 1.0
        return s

    pool.sort(key=score, reverse=True)
    return {"move": pool[0]["move"]}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
