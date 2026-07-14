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
    """Count open cells reachable from start."""
    if start in blocked or not inside(start, w, h):
        return 0
    q = [start]
    seen = {start}
    total = 0
    qi = 0
    while qi < len(q) and total < limit:
        p = q[qi]
        qi += 1
        total += 1
        for d in MOVES.values():
            n = add(p, d)
            if inside(n, w, h) and n not in blocked and n not in seen:
                seen.add(n)
                q.append(n)
    return total


def adjacent_food(head, food, w, h):
    """Whether a snake could eat this turn, causing its tail not to vacate."""
    fs = set(food)
    return any(inside(add(head, d), w, h) and add(head, d) in fs for d in MOVES.values())


def territory(my_start, enemy_starts, blocked, w, h):
    """Small Voronoi-style estimate of space we can reach before equal/longer enemies."""
    cells = [(x, y) for x in range(w) for y in range(h) if (x, y) not in blocked]

    def dists(starts):
        q = []
        out = {}
        for st in starts:
            if inside(st, w, h) and st not in blocked and st not in out:
                out[st] = 0
                q.append(st)
        qi = 0
        while qi < len(q):
            p = q[qi]
            qi += 1
            for d in MOVES.values():
                n = add(p, d)
                if inside(n, w, h) and n not in blocked and n not in out:
                    out[n] = out[p] + 1
                    q.append(n)
        return out

    mine = dists([my_start])
    theirs = dists(enemy_starts) if enemy_starts else {}
    score = 0
    for c in cells:
        md = mine.get(c)
        if md is None:
            continue
        ed = theirs.get(c, 999)
        if md < ed:
            score += 1
        elif md == ed:
            score -= 0.25
        else:
            score -= 0.5
    return score


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



def self_path_count(body, food, static_blocked, w, h, depth=6, cap=200):
    """Count short self-avoiding continuations after a candidate move.

    Flood fill sees eventual space, but long snakes can still coil into a local
    one-way noose while the tail is several turns away.  This shallow search
    treats other snakes as static obstacles and simulates our own tail movement,
    giving a cheap mobility tie-breaker in long/healthy games.
    """
    food = frozenset(food)
    static_blocked = frozenset(static_blocked)
    cache = {}

    def rec(cur_body, cur_food, d):
        if d <= 0:
            return 1
        key = (cur_body, cur_food, d)
        old = cache.get(key)
        if old is not None:
            return old
        head = cur_body[0]
        neck = cur_body[1] if len(cur_body) > 1 else None
        total = 0
        for delta in MOVES.values():
            n = add(head, delta)
            if not inside(n, w, h) or n in static_blocked:
                continue
            if n == neck and len(set(cur_body[:3])) > 1:
                continue
            grow = n in cur_food
            occupied = set(cur_body if grow else cur_body[:-1])
            if n in occupied:
                continue
            nf = cur_food
            if grow:
                nf = frozenset(x for x in cur_food if x != n)
            nb = (n,) + (cur_body if grow else cur_body[:-1])
            total += rec(nb, nf, d - 1)
            if total >= cap:
                total = cap
                break
        cache[key] = total
        return total

    return rec(tuple(body), food, depth)

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
        hazard_damage = game_state.get("game", {}).get("ruleset", {}).get("settings", {}).get("hazardDamagePerTurn", 14)
        snakes = board.get("snakes", [])
        enemies = [s for s in snakes if s.get("id") != my_id]

        # Cells occupied after the normal tail pop.  An enemy tail is *not* safe
        # if that enemy can eat this turn, because eating keeps the tail in place.
        # Our own tail is handled per candidate below (it stays if we eat).
        blocked = set()
        for s in snakes:
            body = [pt(x) for x in s.get("body", [])]
            if not body:
                continue
            is_me = s.get("id") == my_id
            could_grow = (not is_me) and (adjacent_food(body[0], food, w, h) or s.get("health", 100) <= 1)
            for i, cell in enumerate(body):
                if i == len(body) - 1 and not could_grow:
                    continue
                blocked.add(cell)

        enemy_heads = [pt(s["head"]) for s in enemies]
        enemy_lengths = {pt(s["head"]): s.get("length", len(s.get("body", []))) for s in enemies}
        danger_equal_longer = set()
        danger_shorter = set()
        enemy_nexts = []
        for s in enemies:
            body = [pt(x) for x in s.get("body", [])]
            if not body:
                continue
            eh = body[0]
            elen = s.get("length", len(body))
            # Head-to-head danger only matters for squares the enemy can actually
            # choose.  The first version marked all four adjacent cells, including
            # the enemy neck or occupied body cells; that was safe but could make us
            # unnecessarily timid around food and wall-trapped opponents.
            opts = []
            neck2 = body[1] if len(body) > 1 else None
            for d in MOVES.values():
                n = add(eh, d)
                if not inside(n, w, h):
                    continue
                if n == neck2 and len(set(body[:3])) > 1:
                    continue
                if n in blocked and n != head:
                    continue
                opts.append(n)
                if elen >= my_len:
                    danger_equal_longer.add(n)
                else:
                    danger_shorter.add(n)
            enemy_nexts.append((s, opts))

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
            if n in hazards and my_health <= hazard_damage + 1:
                continue

            # Never voluntarily take a tie/losing head-to-head if any other move exists.
            h2h_bad = n in danger_equal_longer
            # Moving into a shorter snake's possible head square can be good, but only
            # if there is still room afterwards.
            h2h_good = n in danger_shorter

            sim_blocked = set(blocked)
            sim_blocked.add(head)  # our old head becomes neck
            if n in food and my_body:
                # If we eat, our current tail does not vacate; do not score paths
                # that rely on squeezing through it.
                sim_blocked.add(my_body[-1])
            area = flood(n, sim_blocked, w, h, limit=w * h)
            if area <= 1:
                continue

            score = area * 12.0
            if h2h_bad:
                # Normally never enter a possible equal/longer head square.  However,
                # in this tyrelh-python matchup several close losses reached a state
                # where the only non-head-risk move was an immediate self-trap (area
                # 1-3), while the "risky" square opened the board and the opponent was
                # only equal/+1 length.  Treat that as a last-ditch gamble instead of
                # choosing certain death; any reasonable safe alternative keeps the
                # full hard penalty.
                h2h_penalty = 10000
                if my_health > 15 and my_len + 1 >= max_enemy_len and area >= max(12, my_len * 3):
                    best_safe_area = 0
                    best_safe_exits = 0
                    for od in MOVES.values():
                        on = add(head, od)
                        if on == n or not inside(on, w, h):
                            continue
                        if on == neck and len(set(my_body[:3])) > 1:
                            continue
                        if on in blocked or on in danger_equal_longer:
                            continue
                        if on in hazards and my_health <= hazard_damage + 1:
                            continue
                        osimb = set(blocked)
                        osimb.add(head)
                        if on in food and my_body:
                            osimb.add(my_body[-1])
                        oa = flood(on, osimb, w, h, limit=w * h)
                        oe = sum(1 for d2 in MOVES.values()
                                 if inside(add(on, d2), w, h) and add(on, d2) not in osimb)
                        if oa > best_safe_area or (oa == best_safe_area and oe > best_safe_exits):
                            best_safe_area, best_safe_exits = oa, oe
                    if best_safe_area <= max(4, my_len // 2) or (best_safe_area <= my_len and best_safe_exits <= 1):
                        h2h_penalty = 850 + max(0, max_enemy_len - my_len) * 220
                score -= h2h_penalty
            if h2h_good and my_len > max_enemy_len:
                # A shorter snake cannot beat us head-to-head, but when we are
                # already safely ahead there is little need to dive into the
                # squares around its head; doing so can pull us into cramped
                # chase patterns.  Keep a larger bonus only when length is close.
                if my_len <= max_enemy_len + 2:
                    score += 40
                elif my_len <= max_enemy_len + 3:
                    # At +3 length we already win head-to-heads comfortably.  The
                    # battlejake survivor repeatedly wins when we voluntarily step
                    # into a shorter head's possible square at only +3, then get
                    # mirrored into our own body/rail pocket.  Treat these as
                    # mildly bad unless area/food clearly require the chase.
                    score -= 90
                elif my_len <= max_enemy_len + 4:
                    # Battlejake-style survivor losses often begin at only +4: we
                    # are long enough to win a direct head-to-head, but stepping into
                    # the shorter head's possible square lets it mirror beside our
                    # body and close a pocket.  Make these optional chase moves
                    # mildly unattractive unless area/food clearly demand them.
                    score -= 150
                else:
                    # When we are already far ahead, do not enter even a shorter
                    # snake's possible head square just to chase it.  Amphibious
                    # Arthur's rare wins often start with us shadowing a much
                    # smaller head into a cramped pocket; outliving in open space
                    # is safer than forcing a nonessential head-to-head.
                    score -= 240
            # Prefer cells with multiple exits (less likely to enter a cul-de-sac).
            exits = 0
            for d2 in MOVES.values():
                nn = add(n, d2)
                if inside(nn, w, h) and nn not in sim_blocked:
                    exits += 1
            score += exits * 18
            if exits <= 1 and area < my_len + 4:
                score -= 250
            # Against strong A*/space opponents, equal-length endgames often turn
            # into self-coils: a one-exit move may have more than my_len cells of
            # flood-fill, but still be a one-way pocket with no way back to the
            # moving tail.  Add a mild general penalty before the far-ahead-only
            # noose rule below.
            if my_len >= 14 and my_health > 65 and exits <= 1 and area < my_len * 2 and n not in food:
                score -= 90
                # Versus balanced long-game opponents (e.g. battlesnake-elon),
                # many losses begin while we are equal/shorter and voluntarily
                # step through a one-cell throat into our own coil.  Flood-fill
                # can still report ~2 snake-lengths of space, but with a longer
                # enemy alive we cannot afford that forced corridor.  Prefer any
                # comparable two-exit move while healthy; hunger/food corridors
                # remain exempt above.
                if my_len <= max_enemy_len:
                    score -= 620
                    if area < my_len + 8:
                        score -= 140
            # In long games where we are already far ahead, a one-exit move can
            # be the mouth of a large-looking but effectively one-way noose.
            # Amphibious Arthur's rare wins often happen after we voluntarily
            # thread these throats while healthy instead of keeping multiple
            # continuations open.  Keep this disabled when food/hunger or close
            # length makes taking a corridor worth the risk.
            if (my_len >= max_enemy_len + 5 and my_health > 70
                    and exits <= 1 and n not in food):
                score -= 115
                if area < my_len * 2:
                    score -= 70

            # One extra ply of survivability: prefer moves that leave several
            # legal continuations after the opponent also advances.
            future = 0
            for d2 in MOVES.values():
                nn = add(n, d2)
                if inside(nn, w, h) and nn not in sim_blocked and nn not in danger_equal_longer:
                    future += 1
            score += future * 10
            if future == 0:
                score -= 500

            # Avoid one-turn-ahead head traps against equal/longer snakes.
            # The immediate head-to-head filter above is not enough near edges:
            # a tempting food/corner move can leave only exits that a longer
            # enemy can cover on its next move.  Penalize candidates where a
            # plausible enemy step would make all of our next continuations
            # losing head-to-heads.  Keep it gated to healthy, close-length
            # situations so starvation escapes and clear length leads are not
            # over-constrained.
            if my_health > 20 and my_len <= max_enemy_len + 1:
                my_next_len = my_len + (1 if n in food else 0)
                continuations = []
                for d2 in MOVES.values():
                    nn = add(n, d2)
                    if inside(nn, w, h) and nn not in sim_blocked:
                        continuations.append(nn)
                worst_safe = None
                for s, opts in enemy_nexts:
                    elen = s.get("length", len(s.get("body", [])))
                    if elen < my_next_len or dist(n, pt(s["head"])) > 5:
                        continue
                    for eo in opts:
                        if dist(n, eo) > 2:
                            continue
                        next_danger = {eo}
                        for ed in MOVES.values():
                            en = add(eo, ed)
                            if inside(en, w, h):
                                next_danger.add(en)
                        safe_after = sum(1 for c in continuations if c not in next_danger)
                        worst_safe = safe_after if worst_safe is None else min(worst_safe, safe_after)
                if worst_safe == 0 and continuations:
                    score -= 220
                    if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                        score -= 120
                elif worst_safe == 1 and len(continuations) <= 2:
                    score -= 55

            # Shallow self-avoidance lookahead for long, healthy games.  This is
            # intentionally only a tie-breaker unless a move has almost no
            # continuations; it targets late losses where flood-fill space stayed
            # large until we had already coiled into a noose.
            if my_len >= 8 and my_health > 45:
                static_blocked = set(sim_blocked) - set(my_body)
                # If this candidate eats, our tail stays for the next turn.
                # The previous version always dropped the tail for this shallow
                # self-lookahead, which made immediate food inside a near-closed
                # coil look safer than it really was.
                if n in food:
                    next_body = tuple([n] + my_body)
                    lookahead_food = [f for f in food if f != n]
                else:
                    next_body = tuple([n] + my_body[:-1])
                    lookahead_food = food
                path_count = self_path_count(next_body, lookahead_food, static_blocked, w, h, depth=6, cap=200)
                score += min(path_count, 80) * 2.0
                if path_count == 0:
                    score -= 450
                elif path_count < 8:
                    score -= (8 - path_count) * 120
                # Gigantic-george endgames are won positions until we enter a
                # short forced sequence in our own coil.  If we are healthy and
                # far ahead, a non-food move with almost no self-avoiding
                # continuations is usually a noose throat, not a useful attack.
                if (my_health > 70 and my_len >= max_enemy_len + 8
                        and n not in food and path_count < 4):
                    score -= 2400
                    if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                        score -= 500

                # Battlejake-style mirrored losses often start when we are already
                # clearly longer and step into a shorter head's possible square
                # through a shallow self-avoidance throat.  Direct kills are not
                # needed at +5 or more; preserve mobility instead, especially on
                # the outer ring where the smaller snake can parallel our rail.
                if (my_health > 70 and my_len >= max_enemy_len + 5
                        and h2h_good and n not in food and path_count < 25):
                    score -= (25 - path_count) * 22
                    if n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2:
                        score -= 130

                # In late, already-long games the remaining safe region can be a
                # narrow pocket even though the flood-fill score still looks nonzero.
                # Prefer moves that keep a short route to our moving tail in those
                # cramped pockets; this helps avoid dying in our own coil while far
                # ahead of a weaker opponent.  The gate keeps it as a defensive
                # endgame rule rather than a general food/tail-chasing habit.
                far_ahead_cruise = (my_len >= 18 and my_len >= max_enemy_len + 8 and my_health > 45)
                if my_body and ((my_len >= max_enemy_len + 3 and my_health > 70) or far_ahead_cruise):
                    tail_cell = next_body[-1]
                    tail_blocked = set(sim_blocked)
                    tail_blocked.discard(tail_cell)
                    tail_dist = shortest(n, [tail_cell], tail_blocked, w, h, max_depth=w * h)
                    if area <= max(8, my_len // 2):
                        if tail_dist is None:
                            score -= 220
                        else:
                            score += max(0, 6 - tail_dist) * 38
                            if n == my_body[-1]:
                                score += 460
                    # When far ahead and healthy, our main remaining failure mode is
                    # building a long noose while pursuing a much shorter snake.  A
                    # full flood fill can still be huge through a one-cell throat, so
                    # add a very small global tail-connectivity bias in late games.
                    # This is intentionally weaker than area/exits and only active
                    # with a clear length lead.
                    elif tail_dist is not None:
                        score += max(0, 18 - tail_dist) * 4
                        # Against this round's balanced survivor, many losses are
                        # not from the opponent attacking but from our long, healthy
                        # snake coiling after a huge length lead.  Once we are safely
                        # ahead, make tail connectivity a real survival objective even
                        # at mid health; food is abundant and preserving an unwind path
                        # is worth more than marginal area/exits.
                        if far_ahead_cruise:
                            score += max(0, 26 - tail_dist) * 10
                            if tail_dist > my_len:
                                score -= min(350, (tail_dist - my_len) * 18)
                    else:
                        # No path to our moving tail while far ahead is the common
                        # signature of the losses versus gigantic-george: the raw
                        # flood-fill may count a pocket that is large enough for a
                        # few turns but not enough to unwind a long snake.
                        if area < my_len * 2:
                            score -= 650
                        elif exits <= 1:
                            score -= 250
                            # At a comfortable +5 lead, Battlejake-style survivors
                            # often win by mirroring while our snake takes a one-exit
                            # no-tail corridor with deceptively large flood-fill.
                            # Survival is better than pressure; avoid these optional
                            # noose throats when healthy.
                            if my_health > 70 and my_len >= max_enemy_len + 5:
                                score -= 700
                        else:
                            score -= 80
                        if far_ahead_cruise:
                            score -= 520
                            # Battlejake round-1 losses still showed 2-exit, large
                            # flood-fill regions on/near the rail with no path back
                            # to the moving tail.  In a won +8 endgame those are
                            # usually noose lobes, not real space; discount them
                            # before raw area can dominate a smaller tail-connected
                            # route.
                            if area < my_len * 4:
                                score -= 520
                                if n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2:
                                    score -= 240
                                if h2h_good:
                                    score -= 260
                            # Battlejake-style mirrored survivor endgames often show
                            # us far ahead, healthy, and choosing a one-exit/no-tail
                            # continuation because its raw flood-fill is large.  That
                            # space is usually behind a noose throat; prefer a smaller
                            # route that stays connected to the moving tail.
                            if exits <= 1:
                                score -= 900
                elif my_health > 55 and my_len >= 14 and area < my_len * 3 and n not in food:
                    # In close-length long games, survival often depends on staying
                    # connected to our own tail rather than maximizing raw area.
                    # Battlesnake-elon losses often show flood-fill areas of 2+
                    # snake lengths after stepping through a coil throat, but no
                    # route back to the moving tail; by the time area is tiny the
                    # game is already forced.  Let this tail-connectivity check
                    # look at moderately-sized regions too, while staying disabled
                    # for food and short/open-board positions.
                    tail_cell = next_body[-1]
                    tail_blocked = set(sim_blocked)
                    tail_blocked.discard(tail_cell)
                    tail_dist = shortest(n, [tail_cell], tail_blocked, w, h, max_depth=w * h)
                    if tail_dist is None:
                        score -= 160
                        # In roughly equal long endgames, no path to tail is a
                        # strong noose signature even if raw flood-fill still looks
                        # moderately large.  Penalize it enough to prefer a smaller
                        # tail-connected corridor when both options are otherwise
                        # safe; this targets the balanced battlesnake-elon losses.
                        if my_len <= max_enemy_len + 4 and area <= my_len * 3:
                            score -= 760
                            if exits <= 1:
                                score -= 160
                        # When we are not longer, a small region with no path back
                        # to our moving tail is usually a losing pocket rather than
                        # useful space.  This Flipez-crystal matchup's rare losses
                        # often end with us stepping through a narrow top/edge pocket
                        # while already shorter, then having only forced moves left.
                        if my_len <= max_enemy_len and area <= my_len + 2:
                            score -= 260
                            if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                                score -= 90
                    else:
                        score += max(0, 12 - tail_dist) * 14
                        if n == my_body[-1]:
                            score += 140

            # Voronoi-style space ownership versus equal/longer opponents.
            scary_heads = [pt(s["head"]) for s in enemies if s.get("length", len(s.get("body", []))) >= my_len]
            if scary_heads:
                score += territory(n, scary_heads, sim_blocked, w, h) * 1.5

            # Food valuation.  Use BFS distance after making this move, because
            # Manhattan distance often walks through bodies.  Be hungrier when low
            # health or when we need length to win head-to-heads.
            food_dist = shortest(n, food, sim_blocked, w, h, max_depth=60)
            if food_dist is not None:
                hunger = max(0, 70 - my_health) * 1.4
                if my_len < max_enemy_len:
                    # Against efficient food-seeking opponents, falling even one
                    # length behind makes every edge/corner race dangerous.  Be
                    # more willing to route toward reachable food while shorter
                    # instead of letting flood-fill space dominate until we are
                    # permanently losing head-to-heads.  Famished-frank is an
                    # especially strong food racer; many losses show us 4-10
                    # lengths behind while high-health, passing a route that is
                    # only 1-3 steps closer to food because raw area ties dominate.
                    # Keep this as a near-food/catch-up bias (not a board-wide
                    # hunger increase) so we do not chase distant snacks through
                    # unsafe rails.
                    hunger += 85
                    if food_dist <= 5:
                        score += (6 - food_dist) * 10
                    deficit = max_enemy_len - my_len
                    # kentmacdonald2__beames is another efficient food/space snake:
                    # many losses have us still healthy but already 4-8 lengths down,
                    # especially in the early/mid game after we orbit open space while
                    # the opponent consumes the board.  Add a narrow distance gradient
                    # only for small, clearly-behind snakes so we start walking toward
                    # reachable food before the starvation clock is urgent.  This is
                    # intentionally weaker and narrower than a general hunger boost: it
                    # does not fire when close in length/ahead or after we have grown
                    # large enough that self-coil safety dominates.
                    if deficit >= 4 and my_len <= 12 and my_health > 45 and food_dist <= 10:
                        score += (11 - food_dist) * 10
                        score -= food_dist * 3
                    if deficit >= 6 and my_health <= 97 and my_len <= 22 and food_dist <= 3:
                        # Narrow extra catch-up pressure for strong food racers:
                        # when badly behind, a safe very-near snack/route is usually
                        # worth more than small open-space tie-breaks. Keep it short
                        # range only; broad food urgency has hurt smoke tests.
                        score += (4 - food_dist) * 42
                        if food_dist == 0:
                            score += 55
                elif my_len == max_enemy_len:
                    hunger += 45
                if food_dist <= 2:
                    hunger += 25
                # When health is genuinely low, reaching food before the clock
                # runs out matters more than a small flood-fill difference.  The
                # original survival weights could overvalue a roomier move that
                # drifted away from food and then starve in longer games.
                if my_health <= 35:
                    hunger += (36 - my_health) * 8
                    if food_dist + 2 >= my_health:
                        score -= 900
                if my_health <= 20:
                    hunger += (21 - my_health) * 18
                score += hunger / (food_dist + 1)
                # In genuinely low-health endgames, area alone can otherwise
                # dominate the score and make us drift parallel to reachable food.
                # Add a direct distance pressure that only activates when the
                # starvation clock is the main threat.
                if my_health <= 30:
                    score -= food_dist * (31 - my_health) * 6
                    if food_dist + 1 <= my_health:
                        score += 90 / (food_dist + 1)
                # Do not wait until the last few turns before committing to food.
                # Rare losses versus jump-flooding come from long, safe-looking
                # loops where both snakes are equal length but we slowly starve
                # while reachable food sits 4-8 cells away.  Add a moderate
                # mid-health distance bias; it is much weaker than the panic
                # rule above and only activates once health is no longer full.
                if my_health <= 60:
                    mid_urgency = 61 - my_health
                    score -= food_dist * mid_urgency * 2.0
                    if food_dist <= 7:
                        score += (8 - food_dist) * mid_urgency * 1.5
                # MorganConrad__tantilla survives as a small snake while food
                # accumulates; our remaining losses are mostly healthy +6/+10
                # length leads that turn into self-coils after optional snacks.
                # Start treating nearby food as mildly hazardous before we become
                # enormous, but keep the gate high enough that close races and
                # real hunger still collect growth.
                if my_health > 65 and my_len >= 14 and my_len >= max_enemy_len + 6:
                    if food_dist == 0:
                        score -= 520
                    elif food_dist == 1:
                        score -= 280
                    elif food_dist == 2:
                        score -= 140
                    elif food_dist <= 5:
                        score -= (6 - food_dist) * 30

                # If we are already enormous and far ahead, food is usually
                # a liability rather than progress: it pins the tail and makes
                # our own coil denser.  The eremetic-eric losses are mostly
                # high-health length-40+ self-traps while a tiny opponent survives.
                # Keep this off when health is relevant or the length race is close.
                if my_health > 65 and my_len >= 24 and my_len >= max_enemy_len + 12:
                    if food_dist <= 2:
                        score -= (3 - food_dist) * 260
                    elif food_dist <= 5:
                        score -= (6 - food_dist) * 18
                # Eremetic-eric's wins are overwhelmingly long endgames where we
                # have already won the length race (often 35-65 vs ~8) but keep
                # taking dense board snacks until our own body is a noose.  Start
                # treating food as a hazard once we are safely +8 and length 20+,
                # unless health is genuinely relevant.  The earlier anti-food rule
                # was too narrow/weak: losing logs still show runaway growth.
                if my_health > 45 and my_len >= 20 and my_len >= max_enemy_len + 8:
                    if food_dist == 0:
                        score -= 1500
                    elif food_dist == 1:
                        score -= 850
                    elif food_dist == 2:
                        score -= 420
                    elif food_dist <= 5:
                        score -= (6 - food_dist) * 90
                    elif food_dist <= 8:
                        score -= (9 - food_dist) * 18

                # If eating immediately is safe, take the growth/health edge.
                # This beats straight-line opponents and also improves future
                # head-to-head odds against more cautious snakes.
                if food_dist == 0:
                    score += 55
                    if my_health > 65 and my_len >= 24 and my_len >= max_enemy_len + 12:
                        score -= 520
                    if my_health > 45 and my_len >= 20 and my_len >= max_enemy_len + 8:
                        score -= 1200
                    # Against nbw-ruby style food/space snakes, the main losing
                    # pattern is getting outgrown by 4+ (including this Flipez-crystal matchup) length.  If a safe snack is
                    # immediately available while we are already far behind, take
                    # the growth instead of letting raw flood-fill/anti-rail terms
                    # keep orbiting.  This is deliberately limited to large deficits
                    # so it does not undo earlier edge-food safety when close/ahead.
                    if my_len + 3 <= max_enemy_len and my_health <= 99:
                        # Famished-frank and other efficient food racers punish us
                        # whenever we pass up a safe adjacent snack while already
                        # several lengths behind.  Earlier catch-up tuning only
                        # helped at -4 and was too weak to overcome small
                        # flood-fill/path-count differences, so widen it slightly
                        # but keep it limited to immediate food (after all hard
                        # safety filters) rather than broad food-chasing.
                        score += 390
                        if my_len + 6 <= max_enemy_len:
                            score += 230
                    # Gigantic-george leaves the board dense with food while staying
                    # short.  In those far-ahead endgames every legal move can be a
                    # snack, so the generic anti-food penalty no longer distinguishes
                    # a safe spacious bite from one that seals a tiny self-coil.
                    # When already safely ahead and healthy, heavily prefer immediate
                    # food that preserves real space/continuations; optional growth in
                    # a pocket is the main way this matchup turns a huge lead into a
                    # self-elimination.
                    if my_health > 70 and my_len >= 20 and my_len >= max_enemy_len + 8:
                        score -= 420
                        if my_health > 85 and my_len >= max_enemy_len + 12:
                            score -= 320
                        if area < my_len:
                            score -= (my_len - area) * 95
                        if area < max(8, my_len // 2):
                            score -= 260
                        # path_count is available in the long/healthy lookahead block
                        # above.  A zero-count eating move pins the tail and has no
                        # short self-avoiding continuation, so avoid it unless forced.
                        try:
                            if path_count == 0:
                                score -= 520
                            elif path_count < 8:
                                score -= (8 - path_count) * 45
                        except UnboundLocalError:
                            pass
                    # Edge food can be a trap when we are already safely ahead:
                    # eating pins our tail for a turn and can start a wall spiral.
                    # Keep taking these when hungry or needing length, but do not
                    # let a healthy, longer snake chase unnecessary wall snacks.
                    edge_food = (n[0] in (0, w - 1) or n[1] in (0, h - 1))
                    outer_food = (n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2)
                    if (my_health > 75 and my_len >= max_enemy_len + 2 and edge_food):
                        score -= 65
                    # A rare rdbrck loss started by taking a high-health y=1 snack
                    # while already twice the opponent's length, pinning our tail and
                    # beginning a self-coil.  Treat outer-ring snacks as optional when
                    # we are far ahead; this is softer than the actual-edge penalty.
                    if (my_health > 80 and my_len >= max_enemy_len + 6 and outer_food):
                        score -= 70
                    # Versus battlejake-like survivors, rare losses often start by
                    # taking a high-health edge snack at a +5/+6 lead that leaves only
                    # a one-cell rail continuation.  That growth is not needed to win
                    # head-to-heads and pins the tail, so require notably more space
                    # for optional one-exit rail food once we are comfortably ahead.
                    if (my_health > 80 and my_len >= 14 and my_len >= max_enemy_len + 5
                            and edge_food and exits <= 1):
                        score -= 260
                    # Do not grab optional rail food when a longer/equal enemy is
                    # already close enough to force the next exit.  Several Xe__since
                    # losses were healthy top/bottom-edge snacks that immediately
                    # became losing head-to-head races; if we need food urgently this
                    # stays disabled by the health gate below.
                    if (edge_food and my_health > 55 and my_len + 1 <= max_enemy_len
                            and enemy_heads and min(dist(n, eh) for eh in enemy_heads) <= 4):
                        # Stronger rail-snack avoidance: against ccSnake2018 several
                        # losses started by eating edge food while still not longer,
                        # giving a nearby equal/longer head the only exit lane.
                        score -= 430
                    # The current opponent often wins the rare games by letting us
                    # chase high-health snacks on the outer lane while it already has
                    # a clear length lead.  Even if the enemy is not adjacent yet,
                    # growing from 7->8 versus 11->12 does not fix head-to-head risk
                    # and can pin our tail into a wall spiral.  Prefer waiting in the
                    # interior unless health is becoming relevant.
                    if outer_food and my_health > 70 and my_len + 3 <= max_enemy_len:
                        # Against strong food-racing opponents, being shorter is
                        # itself dangerous; do not over-penalize useful outer-lane
                        # growth unless we are badly behind and the snack is truly
                        # optional.  Previous tuning for rail-shadow opponents was
                        # too willing to give up catch-up food at only -2 length.
                        score -= 45
                        if edge_food:
                            score -= 35
                # Do not bloat forever when healthy and already far ahead.
                if my_health > 80 and my_len >= max_enemy_len + 4 and food_dist <= 1:
                    score -= 25

            # Avoid optional wall races against equal/longer snakes.  Several
            # losses/draws versus nbw__nbw-crystal came from a healthy snake
            # drifting into the outer rail while a same-size/larger opponent was
            # close enough to take away the only exit a few turns later.  This is
            # deliberately disabled when hungry, when eating immediately, or when
            # we are clearly longer, because edge food/corridors can be correct
            # in those cases.
            scary_close = [eh for eh in enemy_heads
                           if enemy_lengths.get(eh, 0) >= my_len - 1 and dist(n, eh) <= 5]
            if my_health > 55 and n not in food and my_len <= max_enemy_len + 1 and scary_close:
                outer_ring = n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2
                if outer_ring:
                    score -= 70
                    if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                        score -= 45
            # Be much more reluctant to enter the rail/corner when a close
            # equal-or-longer snake is nearby and we are not hungry.  The current
            # opponent repeatedly wins the few lost games by shadowing us along
            # an edge until our only exit is a losing head-to-head.
            close_longer = [eh for eh in enemy_heads
                            if enemy_lengths.get(eh, 0) >= my_len and dist(n, eh) <= 6]
            if my_health > 55 and my_len <= max_enemy_len and close_longer:
                outer_ring = n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2
                actual_edge = n[0] in (0, w - 1) or n[1] in (0, h - 1)
                if outer_ring:
                    score -= 65
                if actual_edge:
                    score -= 160
                    # Nagini often wins close/shorter games by shadowing our rail
                    # lane until the only exit is a losing head-to-head.  Make
                    # healthy non-food rail steps near an equal/longer head much
                    # less attractive before they become immediate forced moves.
                    if my_health > 65 and n not in food and min(dist(n, eh) for eh in close_longer) <= 5:
                        score -= 180
                        if exits <= 2:
                            score -= 90
                    if (n[0] in (0, w - 1)) and (n[1] in (0, h - 1)):
                        score -= 180
                # If the move also closes distance to that stronger head, it is
                # especially likely to start/continue a rail race.
                cur_near = min(dist(head, eh) for eh in close_longer)
                new_near = min(dist(n, eh) for eh in close_longer)
                if outer_ring and new_near < cur_near:
                    score -= 90

            # Do not follow a longer snake into a same-edge/corner race when we
            # have an interior escape.  In several ccSnake2018 losses our head
            # shadowed a longer enemy along x=0/x=10 or y=0/y=10; the next square
            # was not an immediate head-to-head yet, but the opponent could take
            # the only rail exit on the following turn.
            if my_health > 55 and my_len <= max_enemy_len and enemy_heads:
                same_edge_race = False
                for eh in enemy_heads:
                    if enemy_lengths.get(eh, 0) < my_len or dist(n, eh) > 3:
                        continue
                    if (n[0] == eh[0] and n[0] in (0, w - 1)) or (n[1] == eh[1] and n[1] in (0, h - 1)):
                        same_edge_race = True
                        break
                if same_edge_race:
                    score -= 360
                    if n[0] in (0, w - 1) and n[1] in (0, h - 1):
                        score -= 240

            # When we are substantially shorter but healthy, do not volunteer
            # for outer-lane races anywhere on the board.  Round-1 ccSnake2018 losses
            # repeatedly show us entering an edge with high health while the larger
            # snake shadows the adjacent lane; by the time it is close, all exits are
            # losing head-to-heads.
            if my_health > 70 and my_len + 3 <= max_enemy_len and n not in hazards:
                outer_ring = n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2
                actual_edge = n[0] in (0, w - 1) or n[1] in (0, h - 1)
                if outer_ring:
                    score -= 35
                if actual_edge:
                    score -= 55
                    # Xtagon/Nagini often wins by getting a clear length lead and
                    # then shadowing our much shorter snake along the actual rail.
                    # When badly behind and healthy, a non-food edge step is rarely
                    # worth the head-to-head squeeze risk; keep edge food available
                    # for catch-up, but bias ordinary movement back to the interior.
                    if n not in food and my_len + 6 <= max_enemy_len:
                        score -= 140
                    if (n[0] in (0, w - 1)) and (n[1] in (0, h - 1)):
                        score -= 45


            # Also avoid equal-length healthy rail shadows before they become
            # immediate head-to-head traps.  The Spenca round-1 loss had us run
            # along the bottom edge while an equal-length opponent paralleled a
            # few cells inside; by the time the enemy was adjacent, all exits
            # were losing.  Bias off the actual rail earlier when an equal-or-
            # longer head is within striking distance and food is not urgent.
            if (my_health > 75 and my_len <= max_enemy_len and n not in food
                    and (head[0] in (0, w - 1) or head[1] in (0, h - 1))
                    and (n[0] in (0, w - 1) or n[1] in (0, h - 1))):
                rail_shadow = [eh for eh in enemy_heads
                               if enemy_lengths.get(eh, 0) >= my_len and dist(n, eh) <= 8]
                if rail_shadow:
                    score -= 170
                    if (n[0] in (0, w - 1)) and (n[1] in (0, h - 1)):
                        score -= 120
                    cur_corner_lane = min(head[0], w - 1 - head[0]) if head[1] in (0, h - 1) else min(head[1], h - 1 - head[1])
                    new_corner_lane = min(n[0], w - 1 - n[0]) if n[1] in (0, h - 1) else min(n[1], h - 1 - n[1])
                    if new_corner_lane < cur_corner_lane:
                        score -= 120


            # If we are clearly shorter but healthy, avoid continuing along an
            # outer rail toward a corner.  The Spenca/vulture loss was a classic
            # shadowed-rail squeeze: while 4 lengths behind, we moved down the
            # right wall from y=2 to y=1/y=0, then had no escape as the longer
            # snake paralleled us.  This is disabled for food/hungry states and
            # only penalizes moves that reduce distance to the nearest corner
            # while staying on the actual edge.
            if (my_health > 70 and my_len + 2 <= max_enemy_len and n not in food
                    and (head[0] in (0, w - 1) or head[1] in (0, h - 1))
                    and (n[0] in (0, w - 1) or n[1] in (0, h - 1))):
                cur_corner_lane = min(head[0], w - 1 - head[0]) if head[1] in (0, h - 1) else min(head[1], h - 1 - head[1])
                new_corner_lane = min(n[0], w - 1 - n[0]) if n[1] in (0, h - 1) else min(n[1], h - 1 - n[1])
                if new_corner_lane < cur_corner_lane:
                    score -= 260
                    if enemy_heads and min(dist(n, eh) for eh in enemy_heads) <= 8:
                        score -= 120

            # Battlejake-style mirrored rail traps: when already comfortably ahead
            # and healthy, a nearby shorter snake often survives by shadowing our
            # edge lane until our only continuation is back into our body.  Do not
            # take optional actual-edge/outer-ring moves near that head just to
            # pressure it or grab another snack; staying in the interior wins.
            if my_health > 70 and my_len >= max_enemy_len + 5 and enemy_heads:
                near_enemy = min(dist(n, eh) for eh in enemy_heads)
                if near_enemy <= 4:
                    outer_ring = n[0] <= 1 or n[0] >= w - 2 or n[1] <= 1 or n[1] >= h - 2
                    actual_edge = n[0] in (0, w - 1) or n[1] in (0, h - 1)
                    if outer_ring:
                        score -= 70
                    if actual_edge:
                        score -= 170
                        if exits <= 2:
                            score -= 80
                        if n in food:
                            score -= 90
                    # Even off the wall, do not keep stepping through a one-exit
                    # throat directly beside the smaller head when a clear lead is
                    # already enough to win by survival.
                    if exits <= 1 and near_enemy <= 2 and n not in food:
                        score -= 160


            # Stay central/open rather than riding walls.
            score -= (abs(n[0] - center[0]) + abs(n[1] - center[1])) * 2.2
            if n[0] in (0, w - 1) or n[1] in (0, h - 1):
                score -= 12
                # When comfortably healthy, avoid voluntarily starting long
                # wall crawls: past losses came from optional edge spirals
                # after we were already safe.  Keep the base penalty small so
                # hungry/endgame states can still use edge corridors.
                if my_health > 60 and area < (w * h) * 0.45:
                    score -= 18
                # A move along the rail with only one immediate exit is often
                # the first step into a corner race where an equal/longer enemy
                # can later force a head-to-head.  Prefer the adjacent interior
                # lane when we are healthy and not taking food.
                if my_health > 55 and exits <= 1 and n not in food:
                    # A one-exit rail move can still have a large flood-fill score
                    # because the space opens up after stepping through the next
                    # corner cell, but in practice these moves are brittle: a
                    # nearby body/head can force us to continue into the corner
                    # before the tail opens.  This caused the only round-0 loss
                    # versus coreyja__bombastic-bob (top-edge chase into (10,10)).
                    score -= 120
                    near_corner = ((n[0] <= 1 or n[0] >= w - 2) and n[1] in (0, h - 1)) or \
                                  ((n[1] <= 1 or n[1] >= h - 2) and n[0] in (0, w - 1))
                    if near_corner:
                        score -= 80
            if n in hazards:
                score -= 200 + max(0, hazard_damage + 12 - my_health) * 10

            # If stronger, squeeze toward the opponent; if weaker, maintain distance.
            if enemy_heads:
                nearest_enemy = min(dist(n, eh) for eh in enemy_heads)
                if my_len > max_enemy_len:
                    if my_len <= max_enemy_len + 3:
                        score += max(0, 7 - nearest_enemy) * 3
                    else:
                        # When safely ahead, do not keep chasing a smaller head into
                        # cramped coils; simply outlive it in open space.  ChaelCodes
                        # losses often begin around +4 to +8 length when the old
                        # proximity bonus pulled us toward a short survivor instead
                        # of preserving open lanes.
                        score += max(0, 5 - nearest_enemy) * 0.5
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
