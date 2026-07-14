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

    # Time-aware flood fill. We BFS outward from the new head; a body segment
    # is only an obstacle while it is still there. My own tail (and the tails
    # of others) retreat over time, so a cell occupied by segment i (0=head)
    # of a snake of length L becomes free after (L - i) turns. This lets us
    # tell a survivable coil apart from a true trap (a coil we can follow our
    # own retreating tail through).
    # Build a map: cell -> earliest turn it becomes free (0 = free now).
    def _build_clear_times():
        clear = {}
        for s in snakes:
            body = [(seg["x"], seg["y"]) for seg in s["body"]]
            L = len(body)
            extra = 1 if s["health"] == 100 else 0  # just ate: tail lingers 1 turn
            for i, seg in enumerate(body):
                # segment i vacates after (L - i) steps (tail i=L-1 -> 1 step)
                free_at = (L - i) + extra
                if seg in clear:
                    clear[seg] = min(clear[seg], free_at)
                else:
                    clear[seg] = free_at
        return clear

    clear_times = _build_clear_times()

    my_tail = my_body[-1] if len(my_body) > 1 else None

    def _can_reach(start_cell, target):
        # Time-aware BFS: can we reach `target` from `start_cell`?
        from collections import deque
        if start_cell == target:
            return True
        seen = {start_cell}
        dq = deque([(start_cell, 1)])
        while dq:
            cur, d = dq.popleft()
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn == target:
                    return True
                if nn in seen or not in_bounds(nn):
                    continue
                ct = clear_times.get(nn)
                if ct is not None and ct > d:
                    continue
                seen.add(nn)
                dq.append((nn, d + 1))
        return False

    def flood_fill(start_cell, blocked_set, limit=None):
        # Distance-limited BFS respecting time-clearing of body cells.
        # A cell is enterable at distance d if it is in bounds and either not a
        # body cell, or its clear time <= d (the occupying segment has moved).
        from collections import deque
        seen = {start_cell}
        dq = deque([(start_cell, 1)])
        count = 0
        while dq:
            cur, d = dq.popleft()
            count += 1
            if limit and count >= limit:
                break
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn in seen or not in_bounds(nn):
                    continue
                ct = clear_times.get(nn)
                if ct is not None and ct > d:
                    continue  # still occupied when we would arrive
                seen.add(nn)
                dq.append((nn, d + 1))
        return count

    # Static flood-fill treating every current body cell as a permanent wall
    # (no tail retreat). This models the worst case (we/opponents just ate and
    # bodies don't shrink) and catches pockets that will seal us in as our body
    # grows -- the multi-turn wall-hug coil deaths seen vs a real opponent.
    static_blocked = set()
    for s in snakes:
        for seg in s["body"]:
            static_blocked.add((seg["x"], seg["y"]))

    def static_flood(start_cell, limit=None):
        from collections import deque
        seen = {start_cell}
        dq = deque([start_cell])
        count = 0
        while dq:
            cur = dq.popleft()
            count += 1
            if limit and count >= limit:
                break
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn in seen or not in_bounds(nn):
                    continue
                if nn in static_blocked:
                    continue
                seen.add(nn)
                dq.append(nn)
        return count

    # Standalone static flood from an arbitrary start with a caller-supplied
    # blocked set (used by the 2-ply self-coil lookahead which simulates our
    # body after a move). Same worst-case (no-retreat) model as static_flood.
    def _static_flood_from(start_cell, blocked, limit=None):
        from collections import deque
        seen = {start_cell}
        dq = deque([start_cell])
        count = 0
        while dq:
            cur = dq.popleft()
            count += 1
            if limit and count >= limit:
                break
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn in seen or not in_bounds(nn):
                    continue
                if nn in blocked:
                    continue
                seen.add(nn)
                dq.append(nn)
        return count

    def _region_and_tail(start_cell, blocked, tail_cell, limit=None):
        # Flood from start_cell (body-after-move as `blocked`). Returns
        # (region_size, tail_reachable). For a huge snake the true survival
        # guarantee is that its head can still reach its own tail cell (a
        # space-filling loop). We prefer moves that keep a large region AND
        # keep the tail reachable.
        from collections import deque
        seen = {start_cell}
        dq = deque([start_cell])
        count = 0
        tail_ok = (start_cell == tail_cell)
        while dq:
            cur = dq.popleft()
            count += 1
            if limit and count >= limit:
                # keep scanning for tail membership cheaply by breaking is fine
                pass
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if nn in seen or not in_bounds(nn):
                    continue
                if nn == tail_cell:
                    tail_ok = True
                if nn in blocked:
                    continue
                seen.add(nn)
                dq.append(nn)
        return count, tail_ok


    def _open_region_quality(start_cell, blocked, limit=None):
        # Flood from start_cell (body-after-move as `blocked`) and measure a
        # CHOKEPOINT-AWARE region size. Static/time-aware floods overcount space
        # reachable through 1-wide channels (a coil clears as the tail retreats),
        # which is why the bot serpentines into shrinking pockets and self-coils
        # (the dominant loss class vs cornelius/elon/tantilla/eremetic). Here we
        # penalize cells whose only in-region access is a narrow corridor: a cell
        # with <=1 free (non-blocked, in-bounds) neighbour contributes 0.35, a
        # cell with 2 free neighbours contributes 0.75, else 1.0. This yields a
        # much lower "quality" for a serpentine channel than for open room, so
        # the scorer prefers genuinely open moves and breaks coils earlier.
        from collections import deque
        seen = {start_cell}
        dq = deque([start_cell])
        quality = 0.0
        while dq:
            cur = dq.popleft()
            free_nbrs = 0
            for ddx, ddy in DIRS.values():
                nn = (cur[0] + ddx, cur[1] + ddy)
                if not in_bounds(nn) or nn in blocked:
                    continue
                free_nbrs += 1
                if nn in seen:
                    continue
                seen.add(nn)
                dq.append(nn)
            if free_nbrs <= 1:
                quality += 0.35
            elif free_nbrs == 2:
                quality += 0.75
            else:
                quality += 1.0
            if limit and len(seen) >= limit:
                break
        return quality

    # Opponent body cells (static, no retreat) for the 2-ply lookahead.
    opp_bodies_static = set()
    for s in opponents:
        for seg in s["body"]:
            opp_bodies_static.add((seg["x"], seg["y"]))

    # Build a blocked set for flood fill: bodies (excluding our tail which moves).
    # Anti-pin: when we are SHORTER than the nearest opponent, a longer snake
    # can pursue us and pin us to a wall/corner (round-1 crystal losses: sim_0,
    # sim_151, sim_194, sim_103, sim_238 were all head-to-head/pin deaths at high
    # health when we fled to an edge). In that situation strongly value center /
    # open room and avoid walls so we cannot be cut off.
    nearest_opp_len = 0
    nearest_opp_dist = 9999
    for s in opponents:
        oh = (s["body"][0]["x"], s["body"][0]["y"])
        d = _manhattan(head, oh)
        if d < nearest_opp_dist:
            nearest_opp_dist = d
            nearest_opp_len = s["length"]
    # Threatened = a longer/equal opponent is close enough to hunt us.
    being_hunted = (nearest_opp_len >= my_len) and (nearest_opp_dist <= 5)
    cx, cy = width // 2, height // 2

    # Growth strategy: the Xe opponent out-grows us and then wins head-to-heads
    # by being longer (round-0 losses: we were consistently 3-5 cells shorter).
    # Compute how badly we want food so we can actively pursue it (not just as a
    # tie-break). Strong pull when we are not clearly longer than every opponent.
    _food_cells = [(f["x"], f["y"]) for f in board["food"]]
    _max_ol = _max_opp_len(opponents)
    if my_health < 35:
        _food_weight = 4.0            # starving: prioritise reaching food
    elif my_len < _max_ol:
        # BEHIND on length -- flipez-crystal out-grows us early (avg gap 5.3)
        # then wins forced h2h. Grow AGGRESSIVELY to reach length parity.
        _behind = _max_ol - my_len
        _food_weight = 8.0 + min(_behind, 6) * 0.9   # 8.0..13.4
    elif my_len == _max_ol:
        _food_weight = 5.5            # tied: contest hard so flipez cannot pull ahead
    else:
        _food_weight = 0.6            # ahead: mild interest
    # DOMINANCE ANTI-COIL (fix vs pinky-snek sim_145 R1 loss): when we are
    # MUCH longer and healthy we do NOT need food. The mild 0.6 food pull was
    # dragging our head toward wall-adjacent food (bottom-row cluster), which
    # started a multi-turn wall coil that eventually sealed us in a single-escape
    # corridor while we dominated (len 24 vs 13). Zero the food pull so we prefer
    # open interior space and never coil toward edge food when we're winning big.
    if my_len > _max_ol + 4 and my_health >= 40:
        _food_weight = 0.0
    # BATTLEJAKE FIX (R0: 36/37 losses were self-coils while LONGER, mostly on
    # edges, at high health, lengths 13-35 -- NOT the huge-dominance regime).
    # Root cause: in the near-equal band (ml only 1-6 > ol) food racing pulled
    # our head toward EDGE/corner food (e.g. sim_186 t190: chased food at (8,0)/
    # (10,0) right along the bottom wall into the (10,3) dead-end death-march).
    # When we are AT/ABOVE parity and healthy and not hunted, we do NOT need to
    # race edge food; suppress the edge-food lure so we prefer open interior room.
    # Only suppress edge food when STRICTLY LONGER: when TIED (esp. the opening)
    # we MUST grab close spawn-side edge food to keep pace with frank, who eats
    # its adjacent spawn food on turn 1-2. Suppressing edge food when tied made
    # us walk past close edge food toward center food and permanently fall behind.
    _suppress_edge_food = (my_len > _max_ol and my_health >= 40)
    # Distance to food from current head (baseline) for a directional bonus.

    def score_candidate(cand):
        name, nc, lose_h2h, h2h_len = cand
        # Time-aware reachable space from the new head cell.
        space = flood_fill(nc, None, limit=width * height)
        # Growth-aware (static) space: worst case where no bodies retreat.
        sspace = static_flood(nc, limit=width * height)

        score = 0.0
        # Heavily penalize potential losing head-to-heads.
        if lose_h2h:
            score -= 1000.0
        else:
            # winning/no h2h - if enemy could be there and we're longer, chance to kill.
            if h2h_len > 0:
                score += 30.0

        # Space is critical: reward available room. Need at least my_len space.
        score += space * 10.0
        if space < my_len:
            score -= (my_len - space) * 100.0
        # Extra danger: a very tight pocket (< half my length) is near-fatal.
        if space < my_len // 2 + 1:
            score -= 300.0
        # Growth-aware pocket: if the static (no-retreat) reachable region is
        # smaller than our length, this cell leads into a region that will seal
        # us in as bodies grow. Penalize proportionally -- this is the key fix
        # for the multi-turn wall-hug coil deaths (we were LONGER yet trapped).
        if sspace < my_len:
            score -= (my_len - sspace) * 16.0
        # Truly tiny static region = crawling into a pocket that seals us in as
        # bodies grow (sim_163: LONGER 15 vs 7 yet coiled into top-left corner).
        if sspace <= 4:
            score -= 400.0
        elif sspace <= 8:
            score -= 140.0
        elif sspace <= 12:
            score -= 40.0
        # Tail reachability: if we can reach our own tail cell from the new
        # head (time-aware), we can always chase our tail and never truly trap.
        # This is the key anti-coil heuristic that prevents sealing ourselves in.
        if my_tail is not None and _can_reach(nc, my_tail):
            score += 200.0
        else:
            score -= 200.0

        # UNIVERSAL TAIL-REACHABLE-REGION (fix vs jackisherwood__battlesnake-elon
        # R0 losses: 10 DOMINANCE / near-equal-length SELF-COILs -- ml 21-32 vs
        # ol 19-30, high health, boxed in, mostly INTERIOR). The strong dominance
        # tail-following block only fired at my_len > _max_ol+3, so the NEAR-EQUAL
        # length band (ml~ol) was uncovered and only had the time-aware checks,
        # which OVERCOUNT through 1-wide channels and via tail retreat. Here we use
        # the STATIC (body-after-move as permanent walls) region + true tail
        # reachability -- the real survival metric -- for EVERY length band. Gated
        # to not-being-hunted + healthy so it never interferes with h2h combat or
        # starving-food logic. This steers us off a forming coil (interior OR wall)
        # many turns before it seals, independent of length.
        if (not being_hunted) and my_health >= 30 and my_tail is not None \
                and len(my_body) >= 2:
            _eats_u = nc in _food_cells  # landing on food: tail does NOT retreat
            if _eats_u:
                _occ_u = set(my_body)         # full body stays (grows by one)
                _occ_u.add(nc)
                _future_tail_u = my_body[-1]  # tail stays put this turn
            else:
                _occ_u = set(my_body[:-1])    # body after move: old tail vacates
                _occ_u.add(nc)
                _future_tail_u = my_body[-2]  # cell the tail retreats to
            _reg_u, _tail_ok_u = _region_and_tail(
                nc, _occ_u, _future_tail_u, limit=None)
            if _tail_ok_u:
                score += 90.0             # stays on a survivable space-filling loop
            else:
                score -= 500.0            # severs the loop -> multi-turn coil death
            # Prefer moves that keep a static region at least as large as we are;
            # a region smaller than our length is a pocket that seals as we grow.
            if _reg_u < my_len:
                score -= (my_len - _reg_u) * 14.0
            if _reg_u <= 4:
                score -= 250.0
            # CHOKEPOINT-AWARE OPEN-REGION QUALITY (fix vs cornelius/elon/tantilla
            # self-coils): static/time-aware floods overcount space reachable
            # through 1-wide channels, so a serpentine coil looks "big" while it
            # is actually a shrinking corridor. Reward moves whose reachable
            # region is genuinely OPEN (few chokepoints) and penalize corridor-
            # heavy regions. Only meaningful when the quality falls short of our
            # length (we need room to keep moving without sealing in).
            _q_u = _open_region_quality(nc, _occ_u, limit=None)
            score += _q_u * 2.0
            if _q_u < my_len:
                score -= (my_len - _q_u) * 8.0
            # NEAR-EQUAL-LENGTH ANTI-COIL (fix vs jackisherwood__battlesnake-elon
            # R1: 15 losses were near-equal-length INTERIOR self-coils, ml~ol,
            # high health, boxed in via a multi-turn serpentine weave -- e.g.
            # sim_131 t253-259 we snaked into a shrinking 8x pocket and sealed).
            # The strong anti-serpentine + 2-ply static lookahead only fired in
            # the DOMINANCE band (my_len > _max_ol+3). Apply a milder version to
            # the NEAR-EQUAL band (my_len <= _max_ol+3) that the universal
            # tail-region term alone did not catch. Gated to not-hunted + healthy
            # so it never interferes with h2h combat or food when it matters.
            if my_len <= _max_ol + 3:
                # anti-serpentine: snugging 2+ own body cells = weaving a coil.
                _own_ne = set(my_body[:-1])
                _adj_ne = 0
                for _anx, _any in DIRS.values():
                    if (nc[0] + _anx, nc[1] + _any) in _own_ne:
                        _adj_ne += 1
                if _adj_ne >= 2:
                    score -= (_adj_ne - 1) * 45.0
                elif _adj_ne == 1:
                    score -= 12.0
                # tail-following: prefer moves that keep us near our own tail
                # (the survivable space-filling loop) over drifting inward.
                if my_tail is not None:
                    _tdn = abs(nc[0] - my_tail[0]) + abs(nc[1] - my_tail[1])
                    score -= _tdn * 5.0
                # 2-ply static lookahead: best no-retreat region reachable from a
                # safe neighbour of nc; if even the best is < our length we are
                # funneling into a shrinking pocket 2 moves ahead (the coil).
                # Use a generous limit so a truly open region is distinguished
                # from a shrinking pocket even for a longer near-equal snake.
                if nc in _food_cells:
                    _occ2n = set(my_body)
                else:
                    _occ2n = set(my_body[:-1])
                _occ2n.add(nc)
                _best2n = 0
                for _b2xn, _b2yn in DIRS.values():
                    _nn2n = (nc[0] + _b2xn, nc[1] + _b2yn)
                    if not in_bounds(_nn2n) or _nn2n in _occ2n:
                        continue
                    _s2n = _static_flood_from(_nn2n, _occ2n, limit=my_len + 12)
                    if _s2n > _best2n:
                        _best2n = _s2n
                if _best2n < my_len:
                    score -= (my_len - _best2n) * 16.0
                if _best2n <= 4:
                    score -= 300.0

        # Escape-count: how many of the new head's neighbours are still safe
        # to enter next turn (in bounds, not a body segment now, not a losing
        # head-to-head)?  Moving into a cell with 0-1 escapes is how we walked
        # into wall traps in round 1 (sim_152 bottom-row chase, sim_235 coil).
        escapes = 0
        for ex, ey in DIRS.values():
            en = (nc[0] + ex, nc[1] + ey)
            if not in_bounds(en):
                continue
            if en in occupied:
                continue
            el = enemy_next.get(en, 0)
            if el >= my_len:
                continue  # a cell an equal/longer enemy could take = not a safe escape
            escapes += 1
        if escapes == 0:
            score -= 400.0   # dead-end unless our tail retreat saves us
        elif escapes == 1:
            score -= 40.0    # single escape = risky corridor

        # DOMINANCE CORRIDOR AVOIDANCE (fix vs coreyja__eremetic-eric R0 losses):
        # 14 losses were LONG endgames (300-565 turns) where we grew HUGE (len
        # 37-61 vs opp 7-12) at HIGH health, then crawled a WALL corridor into a
        # corner and sealed ourselves (e.g. sim_129: coiled the x=9 column then
        # ran the x=10 wall down into (0,0)). When we are much longer than the
        # opponent, open space is at a premium: a low-escape cell is far more
        # dangerous than the flat -40 (which is dwarfed by space*10 for a huge
        # snake). Scale the corridor penalty with our length when dominant so we
        # break out of a forming wall coil MANY turns before it seals, and pick
        # the open-interior move over continuing down the wall. Gated to
        # not-hunted + healthy so it never blocks fighting/food when it matters.
        if (not being_hunted) and my_health >= 30 and my_len > _max_ol + 3:
            if escapes <= 1:
                score -= (my_len - 6) * 4.0
            # Also prefer maximizing our own reachable room when dominant: a
            # move into a smaller time-aware region is a step toward a coil.
            score += space * 3.0
            # DOMINANCE TAIL-FOLLOWING (fix vs coreyja__eremetic-eric R1 losses:
            # 19 DOMINANCE SELF-COILs at len 29-62). A huge snake survives
            # indefinitely only by CHASING ITS OWN TAIL (a space-filling loop).
            # The time-aware flood OVERCOUNTS through 1-wide channels so space*3
            # lets us serpentine into a shrinking pocket. Instead, when HUGE,
            # reward moving CLOSER to our own tail cell (the classic survival
            # loop) and reward keeping the largest STATIC (no-retreat) region.
            if my_tail is not None:
                _td = abs(nc[0] - my_tail[0]) + abs(nc[1] - my_tail[1])
                score -= _td * 28.0
            score += sspace * 8.0
            # TAIL-REACHABLE REGION (huge-snake space-filling survival): from the
            # new head, flood the board treating our body-after-move as walls and
            # check whether we can still reach our OWN TAIL (which will retreat).
            # A move that keeps the tail reachable is a move that keeps us on a
            # survivable space-filling loop; a move that severs it is a step into
            # a sealing pocket. This is the true survival metric a huge snake
            # needs (the time-aware/static floods overcount through 1-wide
            # channels and via tail retreat, so they miss the multi-turn coil).
            if my_tail is not None and len(my_body) >= 2:
                if nc in _food_cells:          # eating: tail does NOT retreat
                    _occ_tr = set(my_body)
                    _occ_tr.add(nc)
                    _future_tail = my_body[-1]
                else:
                    _occ_tr = set(my_body[:-1])   # body after move: drop old tail
                    _occ_tr.add(nc)
                    _future_tail = my_body[-2]     # the cell the tail vacates to
                _reg, _tail_ok = _region_and_tail(
                    nc, _occ_tr, _future_tail, limit=None)
                if _tail_ok:
                    score += 120.0             # stays on a survivable loop
                else:
                    score -= 1500.0            # severs the loop -> coil death
                # also reward a bigger reachable region (open room, no channel)
                score += _reg * 16.0
            # ANTI-SERPENTINE: snugging the head against 2+ of our own body cells
            # is weaving a coil that fills a sub-length pocket over many turns
            # (sim_12/sim_141 interior coils). Penalize hard, scaled with length.
            _own_d = set(my_body[:-1])
            _adj_d = 0
            for _adx, _ady in DIRS.values():
                if (nc[0] + _adx, nc[1] + _ady) in _own_d:
                    _adj_d += 1
            if _adj_d >= 2:
                score -= (_adj_d - 1) * 60.0
            elif _adj_d == 1:
                score -= 20.0
            # 2-PLY STATIC LOOKAHEAD when HUGE: after moving to nc (body grown by
            # one, tail retreated), look at the best static (no-retreat) region
            # reachable from any safe neighbour of nc. If even the BEST follow-up
            # region is smaller than our length, this move funnels us into a
            # shrinking pocket 2 moves ahead -- the exact multi-turn interior coil.
            if nc in _food_cells:
                _occ2 = set(my_body)
            else:
                _occ2 = set(my_body[:-1])
            _occ2.add(nc)
            _best2 = 0
            for _b2x, _b2y in DIRS.values():
                _nn2 = (nc[0] + _b2x, nc[1] + _b2y)
                if not in_bounds(_nn2) or _nn2 in _occ2:
                    continue
                _s2v = _static_flood_from(_nn2, _occ2, limit=my_len + 4)
                if _s2v > _best2:
                    _best2 = _s2v
            if _best2 < my_len:
                score -= (my_len - _best2) * 18.0
            if _best2 <= 4:
                score -= 300.0

        # PARALLEL-SHADOW WALL TRAP (rdbrck__btas round-0 losses sim_156/177):
        # Even when we are MUCH LONGER, the opponent shadows us along the OUTER
        # wall and seals our only exit with its body -- we die on the wall while
        # dominating (being_hunted was False because we were longer, so anti-pin
        # never fired). Fix: when ANY opponent head is close (<=4) and our new
        # head lands on an edge, penalize it -- pull us off the wall into open
        # board where a shadow cannot cut us off. Applies regardless of length.
        if nearest_opp_dist <= 4:
            _on_edge_s = (nc[0] == 0 or nc[0] == width - 1
                          or nc[1] == 0 or nc[1] == height - 1)
            if _on_edge_s:
                score -= 45.0
                # heading INTO a corner with a close opponent = near-certain seal
                if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                    score -= 120.0
                # extra: if this edge cell has <=1 non-losing escape it is a
                # death-march down the wall against a shadowing snake.
                if escapes <= 1:
                    score -= 250.0

        # 1-PLY LOOKAHEAD SPACE (anti multi-turn coil, sim_238 round-1 loss):
        # A single-turn flood can look fine while our body spirals into a loop
        # that seals a turn or two later (we were LONGER 13v10 at 94hp yet all 4
        # neighbours got blocked). Here: after moving to nc, look at nc's safe
        # neighbours and take the BEST time-aware flood from any of them. If even
        # our best follow-up cell has little room, we are about to be sealed.
        best_next = 0
        for ex, ey in DIRS.values():
            en = (nc[0] + ex, nc[1] + ey)
            if not in_bounds(en) or en in occupied:
                continue
            el = enemy_next.get(en, 0)
            if el >= my_len:
                continue
            ns = flood_fill(en, None, limit=my_len + 2)
            if ns > best_next:
                best_next = ns
        if best_next < my_len:
            score -= (my_len - best_next) * 12.0
        if best_next <= 2:
            score -= 300.0   # next move leads into a near-dead pocket

        # Edge/wall penalty: hugging walls is what let the opponent cut us off
        # along the bottom row (sim_152) and let us coil into a corner (sim_235).
        # Only a SMALL nudge toward the interior, and disabled when hungry so we
        # can still reach food located on an edge/corner (solo starve otherwise).
        if my_health >= 25:
            on_edge = (nc[0] == 0 or nc[0] == width - 1
                       or nc[1] == 0 or nc[1] == height - 1)
            if on_edge:
                score -= 8.0
                # corner is worse (only two exits at most)
                if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                    score -= 16.0

        # Anti-pin (only when being hunted by a longer/equal opponent nearby):
        # prefer cells toward the center and heavily penalize edges/corners so we
        # keep escape routes and cannot be sealed against a wall.
        if being_hunted:
            dist_center = abs(nc[0] - cx) + abs(nc[1] - cy)
            score -= dist_center * 4.0
            on_edge2 = (nc[0] == 0 or nc[0] == width - 1
                        or nc[1] == 0 or nc[1] == height - 1)
            if on_edge2:
                score -= 35.0
                if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                    # Entering a CORNER while a longer/equal snake hunts us is
                    # almost always death (sim_40/102/23/110: pinned at (0,0),
                    # (10,0), (1,0)). Make it prohibitive unless there is truly
                    # no other option (the -1000 losing-h2h dominates anyway).
                    score -= 250.0
            # Being pinned: if the pursuing opponent is BEHIND us relative to
            # the wall we're heading toward, moving further along/into the wall
            # lets it seal us. Penalize cells whose safe-escape count is low
            # extra hard while hunted (a corridor along a wall is a death march
            # against a longer chaser).
            if escapes <= 1:
                score -= 120.0

        # Hazard avoidance: entering a hazard costs 14hp/turn. Penalize unless
        # we have plenty of health or it's needed. Strong penalty when low.
        if nc in hazards:
            # Cost of a hazard step is ~14hp. Penalize proportionally so we
            # avoid it when healthy but can still chase essential food when
            # starving (food logic breaks ties among equal-scored moves).
            score -= 60.0

        # Food attraction: reward moves that get us closer to the nearest food,
        # scaled by how much we want to grow. Only apply when the cell is safe
        # (space is adequate) so we never dive into a trap for food.
        if _food_cells and space >= my_len:
            _fw = _food_weight
            # When a longer/equal opponent is hunting us, do NOT let food lure
            # us into edge/corner cells where we can be pinned (ccsnake losses
            # sim_103 etc: we chased corner food while shorter and got sealed).
            _on_edge_f = (nc[0] == 0 or nc[0] == width - 1
                          or nc[1] == 0 or nc[1] == height - 1)
            if being_hunted and _on_edge_f:
                _fw = 0.0
            # vs TheApX__hungry (R1: 37/39 losses we were SHORTER, fell behind
            # turns 5-10). Traced sim_9 t8: we were TIED (len4) with food at (5,5)
            # a 2-2 TIE race vs the opp -- arriving together = equal-length mutual
            # death, correctly avoided, but then we had no clear alternate target
            # and wandered while the opp grabbed (5,5) then more food uncontested.
            # FIX: when TIED-or-SHORTER, exclude food we can only reach in a
            # LOSING/MUTUAL-death tie race (opp arrives <= us AND opp is >= our
            # length) from the nearest-food pull, so our head redirects toward an
            # alternate food we can actually win. Keep such food if it is the ONLY
            # food (fall back to the plain nearest).
            _cand_food = _food_cells
            if my_len <= _max_ol:
                _winnable = []
                for f in _food_cells:
                    _mf = _manhattan(nc, f)
                    _of = 999
                    for opp in opponents:
                        oh = (opp["body"][0]["x"], opp["body"][0]["y"])
                        _ol2 = len(opp["body"])
                        _od = _manhattan(oh, f)
                        # a food is un-winnable if a >= length opp reaches it no
                        # later than us (tie => mutual death, sooner => opp eats it)
                        if _od <= _mf and _ol2 >= my_len:
                            _of = min(_of, _od)
                    if _of == 999:
                        _winnable.append(f)
                if _winnable:
                    _cand_food = _winnable
            nd = min(_manhattan(nc, f) for f in _cand_food)
            score -= nd * _fw
            if nd == 0 and not (being_hunted and _on_edge_f):
                score += 40.0   # landing on food = growth, extra reward when behind

            # FOOD RACING (fix vs jump-flooding, sim_40): when we are NOT clearly
            # longer, we must GROW to win/avoid head-to-heads. In the losses we
            # fled from contested food and wall-hugged at len 4 until pinned.
            # Here: strongly reward moving toward any food we can reach STRICTLY
            # before the nearest opponent (an uncontested race we win). This is
            # safe (opp can't contest it) and keeps us at length parity. We even
            # allow edge food if we clearly win the race and it isn't a deep
            # pin-corner (escapes >= 2), so we stop starving on the walls.
            if my_len <= _max_ol + 1 and not lose_h2h:
                _behind_now = my_len < _max_ol
                for f in _food_cells:
                    my_fd = _manhattan(nc, f)
                    opp_fd = 999
                    for opp in opponents:
                        oh = (opp["body"][0]["x"], opp["body"][0]["y"])
                        od = _manhattan(oh, f)
                        if od < opp_fd:
                            opp_fd = od
                    # When BEHIND on length we MUST grow to reach parity, so
                    # contest any food we win OR tie the race for (my_fd<=opp_fd);
                    # when even/ahead only take food we clearly win (my_fd<opp_fd-1).
                    _aggro = my_len <= _max_ol
                    # vs beames (kentmacdonald2): 96% of losses we were SHORTER;
                    # beames slowly out-grows us in the opening then pins us. When
                    # CLEARLY BEHIND (behind by 2+), also contest food we lose the
                    # race by 1 cell -- but ONLY if it is a SAFE landing (escapes>=2,
                    # not a corner) so we never dive into a pin for food. This closes
                    # the length gap so we win forced h2h contacts.
                    _far_behind = my_len < _max_ol - 1
                    if _aggro:
                        _win_race = (my_fd <= opp_fd)
                        # vs beames (kentmacdonald2 R1): 46/46 losses we were
                        # SHORTER; beames slowly out-grows us in turns 6-10 then
                        # wins length contacts (traced sim_150: opp ate contested
                        # center food then a 2nd food while we walked to a corner).
                        # Widen the stretch race: whenever BEHIND (by 1+), contest
                        # food we lose the race by 1 cell IF it's a safe landing
                        # (escapes>=2), so we keep pace even when only 1 short.
                        _behind2 = my_len < _max_ol - 1
                        _sm = 2 if _behind2 else 1  # vs TheApX__hungry (out-grows us): when clearly behind, contest food we lose by up to 2 cells (safe landings only)
                        _stretch = (_behind_now and my_fd <= opp_fd + _sm and escapes >= 2)
                    else:
                        _win_race = (my_fd < opp_fd - 1)
                        _stretch = False
                    if _win_race or _stretch:
                        _corner_f = ((f[0] in (0, width - 1))
                                     and (f[1] in (0, height - 1)))
                        if _corner_f and escapes <= 1:
                            continue  # deep corner pin risk, skip
                        _edge_f = (f[0] in (0, width - 1)
                                   or f[1] in (0, height - 1))
                        _nc_edge = (nc[0] == 0 or nc[0] == width - 1
                                    or nc[1] == 0 or nc[1] == height - 1)
                        # Don't race EDGE food into a wall corridor when we're at
                        # parity+ and healthy: it starts the wall self-coil that
                        # is 36/37 of our battlejake losses. Skip the reward AND
                        # penalize entering an edge cell with a low escape count.
                        if _suppress_edge_food and _edge_f:
                            if _nc_edge and escapes <= 2:
                                score -= 45.0
                            continue
                        # reward getting closer; big bonus for landing on it
                        _race_w = 5.0 if _aggro else 3.0
                        # ensure a positive pull even on a 1-cell-losing stretch race
                        _margin = max(opp_fd - my_fd + 1, 1)
                        score += _margin * _race_w
                        if my_fd == 0:
                            score += 55.0

        # NEUTRAL-ZONE WALL AVOIDANCE (fix vs amphibious-arthur sim_124/38/85):
        # In several losses we were roughly EVEN length (e.g. len5 vs 4) and got
        # onto a wall then coiled into a corner. Neither anti-pin (needs opp>=us)
        # NOR the winning anti-wall-coil (needs my_len>max_opp+1) fired in that
        # neutral band, so only the mild -8 edge nudge applied and the wall cell
        # still scored best. Add a moderate center-pull + edge penalty whenever we
        # are AT LEAST tied on length, healthy, and not being hunted. This keeps us
        # off walls in the even-length band without touching the hungry/food logic.
        if (not being_hunted) and my_health >= 30 and my_len >= _max_ol:
            # OPENING GROWTH (fix vs famished-frank R1: 58/60 losses we were
            # SHORTER; frank eats its adjacent spawn food on turn 1-2 while we
            # walked toward CENTER food and fell behind by turn 2 and never
            # recovered). When exactly TIED and still short (early game, len<=8)
            # the wall-coil risk is ~zero, so SOFTEN this center-pull/edge penalty
            # so close spawn-side edge food (2 cells away at spawn) wins over
            # center food. Longer snakes keep the full anti-wall-coil steering.
            _early_tied = (my_len == _max_ol and my_len <= 8)
            _dc = abs(nc[0] - cx) + abs(nc[1] - cy)
            if _early_tied:
                score -= _dc * 0.5
            else:
                score -= _dc * 2.5
            _on_edge_n = (nc[0] == 0 or nc[0] == width - 1
                          or nc[1] == 0 or nc[1] == height - 1)
            if _on_edge_n:
                score -= (6.0 if _early_tied else 25.0)
                if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                    score -= (15.0 if _early_tied else 50.0)

        # GENERAL ANTI-WALL-COIL (fix vs OliverMKing__astar-snake, round-0):
        # 47/79 losses were multi-turn self-coils/wall-hugs where we ran up a
        # wall (x=0/10) or along the top/bottom row and coiled into a corner at
        # HIGH health while roughly EQUAL or even SHORTER (e.g. sim_101 len27
        # went up right wall then top wall; sim_102 len27v28 up left wall into
        # (0,0)). In those the opponent was FAR (not being_hunted) and we were
        # not clearly longer, so NEITHER the neutral-zone (needs my_len>=_max_ol)
        # NOR the winning anti-wall-coil fired. This fires whenever we are simply
        # healthy and not being hunted, independent of length, to keep us off
        # walls and detect a forming coil via a 2-ply STATIC (no-retreat) flood.
        if (not being_hunted) and my_health >= 25:
            # GROWTH-PRIORITY (fix vs coreyja__famished-frank R0): when we are
            # BEHIND on length the opponent out-grows us early then pins us in
            # forced h2h/self-coil (48/51 losses we were SHORTER, stuck at len
            # 4-6 by turn 30 while frank hit 7-9). The center-pull + edge penalty
            # here was overwhelming the food-racing reward, so we walked PAST
            # winnable edge food (sim_9 t14: food (8,10) ignored) and stayed
            # short. A short snake has ~no self-coil risk, so soften the anti-
            # wall-coil steering while behind so growth (food racing) wins.
            _short = my_len < _max_ol
            _cp = 0.6 if _short else 3.0
            _ep = 6.0 if _short else 30.0
            _cop = 15.0 if _short else 70.0
            _dcg = abs(nc[0] - cx) + abs(nc[1] - cy)
            score -= _dcg * _cp
            _on_edge_g = (nc[0] == 0 or nc[0] == width - 1
                          or nc[1] == 0 or nc[1] == height - 1)
            if _on_edge_g:
                score -= _ep
                if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                    score -= _cop
            # 2-ply static-space: does the best 2-step no-retreat region stay
            # large enough for our body? Catches the coil BEFORE it seals.
            _body_g = set(my_body)
            if my_body:
                _body_g.discard(my_body[-1])   # tail retreats
            _occ_g = _body_g | opp_bodies_static
            _best2g = 0
            for _gdx, _gdy in DIRS.values():
                _gn = (nc[0] + _gdx, nc[1] + _gdy)
                if not in_bounds(_gn) or _gn in _occ_g or _gn == nc:
                    continue
                if enemy_next.get(_gn, 0) >= my_len:
                    continue
                _gs = _static_flood_from(_gn, _occ_g, limit=my_len + 3)
                if _gs > _best2g:
                    _best2g = _gs
            if _best2g < my_len:
                score -= (my_len - _best2g) * 12.0
            if _best2g <= 3:
                score -= 320.0
            # SELF-ADJACENCY anti-coil (fix vs nbw-ruby R0 losses sim_16/139:
            # multi-turn serpentine self-coils in the EQUAL-length band where the
            # winning anti-coil never fired). Discourage snugging the new head
            # against our own body, which is how a weaving coil builds up before
            # it seals. Applies whenever not-hunted+healthy, independent of length.
            _own_body_g = set(my_body[:-1])
            _adj_g = 0
            for _agx, _agy in DIRS.values():
                if (nc[0] + _agx, nc[1] + _agy) in _own_body_g:
                    _adj_g += 1
            if _adj_g >= 2:
                score -= (_adj_g - 1) * 14.0
            elif _adj_g == 1:
                # Even a single self-adjacency in the not-hunted band nudges us
                # toward inward-turning spiral coils (nbw-ruby R1 losses sim_50/73:
                # interior self-coils where each step touched 1 own body cell and
                # slowly sealed a pocket). A small penalty prefers straighter,
                # outward moves and breaks the spiral before it forms.
                score -= 6.0

        # Anti-coil: when winning (clearly longer) and safe, penalize moves that
        # snug the new head against our own body. Tight self-adjacency in open
        # space builds multi-turn coils that eventually seal us in even while we
        # dominate (sim_18: len9v6, sim_231: len18v5 -- both self-coil deaths).
        if (not being_hunted) and my_len > _max_opp_len(opponents) + 1:
            own_body = set(my_body[:-1])
            adj_own = 0
            for ax, ay in DIRS.values():
                if (nc[0] + ax, nc[1] + ay) in own_body:
                    adj_own += 1
            score -= adj_own * 22.0

            # ANTI-WALL-COIL (bob round-1 losses sim_201/206/225/4): when we are
            # clearly longer and healthy we kept crawling along walls into corners
            # and sealing ourselves in over many turns, even while dominating.
            # Static flood stays large on a wall (tail retreats), so the previous
            # small -8 edge nudge wasn't enough. When winning + healthy, pull
            # toward the interior and strongly avoid edges/corners.
            if my_health >= 30:
                dist_center = abs(nc[0] - cx) + abs(nc[1] - cy)
                score -= dist_center * 5.0
                _on_edge_w = (nc[0] == 0 or nc[0] == width - 1
                              or nc[1] == 0 or nc[1] == height - 1)
                if _on_edge_w:
                    score -= 55.0
                    if (nc[0] in (0, width - 1)) and (nc[1] in (0, height - 1)):
                        score -= 110.0

            # 2-PLY STATIC-SPACE LOOKAHEAD (anti multi-turn self-coil, sim_116):
            # When we dominate we still spiral our own body inward: each single
            # move looks fine (tail retreats -> time-aware flood stays large) but
            # two moves later the pocket seals. Here, after moving to nc (head=nc,
            # tail retreated), simulate our body and for each safe follow-up cell
            # compute the STATIC (no-retreat) flood; take the BEST. If even our
            # best two-step static region is smaller than our length, this move
            # is steering us into a coil that will seal -> penalize. This picks
            # the OPEN-board escape over the food-pocket the center-pull favored.
            body_after = set(my_body)
            if my_body:
                body_after.discard(my_body[-1])  # tail retreats
            body_after.add(nc)
            body_after.discard(nc)  # nc is the new head, treated as start below
            occ_after = body_after | opp_bodies_static
            best2 = 0
            for _ndx, _ndy in DIRS.values():
                _nn = (nc[0] + _ndx, nc[1] + _ndy)
                if not in_bounds(_nn):
                    continue
                if _nn in occ_after or _nn == nc:
                    continue
                if enemy_next.get(_nn, 0) >= my_len:
                    continue
                _s2 = _static_flood_from(_nn, occ_after, limit=my_len + 3)
                if _s2 > best2:
                    best2 = _s2
            if best2 < my_len:
                score -= (my_len - best2) * 14.0
            if best2 <= 3:
                score -= 350.0

        # 2-PLY PIN LOOKAHEAD (the key fix vs jump-flooding, sim_141/92/232):
        # We repeatedly died by a longer pursuer cutting off our escapes so that
        # a turn later our ONLY move was a losing head-to-head into the corner.
        # 1-ply escape-count misses this because the opponent hasn't moved yet.
        # Here: after we move to nc, consider the hunting opponent's next moves;
        # for its WORST-case (for us) move, count how many of OUR moves-from-nc
        # stay safe (in bounds, not a body now, not a losing head-to-head vs the
        # opponent's projected new head). If that worst-case count is 0 or 1 we
        # are about to be pinned -> penalize so we steer away 1-2 turns earlier.
        if being_hunted and opponents:
            # nearest hunting opponent (longer/equal, close)
            worst_safe = 99
            for opp in opponents:
                oh = (opp["body"][0]["x"], opp["body"][0]["y"])
                olen = opp["length"]
                if olen < my_len:
                    continue  # only longer/equal snakes can win an h2h vs us
                if _manhattan(nc, oh) > 4:
                    continue
                opp_body = set((seg["x"], seg["y"]) for seg in opp["body"][:-1])
                # candidate opponent next-head positions
                opp_moves = []
                for odx, ody in DIRS.values():
                    onc = (oh[0] + odx, oh[1] + ody)
                    if not in_bounds(onc):
                        continue
                    if onc in opp_body:
                        continue
                    opp_moves.append(onc)
                if not opp_moves:
                    continue
                for onh in opp_moves:
                    # our body after moving to nc: head=nc, tail retreats (assume
                    # no growth so tail cell frees). Our old body minus tail.
                    our_after = set(occupied)
                    # our tail will move off unless we just ate; approximate: tail free
                    if my_body:
                        tail_cell = my_body[-1]
                        our_after.discard(tail_cell)
                    our_after.add(head)  # our old head becomes body
                    safe_next = 0
                    for ndx, ndy in DIRS.values():
                        nn = (nc[0] + ndx, nc[1] + ndy)
                        if not in_bounds(nn):
                            continue
                        if nn in our_after:
                            continue
                        # opponent's projected new head at onh: adjacent cells are
                        # cells it could h2h us on the following turn. If nn == onh
                        # that's an immediate losing h2h (opp longer/equal).
                        if nn == onh:
                            continue
                        # nn adjacent to onh -> opponent could also enter -> losing h2h
                        if abs(nn[0] - onh[0]) + abs(nn[1] - onh[1]) == 1 and olen >= my_len:
                            continue
                        # also avoid cells other enemies can take
                        if enemy_next.get(nn, 0) >= my_len:
                            continue
                        safe_next += 1
                    if safe_next < worst_safe:
                        worst_safe = safe_next
            if worst_safe == 0:
                score -= 500.0   # about to be pinned into a forced losing h2h
            elif worst_safe == 1:
                score -= 120.0   # only one escape after opp's best cut

        # OFFENSIVE SPACE-DENIAL (fix vs OliverMKing__astar-snake): when we are
        # clearly longer and healthy, actively finish the kill by keeping the
        # opponent confined to a SMALL reachable region. Analysis of round-1
        # losses (e.g. sim_10, 430 turns) showed we repeatedly TRAPPED the
        # opponent (their space dropped to 2-10) but let them ESCAPE and later
        # got outmaneuvered in a 400+ turn endgame we then LOST. Rewarding moves
        # that reduce the nearest opponent's reachable space converts a dominant
        # position into an actual win instead of a drawn-out endgame. This uses a
        # STATIC (no-retreat) flood from the opponent head, treating our body
        # (after moving to nc) as walls -- so a move that seals off the opp's
        # escape scores higher. Gated to clearly-longer + healthy so it never
        # overrides our own survival (space/coil/pin terms already applied above).
        if (not being_hunted) and my_len > _max_ol + 1 and my_health >= 25 and opponents:
            # nearest opponent
            _tgt = min(opponents, key=lambda s: _manhattan(head, (s["body"][0]["x"], s["body"][0]["y"])))
            _oh = (_tgt["body"][0]["x"], _tgt["body"][0]["y"])
            if _manhattan(head, _oh) <= 8:
                # our body after moving to nc: old body (tail retreats) + new head
                _ob = set(my_body)
                if my_body:
                    _ob.discard(my_body[-1])
                _ob.add(nc)
                _walls = _ob | opp_bodies_static
                _walls.discard(_oh)  # opp head is the flood start, not a wall
                _oppspace = _static_flood_from(_oh, _walls, limit=width * height)
                # smaller opp space = better for us. Reward the squeeze.
                if _oppspace < my_len:
                    score += (my_len - _oppspace) * 3.0
                if _oppspace <= 4:
                    score += 120.0   # opp nearly sealed -> press hard
                elif _oppspace <= 8:
                    score += 50.0

        return score, space, name, nc, sspace

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
        # Prefer the move that most reduces distance to nearest food, but never
        # sacrifice space for a marginal distance gain: break near-ties by space.
        # This stops us diving into a wall-corner just to shave one manhattan
        # step toward food while the enemy closes in (round-1 sim_152 death).
        opp_heads_all = [(o["body"][0]["x"], o["body"][0]["y"]) for o in opponents]
        def food_pref(s):
            nc = s[3]
            fd = food_dist(nc)
            # if enemy head is near AND we are on an edge heading toward it,
            # prefer more space over chasing the contested food.
            return (fd, -s[4], -s[1])
        best.sort(key=food_pref)
    else:
        # We are clearly longer than every opponent: hunt to force a
        # favorable head-to-head, while keeping space priority.
        _mol = _max_opp_len(opponents)
        clearly_longer = my_len > _mol + 1
        massively_longer = my_len > _mol * 2  # don't chase a tiny snake into coils
        if clearly_longer and not massively_longer and opponents:
            opp_heads = [(o["body"][0]["x"], o["body"][0]["y"]) for o in opponents]

            def opp_dist(nc):
                return min(_manhattan(nc, oh) for oh in opp_heads)

            # Keep ample space, then close distance to the enemy head.
            best.sort(key=lambda s: (-s[4], -s[1], opp_dist(s[3])))
        else:
            # Prefer more space, then move toward center for safety.
            center = (width // 2, height // 2)
            best.sort(key=lambda s: (-s[4], -s[1], _manhattan(s[3], center)))

    return best[0][2]


def _max_opp_len(opponents):
    if not opponents:
        return 0
    return max(s["length"] for s in opponents)


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
