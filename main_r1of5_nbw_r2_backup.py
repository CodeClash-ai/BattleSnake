"""
CodeClash Battlesnake bot (opus-4-8).

Strategy (much stronger than the naive SimpleSnake port):
  - Enumerate legal moves (in bounds, not into any snake body that will persist).
  - Model tails: a tail cell vacates next turn unless that snake just ate.
  - Avoid head-to-head losses: don't step onto a cell an equal/longer enemy
    head could also move to (unless we have no other choice).
  - Prefer head-to-head *wins* against strictly shorter enemies.
  - Score each candidate move by flood-fill reachable space (survival),
    plus a food/health incentive, and closeness to enemy when we are longer.
  - Robust legal fallback so we never crash / return illegal.

Coordinate system (BattleSnake v1 API, y-up, bottom-left origin):
    up = y+1, down = y-1, left = x-1, right = x+1
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
        "color": "#22cc88",
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


def _neighbors(p):
    x, y = p
    return [(x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)]


def _flood_fill(start_cell, blocked, w, h, limit=None):
    """Count reachable free cells from start_cell (BFS), bounded by limit."""
    if start_cell in blocked or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    stack = [start_cell]
    count = 0
    while stack:
        cur = stack.pop()
        count += 1
        if limit is not None and count >= limit:
            return count
        for nb in _neighbors(cur):
            if nb in seen:
                continue
            if not _in_bounds(nb, w, h):
                continue
            if nb in blocked:
                continue
            seen.add(nb)
            stack.append(nb)
    return count


def _reachable_with_tails(start_cell, static_blocked, snakes_bodies, w, h, limit=None):
    """BFS where a body cell frees up once the tail has retreated past it.

    static_blocked: cells that never free (e.g. permanent). We instead compute
    per-cell free-time from snake bodies: body cell at index i (0=head) of a
    snake of length L vacates after (L - i) steps (tail=index L-1 vacates at
    step 1, unless the snake just grew). We do a BFS carrying the step count;
    a cell is enterable at step t if it's empty OR its vacate_time <= t.
    """
    # Build vacate-time map: cell -> earliest step it becomes free.
    vacate = {}
    for body, grew in snakes_bodies:
        L = len(body)
        for i, cell in enumerate(body):
            # steps until this cell is vacated by tail retreat
            # tail (i=L-1) vacates after 1 step normally; if grew, +1 delay
            t = (L - i) + (1 if grew else 0)
            # keep the max requirement if overlap
            if cell not in vacate or vacate[cell] > t:
                vacate[cell] = t
    from collections import deque
    dq = deque()
    dq.append((start_cell, 1))
    seen = {start_cell}
    count = 0
    while dq:
        cur, step = dq.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        for nb in _neighbors(cur):
            if nb in seen:
                continue
            if not _in_bounds(nb, w, h):
                continue
            if nb in static_blocked:
                continue
            vt = vacate.get(nb)
            if vt is not None and vt > step + 1:
                # still occupied when we'd arrive
                continue
            seen.add(nb)
            dq.append((nb, step + 1))
    return count


def _can_reach(start_cell, target, static_blocked, snakes_bodies, w, h):
    """Time-aware BFS: can we reach `target` cell from start_cell, treating
    body cells as vacating once their tail retreats past them? Returns bool.
    This is the anti-self-trap signal: if we can still reach our own tail,
    we can keep chasing it and won't box ourselves in."""
    if start_cell == target:
        return True
    vacate = {}
    for body, grew in snakes_bodies:
        L = len(body)
        for i, cell in enumerate(body):
            t = (L - i) + (1 if grew else 0)
            if cell not in vacate or vacate[cell] > t:
                vacate[cell] = t
    from collections import deque
    dq = deque([(start_cell, 1)])
    seen = {start_cell}
    while dq:
        cur, step = dq.popleft()
        for nb in _neighbors(cur):
            if nb == target:
                return True
            if nb in seen or not _in_bounds(nb, w, h):
                continue
            if nb in static_blocked:
                continue
            vt = vacate.get(nb)
            if vt is not None and vt > step + 1:
                continue
            seen.add(nb)
            dq.append((nb, step + 1))
    return False


def _future_safe_moves(cell, blocked, w, h):
    """Count in-bounds, non-blocked neighbors of `cell` (escape options)."""
    n = 0
    for nb in _neighbors(cell):
        if _in_bounds(nb, w, h) and nb not in blocked:
            n += 1
    return n

def _voronoi_owned(my_head, enemy_heads_cells, blocked, w, h):
    """Multi-source BFS: count cells we reach STRICTLY before any enemy head.
    `enemy_heads_cells` is a list of enemy head (x,y). Returns (my_count, enemy_count).
    Cells reached at equal distance are contested (counted for neither / enemy-favored)."""
    from collections import deque
    INF = 1 << 30
    dist_me = {}
    dq = deque()
    if my_head not in blocked:
        dist_me[my_head] = 0
        dq.append((my_head, 0))
    while dq:
        cell, d = dq.popleft()
        for nb in _neighbors(cell):
            if not _in_bounds(nb, w, h):
                continue
            if nb in blocked:
                continue
            if nb in dist_me:
                continue
            dist_me[nb] = d + 1
            dq.append((nb, d + 1))
    dist_en = {}
    dq = deque()
    for eh in enemy_heads_cells:
        if eh not in blocked and eh not in dist_en:
            dist_en[eh] = 0
            dq.append((eh, 0))
    while dq:
        cell, d = dq.popleft()
        for nb in _neighbors(cell):
            if not _in_bounds(nb, w, h):
                continue
            if nb in blocked:
                continue
            if nb in dist_en:
                continue
            dist_en[nb] = d + 1
            dq.append((nb, d + 1))
    mine = 0
    theirs = 0
    for cell, dm in dist_me.items():
        de = dist_en.get(cell, INF)
        if dm < de:
            mine += 1
        elif de < dm:
            theirs += 1
        # equal -> contested, skip
    for cell in dist_en:
        if cell not in dist_me:
            theirs += 1
    return mine, theirs


def _enemy_reach_cells(enemy_head, blocked, w, h, steps):
    """BFS: set of cells the enemy head can reach within `steps` moves.
    Used to make the deep self-survival sim ENEMY-AWARE: cells the enemy can
    occupy soon are treated as blocked, so we detect enemy-assisted seals
    (funneling us into a wall pocket) that pure self-sim misses."""
    from collections import deque
    seen = {enemy_head: 0}
    dq = deque([enemy_head])
    while dq:
        c = dq.popleft()
        if seen[c] >= steps:
            continue
        for nb in _neighbors(c):
            if _in_bounds(nb, w, h) and nb not in blocked and nb not in seen:
                seen[nb] = seen[c] + 1
                dq.append(nb)
    return set(seen)


def _deep_self_survival(head, my_body_cells, static_blocked, w, h, depth=8):
    """Greedily simulate our own snake forward `depth` turns, each turn moving
    to the neighbor that maximizes flood-fill space (tail retreats each turn).
    Returns (turns_survived, min_space_seen). This catches multi-turn coil
    traps that 2-ply lookahead misses: a corridor keeps shrinking each turn
    even when the immediate flood-fill still looks large.
    Enemy is ignored here (this is a pure self-trap detector) but enemy body
    cells are included in static_blocked to be conservative.
    """
    body = list(my_body_cells)  # head-first list of (x,y)
    turns = 0
    min_space = 10 ** 9
    for _ in range(depth):
        h0 = body[0]
        # occupied = all body except the tail (which vacates as we move,
        # assuming no growth in this short horizon)
        occ = set(body[:-1]) | static_blocked
        best_cell = None
        best_space = -1
        for nb in _neighbors(h0):
            if not _in_bounds(nb, w, h):
                continue
            if nb in occ:
                continue
            sp = _flood_fill(nb, occ, w, h, limit=None)
            if sp > best_space:
                best_space = sp
                best_cell = nb
        if best_cell is None:
            break  # dead end reached
        turns += 1
        if best_space < min_space:
            min_space = best_space
        # advance: prepend new head, drop tail
        body = [best_cell] + body[:-1]
    if min_space == 10 ** 9:
        min_space = 0
    return turns, min_space


def move(game_state):
    try:
        return _decide(game_state)
    except Exception:
        return {"move": "up"}


def _decide(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_body = [(s["x"], s["y"]) for s in you["body"]]
    head = my_body[0]
    my_len = you.get("length", len(my_body))
    my_health = you["health"]

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]

    # Determine which snakes just ate (tail duplicated => will grow, tail stays).
    # Build set of occupied body cells; tail cells vacate next turn unless grown.
    occupied = set()  # cells blocked next turn (bodies minus vacating tails)
    all_bodies = {}   # snake id -> list of cells
    enemy_heads = []  # (head_cell, length) for enemies
    snakes_bodies = []  # (body_cells_list, grew_bool) for time-aware fill

    for sn in snakes:
        body = [(s["x"], s["y"]) for s in sn["body"]]
        all_bodies[sn["id"]] = body
        # Tail vacates unless the last two cells coincide (just ate / start).
        grew = len(body) >= 2 and body[-1] == body[-2]
        # Add all cells except tail (if it will move away).
        for i, cell in enumerate(body):
            if i == len(body) - 1 and not grew:
                continue  # tail will move away
            occupied.add(cell)
        snakes_bodies.append((body, grew))
        if sn["id"] != you["id"]:
            enemy_heads.append((body[0], sn.get("length", len(body))))

    # Cells an enemy head could move into next turn (for head-to-head).
    # Map cell -> max enemy length that could reach it.
    enemy_next = {}
    for eh, elen in enemy_heads:
        for nb in _neighbors(eh):
            if not _in_bounds(nb, w, h):
                continue
            enemy_next[nb] = max(enemy_next.get(nb, 0), elen)

    candidates = []
    for mv, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in occupied:
            continue
        # Head-to-head: losing (enemy >= our length) is deadly.
        h2h_len = enemy_next.get(nxt, 0)
        h2h_loss = h2h_len >= my_len
        h2h_win = 0 < h2h_len < my_len  # we'd win if they go there
        candidates.append((mv, nxt, h2h_loss, h2h_win))

    if not candidates:
        # No non-colliding legal move; pick the least-bad in-bounds move.
        # Rank: prefer cells not hit by an equal/longer enemy head, then more
        # flood-fill space (a vacating tail we may survive on), then off-wall.
        best_fb = None
        best_fb_score = None
        for mv, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(nxt, w, h):
                continue
            sc = 0.0
            if enemy_next.get(nxt, 0) >= my_len:
                sc -= 100.0  # likely head-to-head loss
            # Space if we treat all bodies as blocked (conservative).
            sc += _flood_fill(nxt, occupied | {nxt}, w, h, limit=w * h) * 5.0
            if best_fb_score is None or sc > best_fb_score:
                best_fb_score = sc
                best_fb = mv
        return {"move": best_fb or "up"}

    # Prefer moves without head-to-head loss if any exist.
    safe = [c for c in candidates if not c[2]]
    pool = safe if safe else candidates

    # Track the longest enemy so we can stay competitive on length. A key loss
    # vector vs a smart opponent is falling BEHIND in length: once the enemy is
    # significantly longer it can cut us off / win head-to-heads. So we eat to
    # keep pace, not just when starving.
    max_enemy_len = 0
    for _eh, _el in enemy_heads:
        if _el > max_enemy_len:
            max_enemy_len = _el

    # Health-driven food desire (survival) OR competitive-growth desire: eat
    # unless we are already comfortably longer than every enemy.
    starving = my_health < 45 or my_len < 5
    # Behind on length OR the enemy is growing fast: eat aggressively. Vs a
    # smart opponent that grows quickly, falling behind early is our #1 loss
    # vector (it out-lengths us and cuts us off / wins H2H). Consider ourselves
    # "behind" if not clearly ahead by >=2.
    behind_or_even = my_len <= max_enemy_len + 1  # not clearly longer
    # When we are COMFORTABLY longer than the opponent, we do NOT need to grow.
    # Chronic loss vector vs amphibious-arthur: we grow to L30-44 while the
    # opponent stays L6-23, then self-coil and box ourselves in. Once we hold a
    # solid length lead, extra length only makes self-coiling MORE likely, so we
    # actively AVOID food to keep the body short and manageable.
    clearly_ahead = (not starving) and (my_len >= max_enemy_len + 3) and (my_len >= 8)
    want_food = starving or behind_or_even
    # Choose target food with a SAFETY-aware ranking rather than raw nearest.
    # Loss analysis (vs ccSnake): our #1 loss vector is chasing food into an
    # edge/corner region while an enemy is closer to it (or between us and the
    # exit), then getting sealed against the wall. So we:
    #   - compute our manhattan distance and the nearest enemy's distance to
    #     each food; skip food an enemy will clearly reach first (they'd take it
    #     and/or trap us going for it).
    #   - add a penalty for food sitting in a corner/edge when it is contested.
    def _corner_edge_risk(f):
        on_v = (f[0] == 0 or f[0] == w - 1)
        on_h = (f[1] == 0 or f[1] == h - 1)
        if on_v and on_h:
            return 2.0   # corner
        if on_v or on_h:
            return 1.0   # edge
        return 0.0

    def _enemy_dist(f):
        best = None
        for eh, _el in enemy_heads:
            d = _manhattan(eh, f)
            if best is None or d < best:
                best = d
        return best if best is not None else 999

    nearest_food_dist = None
    nearest_food = None
    best_food_cost = None
    abs_nearest_food = None
    abs_nearest_dist = None
    for f in food:
        d = _manhattan(head, f)
        ed = _enemy_dist(f)
        risk = _corner_edge_risk(f)
        # Track the absolute closest food (used when CRITICAL / starving).
        if abs_nearest_dist is None or d < abs_nearest_dist:
            abs_nearest_dist = d
            abs_nearest_food = f
        # Base cost = our distance. Penalize contested food (enemy as close or
        # closer) heavily when it sits in a risky edge/corner region: going for
        # it risks being sealed against the wall.
        cost = float(d)
        if ed <= d:
            cost += 4.0 + risk * 8.0   # enemy will contest; corner => avoid
        else:
            cost += risk * 2.0         # uncontested but still mildly risky
        if best_food_cost is None or cost < best_food_cost:
            best_food_cost = cost
            nearest_food_dist = d
            nearest_food = f

    # CRITICAL health: about to starve. Loss vector (vs coreyja__jump-flooding,
    # sim_221): we wandered the bottom edge with health 8->0 and STARVED while
    # food existed on the board. When health is low relative to the distance to
    # the nearest food, survival by eating overrides the safety-aware food
    # ranking AND (below) the edge/corner positioning penalties. Use the
    # ABSOLUTE nearest food and leave enough health buffer to reach it.
    critical = False
    if abs_nearest_food is not None:
        # Need health > distance (+small buffer) or we die en route. Trigger
        # emergency mode when health is within a safety margin of that need.
        if my_health <= abs_nearest_dist + 4 or my_health <= 20:
            critical = True
            nearest_food = abs_nearest_food
            nearest_food_dist = abs_nearest_dist

    best_move = None
    best_score = None
    total_free = w * h
    my_tail = my_body[-1]

    for mv, nxt, h2h_loss, h2h_win in pool:
        # Simulate our body after moving: add new head, drop tail (approx).
        new_blocked = set(occupied)
        new_blocked.add(nxt)
        # Static flood fill (conservative) counts reachable free area now.
        space_static = _flood_fill(nxt, new_blocked, w, h, limit=total_free)
        # Time-aware reachable area: accounts for tails retreating so we don't
        # over-penalize following our own (or the enemy's) tail. Use the larger
        # of the two so long snakes recognize corridors they can survive.
        static_bl = {nxt}
        space_t = _reachable_with_tails(nxt, static_bl, snakes_bodies, w, h,
                                        limit=total_free)
        space = max(space_static, space_t)

        # Tail-access check: after this move, can we still reach our own tail's
        # region? If yes we are almost never trapped (we can chase our tail).
        # Use the time-aware fill's reachable set to test tail reachability.
        tail_reach = _can_reach(nxt, my_tail, new_blocked, snakes_bodies, w, h)

        # 1-ply lookahead: how many escape options remain after this move.
        escapes = _future_safe_moves(nxt, new_blocked, w, h)

        # 2-ply space lookahead: after moving to nxt, find the best space we
        # could reach on the FOLLOWING move. If every follow-up is cramped,
        # this move is leading us into a trap even if `space` looks okay now.
        best_next_space = 0
        # Deeper anti-coil signal: the *worst-case* follow-up space (the tightest
        # corridor 2 steps out). The single-max 2-ply lookahead can rate a coiling
        # move and an escaping move equally when both still reach the whole board;
        # tracking the MIN over follow-up cells discriminates the coil (which forces
        # us into progressively tighter space) from a true escape toward open board.
        worst_next_space = None
        for nb in _neighbors(nxt):
            if not _in_bounds(nb, w, h):
                continue
            if nb in new_blocked:
                continue
            ns = _reachable_with_tails(nb, {nxt, nb}, snakes_bodies, w, h,
                                       limit=total_free)
            if ns > best_next_space:
                best_next_space = ns
            if worst_next_space is None or ns < worst_next_space:
                worst_next_space = ns
        if worst_next_space is None:
            worst_next_space = 0

        # H2H-aware follow-up safety: count follow-up cells from nxt that are
        # neither blocked nor an equal/longer-enemy head-to-head cell. If a move
        # leaves us with NO such follow-up, next turn we are forced into an H2H
        # loss or a wall (the sim_38 tie pattern: coiling into a pocket whose
        # only exit is an H2H cell). Penalize proportionally.
        safe_followups = 0
        for nb in _neighbors(nxt):
            if not _in_bounds(nb, w, h):
                continue
            if nb in new_blocked:
                continue
            if enemy_next.get(nb, 0) >= my_len:
                continue  # forced H2H loss on the follow-up
            safe_followups += 1
        if safe_followups == 0:
            score_h2h_trap = -300.0
        else:
            score_h2h_trap = 0.0

        score = 0.0
        # Space is king: staying alive requires room.
        score += space * 10.0
        # Strong bonus for keeping access to our own tail (anti-coil / anti-trap).
        # If we can chase our tail we can almost always survive indefinitely.
        if tail_reach:
            score += 120.0
        else:
            score -= 200.0
        # Reward keeping a large follow-up region (trap avoidance, 2-ply).
        score += best_next_space * 10.0
        if best_next_space < my_len:
            score -= (my_len - best_next_space) * 60.0
        # Penalize moves whose TIGHTEST follow-up corridor is smaller than our
        # body -- the deep self-coil signal (all historical losses vs this
        # opponent were our own coils while long + healthy).
        if worst_next_space < my_len:
            score -= (my_len - worst_next_space) * 30.0
        score += score_h2h_trap

        # DEEP SELF-SURVIVAL SIM (anti-coil): 2-ply lookahead can't see traps
        # that develop 5+ turns out when an enemy is actively sealing us into a
        # corridor (loss vector sim_104: we were L17 healthy, funneled into a
        # bottom-left pocket over ~6 turns and boxed ourselves in). Simulate our
        # own greedy survival forward from this move; if we die within the horizon
        # or the corridor keeps shrinking below our length, downrank strongly.
        enemy_body_cells = set()
        for body, _grew in snakes_bodies:
            for c in body:
                enemy_body_cells.add(c)
        # remove our own body (we model it dynamically); keep enemy bodies static
        sim_static = enemy_body_cells - set(my_body)
        sim_body = [nxt] + my_body[:-1]
        # Depth scales with our length: the longer we are, the further ahead a
        # coil develops, so a fixed depth-8 horizon can't see it (loss vector vs
        # amphibious-arthur: we die at L30-44 by coiling). Cap for speed.
        deep_depth = min(20, max(8, my_len // 2))
        surv_turns, min_sp = _deep_self_survival(nxt, sim_body, sim_static, w, h, depth=deep_depth)
        if surv_turns < deep_depth:
            # we hit a dead-end within the horizon -> strong coil penalty
            score -= (deep_depth - surv_turns) * 45.0
        if min_sp < my_len:
            score -= (my_len - min_sp) * 6.0

        # ENEMY-AWARE DEEP SURVIVAL (anti enemy-assisted seal): the pure self-sim
        # above ignores the enemy, so it misses funnels where the enemy actively
        # walls off our escape (loss vector: sim_248/sim_28 -- we were long+healthy,
        # the enemy body + its short-horizon reachable cells sealed us into a coil
        # pocket). We flood the cells the ENEMY head can reach within a few moves
        # and treat them as blocked, then re-run the greedy self-sim. If we die
        # within the horizon under this conservative model, downrank the move.
        # Only apply when we have a real body (avoids early-game over-caution).
        if my_len >= 8 and enemy_heads:
            blocked_now = enemy_body_cells | set(my_body)
            enemy_soon = set()
            for eh, _el in enemy_heads:
                enemy_soon |= _enemy_reach_cells(eh, blocked_now, w, h, 4)
            sim_static_e = (enemy_body_cells | enemy_soon) - set(my_body)
            # don't block the cell we're actually moving into
            sim_static_e.discard(nxt)
            e_surv, e_minsp = _deep_self_survival(nxt, sim_body, sim_static_e, w, h, depth=8)
            if e_surv < 8:
                score -= (8 - e_surv) * 22.0

        # VORONOI TERRITORY CONTROL: the smart opponent (jump-flooding) plays a
        # Voronoi/territory strategy and can CONFINE us into a small corner strip
        # where we then STARVE or self-trap (observed losses: sim_244 starvation
        # while pinned in top-left, sim_238/sim_75 corner seal). Reward moves that
        # keep/expand OUR reachable territory relative to the enemy's. This pulls
        # us toward contesting the open board instead of being boxed into a corner.
        enemy_cells = [eh for eh, _el in enemy_heads]
        if enemy_cells:
            my_terr, en_terr = _voronoi_owned(nxt, enemy_cells, new_blocked, w, h)
            score += my_terr * 2.5
            # If the enemy would own much more of the board than us, we're being
            # confined -- penalize hard so we break out toward open space early.
            terr_diff = my_terr - en_terr
            if terr_diff < 0:
                score += terr_diff * 2.0  # negative -> penalty
            # Being confined to a tiny fraction is the pin-in-corner death; if our
            # territory is very small relative to the board, downrank strongly.
            if my_terr < my_len + 2:
                score -= (my_len + 2 - my_terr) * 8.0

        # Avoid moving into a cell with no follow-up (guaranteed death next turn).
        if escapes == 0:
            score -= 500.0
        elif escapes == 1:
            score -= 40.0

        # Strongly avoid tight spaces relative to our length.
        if space < my_len:
            score -= (my_len - space) * 50.0
        # Extra CONSERVATIVE check on the STATIC fill: the time-aware fill can
        # be over-optimistic about tails vacating; if the immediately-reachable
        # (static) area is already smaller than our body, we're very likely
        # walking into a self-trap corridor. Penalize this directly.
        if space_static < my_len:
            score -= (my_len - space_static) * 15.0

        # Enemy-contested space: the time-aware fill trusts enemy tails to
        # vacate, but the enemy can keep feeding body into a pocket entrance to
        # seal us in (this caused our only losses -- coiling into a wall pocket
        # while an enemy sealed the mouth). Compute a conservative fill that
        # ALSO treats every cell the enemy head can reach next turn as blocked.
        # If that contested area is smaller than our length, we're at risk of
        # being sealed; penalize proportionally.
        if enemy_next:
            contested_blocked = set(new_blocked)
            for ec in enemy_next:
                contested_blocked.add(ec)
            space_contested = _flood_fill(nxt, contested_blocked | {nxt}, w, h,
                                          limit=total_free)
            if space_contested < my_len:
                score -= (my_len - space_contested) * 18.0

        # Head-to-head win bonus (eliminate shorter enemy).
        if h2h_win:
            score += 200.0
        if h2h_loss:
            score -= 1000.0

        # Food incentive. We weight food more heavily than before because the
        # main loss vector vs a smart opponent is falling behind in LENGTH and
        # then getting cut off. If we're starving, chase hard. If we're just
        # not clearly longer than the enemy, still pull toward food to grow.
        # Only when we're comfortably longer do we relax food pursuit.
        if nearest_food is not None:
            d_after = _manhattan(nxt, nearest_food)
            if critical:
                # Emergency: get to food NOW. Dominates edge/corner penalties.
                score -= d_after * 40.0
                if nxt == nearest_food:
                    score += 300.0
            elif starving:
                score -= d_after * 11.0
                if nxt == nearest_food:
                    score += 90.0
            elif behind_or_even:
                score -= d_after * 7.0
                if nxt == nearest_food:
                    score += 70.0
            elif clearly_ahead:
                # We hold a solid length lead: growing further only increases our
                # self-coil risk (chronic loss vector: we grow to L30-44 then
                # self-coil). Actively AVOID eating: strongly penalize landing on
                # food and reward keeping distance from it so we stay short and
                # manageable. Safety/space signals still dominate.
                if nxt == nearest_food:
                    score -= 120.0
                else:
                    score += min(d_after, 6) * 4.0
            else:
                # We're modestly longer; only mild pull so we don't ignore free
                # nearby food but prioritize safe positioning/space.
                score -= d_after * 1.5
                if nxt == nearest_food:
                    score += 15.0

        # Prefer to stay away from walls/corners (more mobility, avoids the
        # canonical self-trap: hugging a wall into a corner while long).
        # Corners are especially dangerous, so penalize them heavily; edges
        # moderately. This is scaled up relative to before because the two
        # observed losses vs a smart opponent were BOTH corner self-traps.
        on_v_edge = (nxt[0] == 0 or nxt[0] == w - 1)
        on_h_edge = (nxt[1] == 0 or nxt[1] == h - 1)
        edge_pen = 0
        if on_v_edge:
            edge_pen += 1
        if on_h_edge:
            edge_pen += 1
        # Base edge penalty (mild) + corner penalty (strong) so that when a
        # non-edge alternative exists with comparable space we take it.
        # Scale by length: corner/edge self-traps are only dangerous when we
        # are LONG (a short snake can afford to graze edges to grab food).
        len_scale = 1.0 + max(0, my_len - 4) * 0.18
        # When CRITICAL (about to starve), suppress edge/corner positioning
        # penalties so they can't steer us away from wall-adjacent food we need
        # to survive. Safety (space/H2H) penalties still apply below.
        edge_w = 2.0 if critical else 9.0
        corner_w = 8.0 if critical else 40.0
        score -= edge_pen * edge_w * len_scale
        if on_v_edge and on_h_edge:
            score -= corner_w * len_scale  # actual corner cell
        # Distance-from-center nudge: gently pull toward the middle so we don't
        # settle into wall-hugging patrols that end in a corner box-in.
        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        center_dist = abs(nxt[0] - cx) + abs(nxt[1] - cy)
        score -= center_dist * 0.15

        # Edge-shadow penalty: the observed losses vs the smart opponent were
        # both cases where we moved ONTO an edge/corner and the enemy shadowed
        # us one lane inward, running parallel and sealing our exits until we hit
        # the corner. Detect this: if nxt is on an edge and an enemy head is on
        # the adjacent inward lane close to us, we're at risk of being walled in.
        # Estimate how far we can run along the edge before the corner and how
        # much the enemy can seal; penalize thin edge corridors near an enemy.
        if (on_v_edge or on_h_edge) and enemy_heads:
            ex, ey = nxt
            # nearest enemy head
            ehead, _elen = min(enemy_heads, key=lambda e: _manhattan(nxt, e[0]))
            edist = _manhattan(nxt, ehead)
            if edist <= 3:
                # Count free edge cells reachable running along the edge away
                # from the nearest corner (rough proxy for room before box-in).
                run = 0
                if on_h_edge and not on_v_edge:
                    # move horizontally; try both directions, take the max run
                    for step in (1, -1):
                        r = 0
                        cx2 = ex
                        while True:
                            cx2 += step
                            c = (cx2, ey)
                            if not _in_bounds(c, w, h) or c in new_blocked:
                                break
                            r += 1
                        run = max(run, r)
                elif on_v_edge and not on_h_edge:
                    for step in (1, -1):
                        r = 0
                        cy2 = ey
                        while True:
                            cy2 += step
                            c = (ex, cy2)
                            if not _in_bounds(c, w, h) or c in new_blocked:
                                break
                            r += 1
                        run = max(run, r)
                else:
                    run = 0  # corner: no run at all
                # If the run before we hit an obstacle/corner is short relative
                # to our length AND the enemy is right there to seal it, this is
                # the classic edge-trap. Penalize strongly.
                if run < my_len:
                    score -= (my_len - run) * 18.0

        if best_score is None or score > best_score:
            best_score = score
            best_move = mv

    return {"move": best_move or pool[0][0]}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
