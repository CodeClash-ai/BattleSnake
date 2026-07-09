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



def _voronoi_territory(my_head, opp_heads, blocked_static, w, h):
    """Multi-source BFS. Returns (my_cells, opp_cells) counts.
    Ties (same distance) count toward opp (conservative).
    blocked_static: cells always blocked (bodies)."""
    # Multi-source BFS: distance grid
    from collections import deque as _dq
    INF = 10**9
    dist_me = {}
    dist_op = {}
    q = _dq()
    if my_head not in blocked_static and _in_bounds(my_head, w, h):
        dist_me[my_head] = 0
        q.append((my_head, 0, 'me'))
    for oh in opp_heads:
        if oh not in blocked_static and _in_bounds(oh, w, h):
            dist_op[oh] = 0
            q.append((oh, 0, 'op'))
    # Merged BFS layer by layer to handle ties
    visited = {}
    # Do proper layered BFS
    layer = {}
    if my_head not in blocked_static and _in_bounds(my_head, w, h):
        layer[my_head] = ('me', 0)
    for oh in opp_heads:
        if oh not in blocked_static and _in_bounds(oh, w, h):
            if oh in layer:
                layer[oh] = ('tie', 0)
            else:
                layer[oh] = ('op', 0)
    frontier = list(layer.keys())
    step = 0
    while frontier:
        step += 1
        new_layer = {}
        for cell in frontier:
            owner, _ = layer[cell]
            for nb in _neighbors(cell):
                if not _in_bounds(nb, w, h): continue
                if nb in blocked_static: continue
                if nb in layer: continue
                if nb in new_layer:
                    if new_layer[nb][0] != owner:
                        new_layer[nb] = ('tie', step)
                else:
                    new_layer[nb] = (owner, step)
        for k, v in new_layer.items():
            layer[k] = v
        frontier = list(new_layer.keys())
    my_cells = sum(1 for v in layer.values() if v[0] == 'me')
    op_cells = sum(1 for v in layer.values() if v[0] == 'op')
    tie_cells = sum(1 for v in layer.values() if v[0] == 'tie')
    return my_cells, op_cells, tie_cells



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
            # If opp adjacent to food, opp may eat and grow -> len becomes length+1
            eff_len = info_["length"]
            if m_cell in food_set:
                eff_len += 1
            if eff_len > my_len:
                danger_h2h.add(m_cell)
            elif eff_len == my_len:
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
        reachable = _flood_fill_full(np, blocked_for_reach, w, h, limit=w * h)
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
            # 3-ply check: does nb have at least one non-blocked, non-danger neighbor? 
            # Avoids counting dead-end next moves as "safe".
            # blocked_post_after_nb: assume we move to np then to nb (both occupy body head positions).
            # For rough check, use blocked_post plus nb, minus my new tail (which will vacate again).
            has_escape = False
            blocked_after_nb = set(blocked_post)
            blocked_after_nb.add(nb)
            # Old tail (my_new_body[-1]) vacates; drop it if not eating on nb move
            if nb not in food_set and len(my_new_body) >= 1:
                blocked_after_nb.discard(my_new_body[-1])
            for nb2 in _neighbors(nb):
                if not _in_bounds(nb2, w, h):
                    continue
                if nb2 in blocked_after_nb:
                    continue
                has_escape = True
                break
            if not has_escape:
                continue  # dead-end, don't count as safe
            next_safe_options += 1

        # Voronoi territory: how many cells we control faster than opps.
        # Simulate opp heads at their possible next moves (union approach).
        # Static blocked for voronoi = my_new_body (minus new head) + opp bodies (minus tails).
        vor_blocked = set()
        for seg in my_new_body:
            vor_blocked.add(seg)
        for s in snakes:
            if s["id"] == my_id: continue
            sb = [(seg["x"], seg["y"]) for seg in s["body"]]
            if len(sb) >= 2 and sb[-1] != sb[-2]:
                for seg in sb[:-1]:
                    vor_blocked.add(seg)
            else:
                for seg in sb:
                    vor_blocked.add(seg)
        vor_blocked.discard(np)
        # Use current opp heads as sources
        opp_heads_vor = [(s["head"]["x"], s["head"]["y"]) for s in snakes if s["id"] != my_id]
        # Remove opp head cells from blocked (they'll move)
        for oh in opp_heads_vor:
            vor_blocked.discard(oh)
        my_terr, op_terr, tie_terr = _voronoi_territory(np, opp_heads_vor, vor_blocked, w, h)

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
            "my_terr": my_terr,
            "op_terr": op_terr,
        })

    if not candidates:
        return {"move": "up"}

    # Filter out lethal (losing) H2H if any alternative exists.
    # Ties are NOT filtered here — they're preferable to certain death.
    safe = [c for c in candidates if not c["h2h_death"]]
    if safe:
        # BUT: if all "safe" options self-trap (space < new_len), the h2h_death options
        # (which give opp a *chance* to kill us, not certainty) may actually be better,
        # since opp might not choose to head-to-head us. Keep h2h_death options if
        # every safe option is a hard trap.
        safe_has_survivable = any(c["space"] >= c["new_len"] for c in safe)
        if not safe_has_survivable:
            # Consider h2h_death as an alternative: prefer moves with more space and
            # where opp isn't forced to hit us.
            unsafe = [c for c in candidates if c["h2h_death"]]
            best_safe_space = max(c["space"] for c in safe)
            # Only keep h2h_death options substantially better in space
            good_unsafe = [c for c in unsafe if c["space"] >= max(best_safe_space + 8, c["new_len"] + 3)]
            if good_unsafe:
                candidates = safe + good_unsafe
            else:
                candidates = safe
        else:
            candidates = safe

    # If we have viable non-tie non-death non-trap options, prefer them.
    # A move is "viable" if space >= new_len (won't self-trap).
    # CRITICAL: don't filter out h2h_death here in a way that ELIMINATES trap alternatives,
    # since some opponents (like beames) aggressively h2h. We want to preserve at least
    # one non-h2h-death option if one exists.
    non_tie_viable = [c for c in candidates
                      if not c["h2h_tie"] and not c["h2h_death"] and c["space"] >= c["new_len"]]
    if non_tie_viable:
        candidates = non_tie_viable
    else:
        # No fully viable non-tie non-death option. Prefer non-tie non-death even if trapped.
        non_tie_alive = [c for c in candidates if not c["h2h_tie"] and not c["h2h_death"]]
        if non_tie_alive:
            candidates = non_tie_alive
        else:
            # All options are h2h_death or h2h_tie. Prefer ties over death.
            non_death = [c for c in candidates if not c["h2h_death"]]
            if non_death:
                candidates = non_death
            # else: all h2h_death, no choice

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
    # Early-game: aggressively seek food when short - starving at length 3 is common loss.
    small_urgent = my_len <= 4

    def score(c):
        s = 0.0
        s += c["space"] * 1.0
        # Territory advantage (Voronoi): we want more of the board than opp
        terr_diff = c.get("my_terr", 0) - c.get("op_terr", 0)
        s += terr_diff * 0.7
        # Absolute low-territory penalty: if we have very few cells, we're getting boxed in.
        if c.get("my_terr", 999) < c["new_len"]:
            s -= 30
        if c["h2h_death"]:
            s -= 400  # h2h loss; only pick if all safe options are traps

        if c["h2h_kill"]:
            s += 50
        if c.get("h2h_tie"):
            s -= 90  # ties are bad but better than certain death
        # DIAGONAL-CHASE TIE AVOIDANCE: when equal-length opp is diagonally adjacent
        # to our current head (manhattan==2, chebyshev==1), moving to a cell adjacent
        # to opp head is dangerous - opp can force mutual death. Reward moves that
        # increase manhattan distance to opp head in this scenario.
        for oid_dtie, info_dtie in opp_head_moves.items():
            if info_dtie["length"] != my_len:
                continue
            oh_dtie = info_dtie["head"]
            dman_now = abs(oh_dtie[0]-my_head[0]) + abs(oh_dtie[1]-my_head[1])
            chb_now = max(abs(oh_dtie[0]-my_head[0]), abs(oh_dtie[1]-my_head[1]))
            if dman_now == 2 and chb_now == 1:
                # Diagonal-adjacent, equal length. Encourage moving AWAY.
                dman_after = abs(oh_dtie[0]-c["cell"][0]) + abs(oh_dtie[1]-c["cell"][1])
                if dman_after > dman_now:
                    s += 12  # move away
                elif dman_after < dman_now:
                    s -= 12  # move toward - risky
                # Also strongly discourage the two "tie-into-shared-cell" moves
                # (cells adjacent to opp head that we could both reach)
                if dman_after == 1:
                    s -= 25  # this cell is opp-adjacent, high tie risk
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
            s -= 25  # tight (was 15)
        elif margin < 6:
            s -= 8   # somewhat tight
        # Extra penalty for tight space when longer/equal opp is close (they'll close the space)
        min_opp_dist = 999
        max_opp_len_local = 0
        for oid_mp, info_mp in opp_head_moves.items():
            oh_mp = info_mp["head"]
            dman_mp = abs(oh_mp[0]-c["cell"][0]) + abs(oh_mp[1]-c["cell"][1])
            if dman_mp < min_opp_dist:
                min_opp_dist = dman_mp
            if info_mp["length"] > max_opp_len_local:
                max_opp_len_local = info_mp["length"]
        opp_ge = max_opp_len_local >= my_len
        if opp_ge and min_opp_dist <= 6:
            # Penalize tight space when longer/equal opp is nearby
            if margin < 5:
                s -= (5 - margin) * 8  # up to -40
        # Anti-trap: if move takes us CLOSER to longer opp AND space margin is not comfortable,
        # significantly penalize (opp can herd us into their body/wall).
        if opp_ge and margin < 8:
            # Find distance from my_head vs c["cell"] to nearest longer opp head
            dist_to_opp_before = 999
            dist_to_opp_after = 999
            for oid_at, info_at in opp_head_moves.items():
                if info_at["length"] < my_len: continue
                oh_at = info_at["head"]
                d_b = abs(oh_at[0]-my_head[0]) + abs(oh_at[1]-my_head[1])
                d_a = abs(oh_at[0]-c["cell"][0]) + abs(oh_at[1]-c["cell"][1])
                if d_b < dist_to_opp_before: dist_to_opp_before = d_b
                if d_a < dist_to_opp_after: dist_to_opp_after = d_a
            if dist_to_opp_after < dist_to_opp_before and dist_to_opp_after <= 4:
                # Moving closer to longer opp when we're already tight
                s -= (8 - margin) * 3
        # 2-ply trap avoidance: penalize moves that leave no safe next-turn options
        nso = c.get("next_safe_options", 999)
        nto = c.get("next_options_total", 999)
        if nto > 0 and nso == 0:
            s -= 200  # heavy penalty: next turn we'd have no safe move (near-certain death)
        elif nto > 0 and nso == 1:
            s -= 20  # only one safe option, brittle
        if want_food and c["food_dist"] is not None:
            # Closer food is better, but only if space margin is healthy
            if margin >= 3:
                # Boost bonus significantly when we're shorter (need to catch up).
                food_bonus = max(0, 45 - c["food_dist"] * 3)
                if my_len < max_opp_len:
                    # BIGGER urgency: length gap matters
                    gap = max_opp_len - my_len
                    food_bonus += max(0, 40 - c["food_dist"] * 2) + gap * 5
                elif my_len == max_opp_len:
                    # Equal length - still important to eat so we dont fall behind.
                    # Especially against nbw-family opponents that systematically out-grow us.
                    food_bonus += max(0, 30 - c["food_dist"] * 2)
                # UNCONTESTED FOOD BOOST: if the nearest food is CLOSER to us than to any
                # opponent by a comfortable margin, we should be aggressive - it's free growth.
                # Compute manhattan dist from c["cell"] to nearest food, and compare to opp dists.
                try:
                    cell_x, cell_y = c["cell"]
                    best_my_fd = None
                    for fx, fy in food:
                        d_me = abs(fx-cell_x)+abs(fy-cell_y)
                        d_opp_min = 999
                        for _oid, _info in opp_head_moves.items():
                            _oh = _info["head"]
                            d_opp = abs(fx-_oh[0])+abs(fy-_oh[1])
                            if d_opp < d_opp_min: d_opp_min = d_opp
                        # uncontested if we're at least 3 closer
                        if d_opp_min - d_me >= 3 and d_me <= 6:
                            if best_my_fd is None or d_me < best_my_fd:
                                best_my_fd = d_me
                    if best_my_fd is not None:
                        # Bonus scales with how close food is (closer = more urgent)
                        food_bonus += max(0, 25 - best_my_fd * 3)
                except Exception:
                    pass
                s += food_bonus
                if c["eats"]:
                    if my_len < max_opp_len:
                        s += 30 + (max_opp_len - my_len) * 3
                    elif my_len == max_opp_len:
                        # Equal length: eat to stay ahead of opp growth
                        s += 22
                    elif my_len <= 5:
                        # Early game: strongly reward eating to grow, even when tied in length.
                        # (Being small too long is the leading cause of starvation.)
                        s += 28
                    else:
                        s += 15
            elif margin >= 0 and c["food_dist"] < 5:
                # Only chase food when close and space is at least survivable
                s += max(0, 22 - c["food_dist"] * 3)
                if my_len < max_opp_len and c["eats"]:
                    s += 10
        # BIG-LEAD BRAKE: if we're already much longer than opponent and healthy,
        # avoid over-eating (leads to self-trap). Penalize food-chasing and eating.
        # my_len - max_opp_len >= 8 = commanding lead. Health > 40 = safe.
        lead = my_len - max_opp_len
        if lead >= 8 and my_health >= 40:
            # Suppress food-chase incentives; encourage NOT eating this turn.
            # Distance-food-dist matters less; penalize eating cells directly.
            if c["eats"]:
                s -= 20 + min(30, (lead - 8) * 3)  # up to -50 for extreme lead
            # Also penalize cells with very small food_dist when board is congested
            # (we want to keep space around us).
        elif c["eats"] and my_health < 90:
            if margin >= 3:
                s += 8
        # Early-game growth urgency: if we're tiny and can safely eat, do it.
        if small_urgent and c["eats"] and margin >= 3 and not c.get("h2h_death") and not c.get("h2h_tie"):
            s += 20
        # CRITICAL HEALTH: strongly bias toward food. Prevents wandering-to-death.
        # my_health decreases 1/turn; if food_dist > my_health, we cannot survive
        # even in a straight line. Prioritize the closest reachable food.
        if my_health <= 40 and c["food_dist"] is not None and margin >= 0:
            # Huge bonus scaled inversely by distance; overrides most space concerns.
            urgency = (45 - my_health)  # 5..45
            s += max(0, urgency * 3 - c["food_dist"] * 2)
            if c["eats"]:
                s += 45
        # DESPERATE HEALTH: at h<=15, food_dist must strictly decrease or we die.
        # Score DOMINATES all other considerations. Multiplicative penalty on distance.
        if my_health <= 15 and c["food_dist"] is not None and margin >= 0:
            # Enormous score gradient by food distance. This must beat territory/wall penalties.
            # A 1-step closer food = +100 points.
            s += max(0, 500 - c["food_dist"] * 100)
            if c["eats"]:
                s += 200
        # Unreachable food at desperate health = death sentence
        if my_health <= 15 and c["food_dist"] is None:
            s -= 300
        # If we're going to starve unless we eat, food_dist == None means bad direction
        if my_health <= 20 and c["food_dist"] is None:
            s -= 80
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
            # LATE-GAME (long snake) edge penalty: coiling risk grows with length.
            # We lose ~10% of games by spiraling into wall traps around length 15-25.
            if my_len >= 12:
                # Count how many of my body segments (head-side, first 8) are on ANY edge
                edge_body = sum(1 for seg in my_body[:8]
                                if seg[0]==0 or seg[0]==w-1 or seg[1]==0 or seg[1]==h-1)
                # If already have 3+ body segs near walls, extra penalty on more edge moves
                if edge_body >= 3:
                    s -= 5 + 2 * (my_len - 12)  # grows with length
                # Space-margin gated: if margin < 6 and long, edge is very risky
                margin_here = c["space"] - c["new_len"]
                if margin_here < 8 and my_len >= 15:
                    s -= 8
            # EARLY-GAME edge penalty: short snakes shouldn't skulk on walls unnecessarily.
            # (Wall-mirror trap risk is compounded before we've grown large enough to survive it.)
            if my_len <= 6:
                s -= 6
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
                s -= 80
            elif trap_risk:
                s -= 35  # shorter opp mirror; still risky (corner-death) but less severe
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
                s -= 8 * wall_segs  # discourage prolonged wall crawl
                # If also being chased/mirrored, extra penalty
                if trap_risk:
                    s -= 20 * wall_segs
            elif wall_segs >= 1 and trap_risk:
                s -= 15  # early: prevent getting sucked into wall chase
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
                s += 15  # STRONG reward escape from wall (was 6)
            elif dist_wall_after < dist_wall_before:
                if dist_wall_after == 0:
                    s -= 60  # was 25 - never enter wall when chased
                elif dist_wall_after == 1:
                    s -= 25  # was 10
                else:
                    s -= 8   # was 3
            elif dist_wall_after <= 1 and dist_wall_before <= 1:
                # Staying near wall with longer opp close -> stronger penalty
                s -= 12  # was 4
            elif dist_wall_after <= 2 and dist_wall_before <= 2:
                # Still uncomfortably close to wall
                s -= 3

        # MIRROR-TRAP detection: longer opp is exactly parallel to us near a wall.
        # If we're heading to a cell where opp is mirror-adjacent (perpendicular to wall)
        # AND opp is longer, this is a wall-chase setup.
        for oid_mt, info_mt in opp_head_moves.items():
            if info_mt["length"] < my_len:
                continue
            oh_mt = info_mt["head"]
            # Check for mirror geometry: same y (or x), opp within 1-2 of a wall on opposite side
            # (i.e., opp shadows us on parallel line near wall)
            if dist_wall_after <= 2:
                # If we're going to be near right/left wall, check y-mirror
                if cx <= 1 or cx >= w-2:
                    if abs(oh_mt[1] - cy) <= 2 and abs(oh_mt[0] - cx) <= 3:
                        s -= 12
                # near top/bottom wall, check x-mirror
                if cy <= 1 or cy >= h-2:
                    if abs(oh_mt[0] - cx) <= 2 and abs(oh_mt[1] - cy) <= 3:
                        s -= 12


        # ANTI-SPIRAL: detect coiling. If new head cell has 2+ own-body neighbors AND
        # is on/near a wall, we're likely spiraling into a self-trap.
        cxs, cys = c["cell"]
        my_body_set_for_check = set(my_body[:-1])  # tail vacates
        body_adj = 0
        for nb_dx, nb_dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nb_x, nb_y = cxs+nb_dx, cys+nb_dy
            if (nb_x, nb_y) in my_body_set_for_check:
                body_adj += 1
        dist_wall_this = min(cxs, cys, w-1-cxs, h-1-cys)
        if body_adj >= 2 and dist_wall_this <= 1 and my_len >= 10:
            # Heavy spiral risk near wall
            s -= 25 + 3 * body_adj
        elif body_adj >= 2 and my_len >= 12:
            # Spiral risk anywhere for long snake
            s -= 10
        # STRICT ANTI-TRAP: if new head has 3 own-body neighbors, only 1 exit exists
        # and next turn we'll likely be blocked. Very high risk of imminent death.
        # This catches self-coil corner traps (observed in losses r2 sim_43, sim_178).
        if body_adj >= 3:
            s -= 80
        # Count blocked-by-anything neighbors (own body + opp body + walls). If 3+, brittle.
        occ_check = occ_now  # opp body + own body, tails excluded
        blocked_neighbors = 0
        for nb_dx, nb_dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nb_x, nb_y = cxs+nb_dx, cys+nb_dy
            if not _in_bounds((nb_x, nb_y), w, h):
                blocked_neighbors += 1
            elif (nb_x, nb_y) in occ_check and (nb_x, nb_y) != my_body[-1]:
                # own or opp body (excluding my current tail which will vacate)
                blocked_neighbors += 1
        # 3 blocked neighbors = only 1 exit, we came from one of the blocked (my prev head).
        # After moving there, next turn we have at most 1-2 options; if we ate food, worse.
        if blocked_neighbors >= 3 and my_len >= 10:
            s -= 50  # near-imminent self-trap
        elif blocked_neighbors >= 3 and my_len >= 6:
            s -= 20

        # Second-order trap: even one step from a wall while opp mirrors, is risky
        # This especially matters when body is trailing along wall.
        # Check if my new body is aligned along the wall for 2+ segments AND opp of >= length is on inner row
        my_new_body_local = None  # placeholder; computed via c metadata

        # ANTI-COIL v2: aggressive anti-self-trap penalties for long snakes.
        # Losses show pattern: len>=13, edge/corner, body-coiled, then trapped.
        # Compute self-body density around new cell within radius 2.
        if my_len >= 12:
            body_set_r2 = set(my_body[:-1])
            close_body = 0
            for dx_ in range(-2, 3):
                for dy_ in range(-2, 3):
                    if dx_ == 0 and dy_ == 0: continue
                    if (cxs+dx_, cys+dy_) in body_set_r2:
                        close_body += 1
            # High density = coil risk
            if close_body >= 6:
                s -= 15 + (close_body - 6) * 3
            elif close_body >= 4:
                s -= 5

        # Space-per-length ratio: on 11x11 board (121 cells), if we occupy a whole quadrant
        # of space and it's smaller than our length, we WILL die. Penalize heavily.
        margin_final = c["space"] - c["new_len"]
        if my_len >= 10:
            # Long snake: require comfortable margin
            if margin_final < 3:
                s -= 30 + (3 - margin_final) * 15  # extremely bad
            elif margin_final < 6:
                s -= 15
            elif margin_final < 10:
                s -= 5


        # SOLO WALL-CRAWL / SELF-COIL: even with no opp near, long snake spiraling
        # into wall can self-trap (see sim_242: len=24 head at right wall, no opp nearby).
        # If moving to edge cell and I already have 3+ recent body segments on SAME edge, penalize.
        if my_len >= 14:
            cxw, cyw = cxs, cys
            on_edge_w = (cxw == 0 or cxw == w-1 or cyw == 0 or cyw == h-1)
            if on_edge_w:
                # Count how many of last 6 body segments are on THIS same edge
                same_edge_count = 0
                for seg in my_body[:6]:
                    if cxw == 0 and seg[0] == 0: same_edge_count += 1
                    elif cxw == w-1 and seg[0] == w-1: same_edge_count += 1
                    elif cyw == 0 and seg[1] == 0: same_edge_count += 1
                    elif cyw == h-1 and seg[1] == h-1: same_edge_count += 1
                if same_edge_count >= 3:
                    # We're already coiled along this edge - big penalty
                    s -= 12 + same_edge_count * 4
                elif same_edge_count >= 2:
                    s -= 6

        # HAMILTONIAN-STYLE space check: for very long snakes, prefer moves where
        # the tail-reachable space is much larger than my length (long-term survival).
        if my_len >= 15 and c["tail_reachable"]:
            # Deep look: is our new space significantly larger than our length?
            deep_margin = c["space"] - c["new_len"]
            if deep_margin >= 12:
                s += 6  # comfortable long-term survival
            elif deep_margin < 4:
                s -= 15  # even tail-reachable is not safe if tight

        # HARD CENTERING pressure when very long: prefer moves toward the geometric center
        # unless food is close and we need it. This breaks wall-crawl and spiral patterns.
        if my_len >= 15:
            center_x, center_y = (w-1)/2, (h-1)/2
            dist_center_before = abs(my_head[0]-center_x) + abs(my_head[1]-center_y)
            dist_center_after = abs(cxs-center_x) + abs(cys-center_y)
            if dist_center_after < dist_center_before:
                s += 4  # slight pull toward center
            elif dist_center_after > dist_center_before and dist_wall_this <= 2:
                s -= 3  # pushing further out toward wall

        return s

    candidates.sort(key=score, reverse=True)
    return {"move": candidates[0]["dir"]}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
