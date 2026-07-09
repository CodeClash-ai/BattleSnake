"""
Smart Battlesnake bot for CodeClash.

Strategy:
  1. Enumerate legal moves (avoid walls, self body except tail-that-will-move, opponent bodies except their tail when they don't eat).
  2. Head-to-head prediction: for opponent adjacent food-adjacencies, avoid head-cells if opponent >= our length.
     Prefer head-cells if we are strictly longer (potential kill).
  3. Flood-fill from each candidate move; require enough space (>= our length or best available).
  4. Prefer moves that: keep large space, move toward nearest food when health low or shorter than opponent, and avoid getting boxed in.
  5. Head-to-head aggression when longer.

Coordinates: y-up. "up" = y+1, "down" = y-1, "left" = x-1, "right" = x+1.
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
        "author": "opus",
        "color": "#22cc88",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def _neighbors(p):
    x, y = p
    return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]


def _will_eat(snake, food_set):
    """Does this snake's next-turn head land on food this turn (i.e., we consider from current state)."""
    # We don't know their move; used generally when computing occupied for our own snake.
    return False


def _build_occupied(snakes, exclude_tail_ids=None):
    """Build set of blocked cells: all snake body segments.
    exclude_tail_ids: set of snake IDs for which the tail cell should NOT be blocked
    (because their tail will move on the next tick, provided they aren't eating).
    """
    occ = set()
    if exclude_tail_ids is None:
        exclude_tail_ids = set()
    for s in snakes:
        body = [(seg["x"], seg["y"]) for seg in s["body"]]
        if not body:
            continue
        # Tail may vacate unless the snake just ate (last two body segments identical)
        if s["id"] in exclude_tail_ids and len(body) >= 2 and body[-1] != body[-2]:
            for seg in body[:-1]:
                occ.add(seg)
        else:
            for seg in body:
                occ.add(seg)
    return occ


def _flood_fill(start_cell, blocked, w, h, limit=None):
    """BFS count of reachable cells from start_cell (start_cell must NOT be in blocked)."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    q = deque([start_cell])
    count = 1
    while q:
        if limit is not None and count >= limit:
            break
        cur = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or nb in blocked or not _in_bounds(nb, w, h):
                continue
            seen.add(nb)
            count += 1
            q.append(nb)
    return count




def _flood_fill_full(start_cell, blocked, w, h, limit=None):
    """Return set of reachable cells (not just count)."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
        return set()
    seen = {start_cell}
    q = deque([start_cell])
    while q:
        if limit is not None and len(seen) >= limit:
            break
        cur = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or nb in blocked or not _in_bounds(nb, w, h):
                continue
            seen.add(nb)
            q.append(nb)
    return seen


def _bfs_distance(src, targets, blocked, w, h):
    """Shortest path length from src to any of the target cells. Returns None if unreachable."""
    if not targets:
        return None
    tset = set(targets)
    if src in tset:
        return 0
    seen = {src}
    q = deque([(src, 0)])
    while q:
        cur, d = q.popleft()
        for nb in _neighbors(cur):
            if nb in seen or not _in_bounds(nb, w, h):
                continue
            if nb in blocked and nb not in tset:
                continue
            if nb in tset:
                return d + 1
            seen.add(nb)
            q.append((nb, d + 1))
    return None


def move(game_state):
    try:
        return _move(game_state)
    except Exception:
        return {"move": "up"}


def _move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    me = game_state["you"]
    my_id = me["id"]
    my_body = [(seg["x"], seg["y"]) for seg in me["body"]]
    my_head = my_body[0]
    my_len = me["length"]
    my_health = me["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    food_set = set(food)

    # All snake tails will vacate unless they ate last turn. Approx: allow all tails to move.
    all_ids = {s["id"] for s in snakes}
    occ_now = _build_occupied(snakes, exclude_tail_ids=all_ids)

    # Opponent heads for head-to-head prediction
    opp_snakes = [s for s in snakes if s["id"] != my_id]
    opp_head_moves = {}  # head -> set of possible next head cells
    for s in opp_snakes:
        oh = (s["head"]["x"], s["head"]["y"])
        obody = set((seg["x"], seg["y"]) for seg in s["body"][:-1])
        possible = []
        for d, (dx, dy) in DIRS.items():
            np = (oh[0] + dx, oh[1] + dy)
            if not _in_bounds(np, w, h):
                continue
            if np in obody:
                continue
            possible.append(np)
        opp_head_moves[s["id"]] = {
            "head": oh,
            "length": s["length"],
            "moves": possible,
        }

    # Danger cells: cells an opponent might move into that would kill us (opp length > my_len for loss, == for tie)
    danger_h2h = set()   # opp strictly longer: we lose
    tie_h2h = set()      # opp equal length: mutual death (tie)
    kill_h2h = set()  # cells where we WIN a head-to-head (strictly longer)
    for oid, info_ in opp_head_moves.items():
        for m_cell in info_["moves"]:
            if info_["length"] > my_len:
                danger_h2h.add(m_cell)
            elif info_["length"] == my_len:
                tie_h2h.add(m_cell)
            else:
                kill_h2h.add(m_cell)

    # Evaluate each possible move
    candidates = []
    for d, (dx, dy) in DIRS.items():
        np = (my_head[0] + dx, my_head[1] + dy)
        if not _in_bounds(np, w, h):
            continue
        if np in occ_now:
            # Could still be OK if it's my own tail that will move and I'm not eating
            # occ_now already excludes tails that will move
            continue
        # Compute space from that cell
        blocked = set(occ_now)
        # Add my new head; remove my old tail if I don't eat here
        # We're moving TO np. If np is food, tail doesn't move (grows).
        my_new_body = [np] + my_body[:-1]
        if np in food_set:
            my_new_body = [np] + my_body  # grow
        # Rebuild blocked as post-move approximation:
        blocked_post = set()
        for s in snakes:
            if s["id"] == my_id:
                continue
            sb = [(seg["x"], seg["y"]) for seg in s["body"]]
            # Assume tail moves for opponent
            if len(sb) >= 2 and sb[-1] != sb[-2]:
                for seg in sb[:-1]:
                    blocked_post.add(seg)
            else:
                for seg in sb:
                    blocked_post.add(seg)
        for seg in my_new_body:
            blocked_post.add(seg)
        # For flood-fill, exclude np itself since our head occupies it (we count reachable AFTER we move).
        # Flood-fill from np treating np as free start.
        blocked_post.discard(np)
        # For tail-reachability, my new tail cell (last of my_new_body) is at my_new_body[-1].
        # Make sure it's not "blocked" so we can see if we can reach it.
        my_new_tail = my_new_body[-1]
        blocked_for_reach = set(blocked_post)
        blocked_for_reach.discard(my_new_tail)
        reachable = _flood_fill_full(np, blocked_for_reach, w, h, limit=max(my_len * 4 + 20, 60))
        space = len(reachable)
        tail_reachable = my_new_tail in reachable
        # New length after this move
        new_len = len(my_new_body)

        # Distance to nearest food from np (in the post-move blocked map)
        food_dist = _bfs_distance(np, food, blocked_post, w, h)

        # H2H flags
        is_h2h_death = np in danger_h2h  # strictly loses
        is_h2h_tie = np in tie_h2h and np not in danger_h2h  # mutual death (tie) if no larger threat too
        is_h2h_kill = np in kill_h2h and np not in danger_h2h and np not in tie_h2h  # only sure if no other threat too

        # Adjacent to opponent head (potential H2H)
        near_larger_head = False
        for oid, info_ in opp_head_moves.items():
            oh = info_["head"]
            if abs(np[0] - oh[0]) + abs(np[1] - oh[1]) == 1 and info_["length"] >= my_len:
                near_larger_head = True
                break

        # 2-ply look-ahead: compute opponent's reachable cells 2 steps from their current head
        # (i.e. cells adjacent to any of their possible next positions).
        # Then check how many of OUR next-move options avoid being killed by a longer opp.
        # We treat the opponent as still being length at least their current length (they might grow).
        # new_len_after is len after this move (already computed as new_len).
        # For opponent whose length_after_next >= new_len_after -> dangerous.
        next_safe_options = 0
        next_options_total = 0
        opp_2step_danger = set()  # cells reachable by any equal/longer opp in exactly 2 steps from now
        for oid, info_ in opp_head_moves.items():
            opp_len_after = info_["length"]  # conservative: might grow if they eat next
            # If opp is currently >= our new_len OR could catch up (opp len == new_len - 1 and eats)
            # For simplicity include if opp_len_after >= new_len - 1 (they might eat and match).
            if opp_len_after < new_len - 1:
                continue
            for m_cell in info_["moves"]:
                # From m_cell, opp can reach m_cell's neighbors in step 2
                for nb in _neighbors(m_cell):
                    if _in_bounds(nb, w, h):
                        opp_2step_danger.add(nb)
        # Our next moves from np
        for nb in _neighbors(np):
            if not _in_bounds(nb, w, h):
                continue
            if nb in blocked_post:  # blocked by opp body or our new body
                continue
            next_options_total += 1
            # Check if this next-move cell is reachable by longer/equal opp on their next turn
            # i.e. is nb a possible 2-step opp cell where opp would be >= new_len?
            # We use conservative danger set opp_2step_danger built above.
            if nb in opp_2step_danger:
                continue  # dangerous
            next_safe_options += 1

        candidates.append({
            "dir": d,
            "cell": np,
            "space": space,
            "food_dist": food_dist,
            "eats": np in food_set,
            "h2h_death": is_h2h_death,
            "h2h_tie": is_h2h_tie,
            "h2h_kill": is_h2h_kill,
            "near_larger_head": near_larger_head,
            "tail_reachable": tail_reachable,
            "new_len": new_len,
            "next_safe_options": next_safe_options,
            "next_options_total": next_options_total,
        })

    if not candidates:
        return {"move": "up"}

    # Filter out lethal (losing) H2H if any alternative exists.
    # Ties are NOT filtered here — they're preferable to certain death.
    safe = [c for c in candidates if not c["h2h_death"]]
    if safe:
        candidates = safe

    # If we have viable non-tie non-trap options, prefer them.
    # A move is "viable" if space >= new_len (won't self-trap).
    non_tie_viable = [c for c in candidates
                      if not c["h2h_tie"] and c["space"] >= c["new_len"]]
    if non_tie_viable:
        candidates = non_tie_viable
    else:
        # No fully viable non-tie option. Consider all remaining candidates.
        # If a non-tie option exists at all, prefer max-space ones there;
        # but if all non-tie options have far less space than a tie, tying might be OK.
        non_tie = [c for c in candidates if not c["h2h_tie"]]
        if non_tie:
            # Best non-tie space
            best_nontie_space = max(c["space"] for c in non_tie)
            # Only include ties if non-tie space is drastically small (likely certain death)
            # e.g. non-tie best space < new_len / 2 -> tying is at least a tie (0 pts) vs loss.
            if best_nontie_space < max(3, my_len // 2):
                # keep all candidates (including ties)
                pass
            else:
                candidates = non_tie

    # Prefer moves where our tail remains reachable (guarantees survival loop)
    tail_ok = [c for c in candidates if c["tail_reachable"]]
    if tail_ok:
        candidates = tail_ok
    # Require enough space; prefer moves with space >= new_len, else max space
    good_space = [c for c in candidates if c["space"] >= c["new_len"]]
    if good_space:
        candidates = good_space
    else:
        max_space = max(c["space"] for c in candidates)
        candidates = [c for c in candidates if c["space"] == max_space]

    # Decide food urgency
    want_food = my_health < 60 or my_len < 5
    # Also want food if we're shorter than the longest opponent
    max_opp_len = max([s["length"] for s in opp_snakes], default=0)
    if my_len <= max_opp_len:
        want_food = True

    def score(c):
        s = 0.0
        s += c["space"] * 1.0
        if c["h2h_kill"]:
            s += 50
        if c.get("h2h_tie"):
            s -= 40  # ties are bad but better than certain death
        if c["near_larger_head"]:
            s -= 30
        # Big bonus for keeping tail reachable
        if c["tail_reachable"]:
            s += 20
        # Space margin bonus (buffer against getting trapped)
        margin = c["space"] - c["new_len"]
        if margin < 0:
            s -= 100  # very bad, only pick if nothing else
        elif margin < 3:
            s -= 15  # tight
        # 2-ply trap avoidance: penalize moves that leave no safe next-turn options
        nso = c.get("next_safe_options", 999)
        nto = c.get("next_options_total", 999)
        if nto > 0 and nso == 0:
            s -= 60  # heavy penalty: next turn we'd have no safe move
        elif nto > 0 and nso == 1:
            s -= 10  # only one safe option, brittle
        if want_food and c["food_dist"] is not None:
            # Closer food is better, but only if space margin is healthy
            if margin >= 3:
                s += max(0, 40 - c["food_dist"] * 3)
                if c["eats"]:
                    s += 15
            elif margin >= 0 and c["food_dist"] < 5:
                # Only chase food when close and space is at least survivable
                s += max(0, 20 - c["food_dist"] * 3)
        elif c["eats"] and my_health < 90:
            if margin >= 3:
                s += 5
        # Corner/edge food-chase penalty: don't take food into a wall trap.
        cx0, cy0 = c["cell"]
        if c["eats"]:
            corner = (cx0 in (0, w-1)) and (cy0 in (0, h-1))
            on_edge0 = (cx0 == 0 or cx0 == w-1 or cy0 == 0 or cy0 == h-1)
            for oid_, info__ in opp_head_moves.items():
                oh__ = info__["head"]
                dman = abs(oh__[0]-cx0)+abs(oh__[1]-cy0)
                opp_bigger = info__["length"] >= my_len
                # Larger/equal opp near edge food = trap (existing)
                if opp_bigger and dman <= 5:
                    if corner: s -= 40
                    elif on_edge0: s -= 15
                # Even a SHORTER opp near edge/corner food can trap us (herd into corner).
                # Penalize less severely but still deter.
                elif not opp_bigger and dman <= 4:
                    if corner: s -= 25
                    elif on_edge0: s -= 10
        # Edge/wall penalty. Much stronger when a >=length opponent is on inner adjacent row/col
        # (mirror-chase trap along wall).
        cx, cy = c["cell"]
        on_edge = (cx == 0 or cx == w - 1 or cy == 0 or cy == h - 1)
        if on_edge:
            s -= 3
            # Detect wall-chase trap: opp head on/near inner adjacent row/col.
            # NOTE: Even a SHORTER opponent can herd us into a corner where we die
            # from walls/self, so trap geometry matters more than head-to-head length.
            trap_risk = False
            trap_risk_hard = False  # opp is same-or-longer: extra penalty
            for oid, info_ in opp_head_moves.items():
                oh = info_["head"]
                same_or_longer = info_["length"] >= my_len
                # Check if opp is on inner adjacent row/col (mirror position),
                # OR diagonal chase (within 2 inward and 5 along). Broader than exact mirror.
                inner_mirror = False
                if cy == 0 and oh[1] <= 2 and abs(oh[0] - cx) <= 5:
                    inner_mirror = True
                elif cy == h - 1 and oh[1] >= h - 3 and abs(oh[0] - cx) <= 5:
                    inner_mirror = True
                elif cx == 0 and oh[0] <= 2 and abs(oh[1] - cy) <= 5:
                    inner_mirror = True
                elif cx == w - 1 and oh[0] >= w - 3 and abs(oh[1] - cy) <= 5:
                    inner_mirror = True
                if inner_mirror:
                    trap_risk = True
                    if same_or_longer:
                        trap_risk_hard = True
                        break
            if trap_risk_hard:
                s -= 60
            elif trap_risk:
                s -= 25  # shorter opp mirror; still risky (corner-death) but less severe
            # Corner is worse
            if (cx in (0, w - 1)) and (cy in (0, h - 1)):
                s -= 15
            # Wall-crawl detection: penalize continuing to hug the wall when body already along it
            wall_segs = 0
            if cy == 0:
                wall_segs = sum(1 for seg in my_body[:4] if seg[1] == 0)
            elif cy == h - 1:
                wall_segs = sum(1 for seg in my_body[:4] if seg[1] == h - 1)
            elif cx == 0:
                wall_segs = sum(1 for seg in my_body[:4] if seg[0] == 0)
            elif cx == w - 1:
                wall_segs = sum(1 for seg in my_body[:4] if seg[0] == w - 1)
            if wall_segs >= 2:
                s -= 5 * wall_segs  # discourage prolonged wall crawl
                # If also being chased/mirrored, extra penalty
                if trap_risk:
                    s -= 10 * wall_segs
        # Proactive edge avoidance: when a LONGER opponent is within "chase range",
        # penalize moves that reduce our distance to the nearest wall.
        # This addresses the "gets herded to wall then dies" loss pattern.
        head_before = my_head
        dist_wall_before = min(head_before[0], head_before[1], w-1-head_before[0], h-1-head_before[1])
        dist_wall_after = min(cx, cy, w-1-cx, h-1-cy)
        # Reward moves that INCREASE distance from wall when longer opp is close (chase avoidance).
        # Penalize moves that stay near wall (dist<=1) when longer opp is within chase range.
        longer_opp_close = False
        for oid_pe, info_pe in opp_head_moves.items():
            if info_pe["length"] < my_len:
                continue
            oh_pe = info_pe["head"]
            dman_pe = abs(oh_pe[0]-my_head[0]) + abs(oh_pe[1]-my_head[1])
            if dman_pe <= 7:
                longer_opp_close = True
                break
        if longer_opp_close:
            if dist_wall_after > dist_wall_before:
                s += 6  # reward escape from wall
            elif dist_wall_after < dist_wall_before:
                if dist_wall_after == 0:
                    s -= 25
                elif dist_wall_after == 1:
                    s -= 10
                else:
                    s -= 3
            elif dist_wall_after <= 1 and dist_wall_before <= 1:
                # Staying near wall with longer opp close -> mild penalty (encourages escape)
                s -= 4

        # Second-order trap: even one step from a wall while opp mirrors, is risky
        # This especially matters when body is trailing along wall.
        # Check if my new body is aligned along the wall for 2+ segments AND opp of >= length is on inner row
        my_new_body_local = None  # placeholder; computed via c metadata
        return s

    candidates.sort(key=score, reverse=True)
    return {"move": candidates[0]["dir"]}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
