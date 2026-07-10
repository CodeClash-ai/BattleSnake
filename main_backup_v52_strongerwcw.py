"""
CodeClash BattleSnake bot (v5).

Strategy (see README_agent.md):
  - Never move into walls, own body, or other snake bodies.
  - Correct tail handling (tail vacates unless the snake just ate).
  - Flood-fill each candidate move for reachable space AND a "survival" check:
    the reachable space must comfortably exceed our body length or we treat it
    as a trap. This prevents coiling ourselves into a dead pocket (the failure
    mode that lost round-2 games vs csauve__bookworm).
  - Tail-reachability as a strong secondary safety.
  - Head-to-head: avoid squares an equal/longer enemy head can reach; win them
    when strictly longer.
  - Aggression: when longer, pressure the enemy toward walls / losing H2H.
  - Seek food when it is safe and especially when health is low.
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


def _neighbors(p):
    x, y = p
    return ((x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y))


def _build_obstacles(board, exclude_tails=True):
    """Occupied cells. Tails excluded when the snake will move (didn't just eat)."""
    obstacles = set()
    for snake in board["snakes"]:
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if exclude_tails and i == n - 1 and n >= 2:
                tail = body[-1]
                pre = body[-2]
                if (tail["x"], tail["y"]) != (pre["x"], pre["y"]):
                    continue
            obstacles.add(cell)
    return obstacles


def _flood_fill(start_cell, obstacles, w, h, limit=None):
    if start_cell in obstacles or not _in_bounds(start_cell, w, h):
        return 0
    seen = {start_cell}
    stack = [start_cell]
    count = 0
    while stack:
        cur = stack.pop()
        count += 1
        if limit is not None and count >= limit:
            return count
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return count


def _timed_space(start_cell, board, you, w, h, food_set, limit=None):
    """Flood-fill that accounts for our OWN body vacating over time.

    We BFS from start_cell (the move destination). A cell occupied by our
    body segment `i` (0=head) frees up after `my_len - i` steps (the tail
    end vacates first). We can enter such a cell only if we reach it at a
    step >= the time it frees. Enemy bodies are treated as static obstacles
    (conservative). This detects shrinking-corridor self-traps that a plain
    flood-fill misses.
    """
    body = you["body"]
    my_len = len(body)
    # Map our body cell -> time it becomes free (steps from now).
    # Segment i (0=head) vacates at step (my_len - i) roughly, since tail
    # moves each turn. Eating extends body; ignore that (conservative).
    my_free = {}
    for i, seg in enumerate(body):
        c = (seg["x"], seg["y"])
        # earliest step this cell is free
        my_free[c] = my_len - i
    # Enemy bodies static (their tails vacate too but treat as blocked = safe).
    enemy_block = set()
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        for seg in snake["body"]:
            enemy_block.add((seg["x"], seg["y"]))

    from collections import deque as _dq
    # We arrive at start_cell at step 1.
    if not _in_bounds(start_cell, w, h):
        return 0
    if start_cell in enemy_block:
        return 0
    # start_cell might be our own tail freeing; check free time.
    sc_free = my_free.get(start_cell, 0)
    if sc_free > 1:
        return 0
    seen = {start_cell}
    q = _dq([(start_cell, 1)])
    count = 0
    while q:
        cur, t = q.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in enemy_block:
                continue
            nt = t + 1
            free = my_free.get(nb, 0)
            if free > nt:
                # cell still occupied by our body when we'd arrive
                continue
            seen.add(nb)
            q.append((nb, nt))
    return count


def _reachable(start_cell, target, obstacles, w, h):
    if start_cell == target:
        return True
    if start_cell in obstacles or not _in_bounds(start_cell, w, h):
        return False
    seen = {start_cell}
    stack = [start_cell]
    while stack:
        cur = stack.pop()
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb == target:
                return True
            nx, ny = nb
            if nb in seen or nx < 0 or nx >= w or ny < 0 or ny >= h or nb in obstacles:
                continue
            seen.add(nb)
            stack.append(nb)
    return False


def _bfs_dist(start_cell, targets, obstacles, w, h):
    if not targets:
        return None
    if start_cell in targets:
        return 0
    seen = {start_cell}
    q = deque([(start_cell, 0)])
    while q:
        cur, d = q.popleft()
        cx, cy = cur
        for nb in ((cx, cy + 1), (cx, cy - 1), (cx - 1, cy), (cx + 1, cy)):
            if nb in seen:
                continue
            nx, ny = nb
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                continue
            if nb in targets:
                return d + 1
            if nb in obstacles:
                continue
            seen.add(nb)
            q.append((nb, d + 1))
    return None


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        return {"move": _safe_fallback(game_state)}


def _safe_fallback(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head_seg = game_state["you"]["body"][0]
        head = (head_seg["x"], head_seg["y"])
        obstacles = _build_obstacles(board)
        best = None
        best_space = -1
        for name, (dx, dy) in DIRS.items():
            nxt = (head[0] + dx, head[1] + dy)
            if _in_bounds(nxt, w, h) and nxt not in obstacles:
                sp = _flood_fill(nxt, obstacles, w, h, limit=w * h)
                if sp > best_space:
                    best_space = sp
                    best = name
        if best:
            return best
    except Exception:
        pass
    return "up"


def _choose_move(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    body = you["body"]
    head = (body[0]["x"], body[0]["y"])
    my_len = len(body)
    health = you["health"]

    obstacles = _build_obstacles(board)

    # Other snakes' heads for head-to-head handling.
    enemies = []
    for snake in board["snakes"]:
        if snake["id"] == you["id"]:
            continue
        eh = snake["body"][0]
        enemies.append({
            "head": (eh["x"], eh["y"]),
            "len": len(snake["body"]),
            "body": [(s["x"], s["y"]) for s in snake["body"]],
        })

    # Cells an enemy head could move into next turn -> max enemy length there.
    enemy_next = {}
    for e in enemies:
        for nb in _neighbors(e["head"]):
            if not _in_bounds(nb, w, h):
                continue
            enemy_next[nb] = max(enemy_next.get(nb, 0), e["len"])

    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    food_set = set(food)

    total_cells = w * h
    my_tail = (body[-1]["x"], body[-1]["y"])
    candidates = []
    for name, (dx, dy) in DIRS.items():
        nxt = (head[0] + dx, head[1] + dy)
        if not _in_bounds(nxt, w, h):
            continue
        if nxt in obstacles:
            continue

        h2h_len = enemy_next.get(nxt, 0)
        loses_h2h = h2h_len >= my_len
        wins_h2h = h2h_len > 0 and h2h_len < my_len

        sim_obstacles = set(obstacles)
        eating_now = nxt in food_set
        if not eating_now:
            sim_obstacles.discard(my_tail)

        space = _flood_fill(nxt, sim_obstacles, w, h, limit=total_cells)
        tail_reachable = _reachable(nxt, my_tail, sim_obstacles, w, h)

        contested_obstacles = set(sim_obstacles)
        for ec in enemy_next:
            if ec != nxt:
                contested_obstacles.add(ec)
        contested_space = _flood_fill(nxt, contested_obstacles, w, h, limit=total_cells)

        # Time-aware space: simulate our body vacating as we advance. Detects
        # shrinking-corridor self-traps that plain flood-fill misses.
        timed_space = _timed_space(nxt, board, you, w, h, food_set, limit=total_cells)

        candidates.append({
            "name": name,
            "cell": nxt,
            "h2h_len": h2h_len,
            "loses_h2h": loses_h2h,
            "wins_h2h": wins_h2h,
            "space": space,
            "contested_space": contested_space,
            "timed_space": timed_space,
            "tail_reachable": tail_reachable,
            "reaches_food": eating_now,
            "food_md": (min((_manhattan(nxt,(fx,fy)) for fx,fy in food_set), default=999)),
        })

    if not candidates:
        return _safe_fallback(game_state)

    # Survival: a move is "safe space" if we can reach our tail OR the reachable
    # space is at least our length (we won't box ourselves in immediately).
    def survivable(c):
        # Time-aware: the space we can actually occupy as our body advances
        # must hold our length. This is the real self-trap guard. Fall back
        # to tail-reachability + ample plain space for edge cases.
        # BUGFIX (v18): timed_space can be wildly over-optimistic for a tiny
        # pocket (it lets the flood "escape" through our own neck cells that
        # vacate over time, but physically our advancing body seals them). A
        # cell whose PLAIN reachable space is far smaller than our length is a
        # real self-trap regardless of timed_space. Gate on plain space too.
        if c["space"] < min(my_len, 4):
            return False
        if c["timed_space"] >= my_len:
            return True
        return c["tail_reachable"] and c["space"] >= my_len + 2

    # Prefer moves that don't lose head-to-heads if any exist.
    safe = [c for c in candidates if not c["loses_h2h"]]
    pool = safe if safe else candidates

    # STARVATION FIX (jump-flooding loss mode): an equal-length enemy head next to
    # us makes every food-ward move a "loses_h2h" (h2h_len >= my_len), so a SHORT,
    # HUNGRY snake flees forever and STARVES (died len4 hp2 with food on board). But
    # an EQUAL-length H2H is at worst a TIE, and the enemy may not even move there.
    # When we are short & hungry, treat equal-length-h2h survivable moves as usable
    # (still exclude moves where a strictly LONGER enemy could take the cell = real loss).
    # TIE FIX (jump-flooding round 1: 53 ties, mostly turn ~6 equal-len H2H at high
    # health). A WIN >> a TIE, so NEVER voluntarily take an equal-length H2H when a
    # genuinely safe move with adequate space exists. Only relax when we are truly
    # hungry (low health) OR when every safe move is inadequate (would self-trap/flee
    # into a tiny pocket) -> then a possible tie beats a certain loss/starvation.
    _lead0 = my_len - max((e["len"] for e in enemies), default=0)
    _shungry = my_len < 8 and (health < 80 or _lead0 < 1)
    # is there a safe (non-h2h) move with real breathing room?
    _safe_ok = [c for c in safe if c["space"] >= min(my_len, 4)]
    if _shungry:
        eq_ok = [c for c in candidates
                 if c["loses_h2h"] and c["h2h_len"] == my_len and c not in safe]
        # keep only survivable-ish ones (won't self-trap)
        eq_ok = [c for c in eq_ok if c["space"] >= min(my_len, 4)]
        # TIE FIX (jump-flooding round 1: 53 ties, mostly turn ~6 equal-len H2H at
        # HIGH health). A WIN >> a TIE. If a genuinely safe move with adequate space
        # exists AND we are healthy, ONLY accept an equal-H2H move when it reaches
        # food (real growth benefit); otherwise avoid the voluntary tie. When there
        # is NO adequate safe move (would flee into a tiny pocket / starve later),
        # keep the equal-H2H moves (a possible tie beats a certain loss/starvation).
        # A WIN >> a TIE: when a genuinely safe move exists, only accept a
        # voluntary equal-H2H if it makes REAL food progress (reaches food, or
        # gets strictly closer to food than the best safe move -> food-race /
        # anti-starvation). Otherwise we would just walk into a needless tie
        # (round-2 ties clustered at turn ~19: wandering len-4 snakes colliding).
        if _safe_ok:
            # When healthy, NEVER voluntarily take an equal-H2H unless it eats
            # NOW (immediate growth). A tie is 0 pts; a safe move keeps us alive
            # to WIN. Only when getting hungry (health < 50) do we allow an
            # equal-H2H that makes real food progress (closer than any safe move)
            # -> preserves the anti-starvation fix without needless ties.
            # A WIN >> a TIE. With a genuinely safe move available, only accept an
            # equal-H2H that EATS food NOW (immediate growth that breaks the length
            # deadlock). We never voluntarily walk INTO a tie just to shave a couple
            # cells off the food route -- the food-race scoring (fdist*20 when
            # short_hungry) already pulls us toward food from the SAFE cell over the
            # next turns, so we still eat without the needless collision.
            # A WIN >> a TIE. Accept an equal-H2H only if it EATS food NOW, OR if
            # (short & hungry) NO safe move makes any food progress -- i.e. fleeing
            # the h2h moves us strictly FARTHER from all food than staying put would
            # (genuine anti-starvation: the h2h is the only route to food). In the
            # needless-tie games a safe move DID make food progress, so we avoid the
            # collision and let the food-race scoring route us there safely.
            _cur_fmd = min((_manhattan(head,(fx,fy)) for fx,fy in food_set), default=999)
            best_safe_fmd = min((c.get("food_md", 999) for c in _safe_ok), default=999)
            if health >= 30 and best_safe_fmd <= _cur_fmd + 1:
                # a safe move at least holds/improves food distance -> no tie needed.
                # When HEALTHY (>=70) with a safe option we don't even need contested
                # food -> avoid the equal-H2H entirely (high-health early ties were
                # both snakes racing the SAME food cell into a mutual-eat collision).
                if health >= 70:
                    # OUTGROWN-WHILE-SHORT FIX (tim-hub loss f588c585): when we are
                    # BEHIND on length (lead <= 0) and the ONLY way to eat this turn
                    # is a contested equal-H2H food cell, take it. Fleeing keeps us
                    # short while the opponent grows and eventually wins the H2H (a
                    # certain LOSS). A tie (0 pts) is no worse than a loss (0 pts), and
                    # if the enemy picks other food we GROW and break the deadlock.
                    # Only allow it when it EATS food NOW (immediate growth) and no
                    # safe move also eats -> we're not creating a needless tie.
                    if _lead0 < 0 and not any(c.get("reaches_food") for c in _safe_ok):
                        eq_ok = [c for c in eq_ok if c.get("reaches_food")]
                    else:
                        eq_ok = []
                else:
                    eq_ok = [c for c in eq_ok if c.get("reaches_food")]
            else:
                eq_ok = [c for c in eq_ok
                         if c.get("reaches_food") or c.get("food_md", 999) < best_safe_fmd]
        if eq_ok:
            pool = safe + eq_ok if safe else (candidates if not eq_ok else eq_ok + candidates)

    # CRITICAL FIX (v16): avoiding a merely POSSIBLE head-to-head must NOT force
    # us into a certain self-trap. If every non-losing-h2h move is NOT survivable
    # (boxes us in), but some h2h-risk move IS survivable with real open space,
    # include those survivable h2h-risk moves in the pool. An h2h against an
    # equal/longer enemy is at worst a TIE (or the enemy may not even move there),
    # whereas a self-trap is a GUARANTEED loss. Real loss games (e.g. 78e77953)
    # died exactly this way: the only non-h2h move led into an 8-cell pocket while
    # the survivable escape was pruned for a possible enemy head collision.
    safe_surv = [c for c in safe if survivable(c)]
    if not safe_surv:
        risky_surv = [c for c in candidates if c["loses_h2h"] and survivable(c)]
        if risky_surv:
            # Only add h2h-risk survivable moves that have clearly MORE space than
            # any safe move (so we escape a trap, not chase a bad H2H needlessly).
            best_safe_space = max((c["timed_space"] for c in safe), default=-1)
            escape = [c for c in risky_surv if c["timed_space"] > best_safe_space + 3]
            if escape:
                pool = safe + escape

    surv = [c for c in pool if survivable(c)]
    pool2 = surv if surv else pool

    # Among survivable, prefer ones with the most space to keep options open.
    max_space = max(c["space"] for c in pool2)
    max_timed = max(c["timed_space"] for c in pool2)

    # Length race: being longer wins head-to-heads and lets us trap the enemy.
    # Seek food unless we are already comfortably longer than the nearest enemy.
    _enemy_max_len = max((e["len"] for e in enemies), default=0)
    _length_lead = my_len - _enemy_max_len
    want_food = health < 75 or my_len < 7 or _length_lead < 3
    # But a BIG, HEALTHY snake that is already at least even on length
    # should NOT race food: chasing edge food while big+healthy is the
    # #1 loss mode vs ccsnake (wall-crawl into a corner, self-trap at hp>90).
    # Turning off want_food re-enables the anti-crawl / tail-follow terms.
    _big_safe = my_len >= 10 and health >= 65 and _length_lead >= 3
    if _big_safe:
        want_food = False

    # FOOD-OWNERSHIP (Voronoi food-race): the dominant loss mode vs the crystal
    # opponent is being OUT-EATEN (opp stays 1-2 longer the whole game, then wins
    # the endgame). To win the food-race we route toward food WE reach strictly
    # BEFORE the enemy (owned food = growth we can secure + deny to the opponent),
    # and avoid committing to food the enemy owns (it grabs it first, we waste
    # turns). Compute BFS distance from our HEAD and from each enemy head to every
    # food using the shared obstacle map (excluding our own tail, which vacates).
    owned_food = set()
    contested_lose_food = set()
    if food_set and enemies:
        own_obs = set(obstacles)
        own_obs.discard(my_tail)
        for fx, fy in food_set:
            my_d = _bfs_dist(head, {(fx, fy)}, own_obs, w, h)
            if my_d is None:
                continue
            # nearest enemy BFS distance to this food (enemies' tails vacate too)
            best_e = None
            for e in enemies:
                e_obs = set(obstacles)
                e_obs.discard(e["body"][-1])
                ed = _bfs_dist(e["head"], {(fx, fy)}, e_obs, w, h)
                if ed is None:
                    continue
                if best_e is None or ed < best_e:
                    best_e = ed
            if best_e is None:
                owned_food.add((fx, fy))
            elif my_d < best_e:
                owned_food.add((fx, fy))
            elif my_d > best_e:
                contested_lose_food.add((fx, fy))
            # equal distance -> genuine contest, leave neutral (H2H logic handles)

    # CORNER-FOOD TRAP AVOIDANCE: food sitting on a wall/corner is a death lure
    # when an equal/longer enemy is at least as close to it — chasing it walks us
    # into a wall-crawl toward a corner where the longer enemy pins us (the exact
    # round-3 loss mode vs Xe__since, games 1095cb4f & ccac596d: both crawled the
    # bottom wall toward corner food at (10,0) while outgrown -> cornered & died).
    # Mark such food as "trap food" so we don't get the strong food pull toward it
    # unless our health is genuinely low (then we must eat regardless).
    trap_food = set()
    # A SHORT snake that is behind on length MUST eat (starvation is the #1 loss
    # mode vs jump-flooding: len4 hp2 death while 7-19 food on board). Only apply
    # edge/corner trap-food avoidance once we are safely fed (len>=7 and hp>=50).
    _fed = my_len >= 7 and health >= 50
    if food_set and enemies and _length_lead < 2 and health >= 40 and _fed:
        for fx, fy in food_set:
            f_on_edge = (fx == 0 or fx == w - 1 or fy == 0 or fy == h - 1)
            if not f_on_edge:
                continue
            my_fd = _manhattan(head, (fx, fy))
            # is an equal/longer enemy at least as close to this food?
            enemy_closer = False
            for e in enemies:
                if e["len"] < my_len:
                    continue
                if _manhattan(e["head"], (fx, fy)) <= my_fd:
                    enemy_closer = True
                    break
            if enemy_closer:
                trap_food.add((fx, fy))
    # SMALL-SNAKE edge-food-near-enemy trap: a small snake climbing a wall toward
    # edge food while an equal/longer enemy is already parked near that food's
    # corner region gets boxed into the corner (loss sim_214: len4 climbed right
    # wall to corner (10,10) as enemy sat at the top). ONLY flag when OTHER food
    # exists (so we never starve) and we are healthy.
    if food_set and enemies and my_len < 7 and health >= 55 and len(food_set) >= 2:
        for fx, fy in food_set:
            walls_f = (fx == 0) + (fx == w - 1) + (fy == 0) + (fy == h - 1)
            if walls_f == 0:
                continue
            my_fd = _manhattan(head, (fx, fy))
            # ANY enemy parked near this wall-food's corner region can box us in
            # even if shorter (it still occupies escape cells). Flag as trap.
            for e in enemies:
                if _manhattan(e["head"], (fx, fy)) <= my_fd + 1:
                    trap_food.add((fx, fy))
                    break
    # CORNER-FOOD trap: a small/mid snake chasing food that sits ON a corner cell
    # (two walls) tends to crawl a wall INTO the corner and self-trap there, even
    # with no enemy nearby (loss game 50aec38e: len6 hp100 crawled x=10 wall to
    # (10,0) corner food & died). Flag corner food as trap when we are not big &
    # health is fine (low health still eats). This softens the food pull toward it.
    if food_set and my_len < 10 and health >= 45 and _fed:
        for fx, fy in food_set:
            walls = (fx == 0) + (fx == w - 1) + (fy == 0) + (fy == h - 1)
            if walls >= 2:
                trap_food.add((fx, fy))
    # BIG-SNAKE wall/corner food trap: a large snake (the #1 loss population vs
    # OliverMKing: L13-28 dying at walls/corners) that chases food sitting ON a
    # wall/corner crawls the perimeter and self-coils into the corner. When we are
    # BIG (len>=13) and healthy (hp>=55) and OTHER (non-wall) food exists, flag the
    # wall/corner food as trap so the food pull is softened -> the anti-wall-crawl
    # term keeps us centered. Gated on other food existing so we never starve; low
    # health (<55) still eats it.
    if food_set and my_len >= 13 and health >= 55:
        nonwall = [f2 for f2 in food_set
                   if (f2[0] != 0 and f2[0] != w - 1 and f2[1] != 0 and f2[1] != h - 1)]
        if nonwall:
            for fx, fy in food_set:
                walls = (fx == 0) + (fx == w - 1) + (fy == 0) + (fy == h - 1)
                if walls >= 1:
                    trap_food.add((fx, fy))
    best = None
    best_key = None
    for c in pool2:
        sim_obstacles = set(obstacles)
        sim_obstacles.discard(my_tail)
        sim_obstacles.discard(c["cell"])
        # Prefer SAFE (non-trap) food for the distance pull. If every food is a
        # corner-trap lure, use the full set but flag it so the pull is softened.
        safe_food = food_set - trap_food
        # FOOD-RACE: when we are NOT comfortably ahead, target food WE OWN (reach
        # strictly first) so we win the growth race & deny the opponent. Only when
        # owned safe food exists; otherwise fall back to all safe food (never
        # starve). Keeps the anti-trap set filtered.
        race_target = None
        if _length_lead < 3 and owned_food:
            race_target = (owned_food - trap_food) or owned_food
        chasing_trap = False
        if race_target:
            bd = _bfs_dist(c["cell"], race_target, sim_obstacles, w, h)
            fdist = bd if bd is not None else (_manhattan(c["cell"], next(iter(race_target))) + 100)
        elif safe_food:
            bd = _bfs_dist(c["cell"], safe_food, sim_obstacles, w, h)
            fdist = bd if bd is not None else (_manhattan(c["cell"], next(iter(safe_food))) + 100)
        elif food_set:
            bd = _bfs_dist(c["cell"], food_set, sim_obstacles, w, h)
            fdist = bd if bd is not None else (_manhattan(c["cell"], food[0]) + 100)
            chasing_trap = True
        else:
            fdist = 0

        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        cdist = abs(c["cell"][0] - cx) + abs(c["cell"][1] - cy)

        score = 0.0
        # Space is the primary survival driver.
        score += c["space"] * 2.0
        # Time-aware space: strongly reward room that survives body advance.
        score += c["timed_space"] * 3.0
        # Reward space we still control even if the enemy pushes toward us.
        score += c["contested_space"] * 1.0
        # Extra reward for having the most space (avoid corridors).
        if c["space"] == max_space:
            score += 6.0
        if c["timed_space"] == max_timed:
            score += 10.0
        # Anti self-coil for VERY big snakes: bias toward the roomiest move.
        if my_len >= 15:
            score -= (max_timed - c["timed_space"]) * 1.0
        # Penalize tight spaces relative to our length (trap risk).
        if c["space"] < my_len + 2:
            score -= (my_len + 2 - c["space"]) * 5.0
        # STRONG penalty when time-aware space can't hold our body (self-trap).
        if c["timed_space"] < my_len:
            score -= (my_len - c["timed_space"]) * 12.0

        # ANTI-SQUEEZE: avoid walking onto a wall/corner cell whose perpendicular
        # escape can be sealed by a nearby enemy. This is the exact failure mode
        # of every match loss (small snake chases edge food into a corner, enemy
        # walls off the exit). Count open, non-losing escape cells from `cell`
        # (excluding where we came from); if few AND an enemy head is close,
        # penalize. Scaled harder when we are small.
        cxn, cyn = c["cell"]
        on_edge = (cxn == 0 or cxn == w - 1 or cyn == 0 or cyn == h - 1)
        if on_edge and enemies:
            walls = (cxn == 0) + (cxn == w - 1) + (cyn == 0) + (cyn == h - 1)
            # open escape cells from this cell (not obstacles, in bounds)
            open_escapes = 0
            for nb in _neighbors(c["cell"]):
                if not _in_bounds(nb, w, h):
                    continue
                if nb == head:
                    continue
                if nb in obstacles and nb != my_tail:
                    continue
                # a cell an enemy of >= our len could take next turn is not a safe escape
                if enemy_next.get(nb, 0) >= my_len:
                    continue
                open_escapes += 1
            nearest_e = min(enemies, key=lambda e: _manhattan(c["cell"], e["head"]))
            edist_e = _manhattan(c["cell"], nearest_e["head"])
            # only worry when an enemy is close enough to seal us (within 4)
            if edist_e <= 4:
                proximity = (5 - edist_e)  # 1..4, bigger when closer
                if walls >= 2:  # corner cell
                    score -= proximity * 8.0
                    if my_len < 8:
                        score -= proximity * 4.0
                elif open_escapes <= 1:  # edge cell with <=1 safe escape
                    score -= proximity * 6.0
                    if my_len < 8:
                        score -= proximity * 3.0

        # WALL-PIN penalty: when moving ALONG a wall toward a nearby equal/longer
        # enemy that shares that wall-side, we risk being cut off & squeezed into
        # the corner (the exact loss mode vs nbw-crystal, game a2115842). Detect a
        # move parallel to a wall whose direction heads toward such an enemy.
        if on_edge and enemies:
            mdx = cxn - head[0]
            mdy = cyn - head[1]
            # moving parallel along a horizontal wall (top/bottom)?
            horiz_wall = (cyn == 0 or cyn == h - 1) and mdx != 0 and mdy == 0
            vert_wall = (cxn == 0 or cxn == w - 1) and mdy != 0 and mdx == 0
            for e in enemies:
                if e["len"] < my_len:
                    continue
                ex, ey = e["head"]
                ed = _manhattan(c["cell"], e["head"])
                if ed > 6:
                    continue
                if horiz_wall:
                    # enemy is in the direction we're moving AND near this wall
                    toward = (mdx > 0 and ex >= cxn) or (mdx < 0 and ex <= cxn)
                    near_wall = abs(ey - cyn) <= 3
                    if toward and near_wall:
                        score -= (7 - ed) * 2.0
                        if my_len < 10:
                            score -= (7 - ed) * 2.0
                elif vert_wall:
                    toward = (mdy > 0 and ey >= cyn) or (mdy < 0 and ey <= cyn)
                    near_wall = abs(ex - cxn) <= 3
                    if toward and near_wall:
                        score -= (7 - ed) * 2.0
                        if my_len < 10:
                            score -= (7 - ed) * 2.0

        # ANTI-WALL-CRAWL: a big, healthy snake hugging the perimeter tends to
        # coil itself into a corner and self-trap (the #1 loss mode vs ccsnake:
        # heads dying at (0,0)/(10,10)/edges at hp 88-100). Nudge such a snake
        # OFF the walls toward open board. dist_to_wall = min dist to any wall
        # (0 on a wall, up to ~5 at center). Only for big+healthy snakes so it
        # never distorts small-snake food-racing (which needs the perimeter food).
        _flooded = len(food_set) >= 10
        _giant = _length_lead >= 3 and my_len >= 10 and _flooded
        # Health 30-59 band: the giant food-flee (fdist*30) is active but the
        # off-wall counter below was gated on health>=60, so a fleeing giant at
        # moderate health wall-crawled into corners with NO counter (tantilla loss
        # sim_73: hp52 crawled (4,8)->wall->corner->death). Add the SAME off-wall
        # pull (25) for _giant snakes in this band only (health>=60 unchanged).
        if _giant and health < 60:
            _dtw = min(cxn, w - 1 - cxn, cyn, h - 1 - cyn)
            score += _dtw * 25.0
        if my_len >= 10 and health >= 60:
            dist_to_wall = min(cxn, w - 1 - cxn, cyn, h - 1 - cyn)
            # GIANT fleeing food gets driven into corners because high-fdist cells
            # are on the perimeter. Strongly dominate that with an off-wall pull so
            # a compact giant on a food-flooded board (stay-small opponent) does NOT
            # wall-crawl into a corner & self-coil (tantilla loss mode: len 14-18
            # coiling at corners).
            if _giant:
                score += dist_to_wall * 25.0
            # Escalate off-wall pull for HUGE snakes: on a 121-cell board a
            # len 40-90 snake that hugs the perimeter WILL coil into a corner
            # and self-trap (eremetic-eric loss mode: len 55-91 crawling walls
            # to death). Keep such a snake in the interior where its own tail
            # vacates cells, so it can coil safely.
            if my_len >= 25:
                _wcw = 11.0
            elif my_len >= 15:
                _wcw = 8.0
            elif my_len >= 12:
                _wcw = 6.0
            else:
                _wcw = 3.5
            score += dist_to_wall * _wcw
        elif chasing_trap and health >= 60:
            # A SMALL healthy snake whose ONLY food is wall/corner-trap food will
            # crawl the perimeter into a corner and self-coil (loss sim_215: len6
            # hp100 chased wall food into corner (0,0) & died). Since all food is a
            # trap lure this turn, nudge OFF the wall toward open board. Narrow:
            # only fires when chasing_trap (no safe food) so it never distorts
            # normal small-snake food-racing toward reachable food.
            dist_to_wall = min(cxn, w - 1 - cxn, cyn, h - 1 - cyn)
            score += dist_to_wall * 3.0

        if health >= 40:
            tail_bonus = 50.0
        elif health >= 20:
            tail_bonus = 15.0
        else:
            tail_bonus = 2.0
        if c["tail_reachable"]:
            score += tail_bonus

        if c["wins_h2h"]:
            score += 5.0 if _length_lead >= 5 else 30.0

        # Aggression: when clearly longer, close on the enemy head to pressure
        # it toward walls / losing head-to-heads. Only when we have room.
        if enemies:
            nearest = min(enemies, key=lambda e: _manhattan(head, e["head"]))
            if my_len > nearest["len"] + 1 and health >= 35 and c["space"] >= my_len + 2:
                edist = _manhattan(c["cell"], nearest["head"])
                if _length_lead < 5:
                    score -= edist * 2.0

        # TAIL-FOLLOW tie-breaker: for a very large, healthy snake, gently
        # prefer staying near our own tail so the body stays a compact,
        # unwind-able coil (mitigates long-game self-trap). Small weight so it
        # only breaks ties, never overriding space/survival decisions.
        if my_len >= 12 and health >= 50 and not want_food:
            tdist = _manhattan(c["cell"], my_tail)
            if my_len >= 25:
                tw = 3.0
            elif _length_lead >= 4:
                tw = 1.5
            else:
                tw = 0.6
            score -= tdist * tw

        # When every food is a corner-trap lure, soften the pull so we don't
        # dive into the wall-crawl-to-corner death (still eat if health is low).
        _fw = 0.25 if chasing_trap and health >= 40 else 1.0
        # A SHORT snake (len < 7) that is not comfortably ahead MUST commit to
        # food or it STARVES (jump-flooding loss mode: wandered at len4 while food
        # was plentiful, hp dropped to 2). Give it a dominant, un-softened food
        # pull that beats the space-wandering terms.
        _short_hungry = my_len < 7 and _length_lead < 2
        # A GIANT snake massively ahead on a food-flooded board must STOP growing
        # (eremetic-eric loss mode: grows to len 55-95, self-coils; opp stays small
        # & outlasts us). When hugely ahead, only eat to avoid true starvation.
        # Only treat as a "giant that must stop growing" when the board is
        # actually FOOD-FLOODED (eremetic/gigantic opponents: 15-40 food on a
        # 121-cell board). On a NORMAL board (few food) a lead-3 snake fleeing
        # food gets driven into corners & self-coils (jackisherwood loss mode:
        # len 13-26 LONGER than opp, coiling on walls). So require a flooded board.
        _flooded = len(food_set) >= 10
        _giant = _length_lead >= 3 and my_len >= 10 and _flooded
        if food_set:
            if _giant:
                # Cap growth: eat ONLY when about to starve; otherwise flee food HARD
                # enough to overwhelm the space-maximization terms (space*2+timed*3)
                # so a hugely-ahead snake stops eating on a food-flooded board and
                # caps at a survivable size (eremetic-eric loss mode: grew to 40-95
                # & self-coiled while the opponent stayed small & outlasted us).
                if health < 15:
                    score -= fdist * 60.0
                elif health < 30:
                    score -= fdist * 6.0
                else:
                    score += fdist * 30.0
                    # DIRECT anti-eat: on a food-flooded board fdist is ~1 in
                    # every direction so the gradient above is near-useless; the
                    # snake eats incidentally & balloons to len 80+ then self-coils
                    # (gigantic-george/eremetic-eric loss mode). Heavily penalize
                    # the move that STEPS ONTO food, and steer toward food-SPARSE
                    # regions so the giant snake actively stops growing.
                    if c["reaches_food"] and health >= 25:
                        score -= 1500.0
                    # Food-density avoidance: fewer nearby food cells = safer for a
                    # giant that must stop growing. Count food within radius 2 of
                    # the destination and push away from dense clusters.
                    _cxg, _cyg = c["cell"]
                    _fd_near = sum(1 for fx, fy in food_set
                                   if abs(fx - _cxg) + abs(fy - _cyg) <= 2)
                    score -= _fd_near * 12.0
            elif health < 25:
                score -= fdist * 100.0
            elif health < 40:
                score -= fdist * 40.0
            elif _short_hungry:
                # dominant pull so we grow instead of circling in open space.
                # BUT if ALL food is wall/corner-trap and we're healthy (not truly
                # starving), soften it so a small snake doesn't crawl the wall into
                # a corner and self-coil (loss sim_215: len6 hp100 chased wall food
                # into corner (0,0) & died).
                if chasing_trap and health >= 60:
                    score -= fdist * 20.0 * 0.25
                else:
                    score -= fdist * 20.0
            elif health < 65:
                score -= fdist * 12.0 * _fw
            elif _length_lead < 0:
                # We are SHORTER than the enemy: strongly race for food to catch up.
                score -= fdist * 14.0 * _fw
            elif _length_lead < 1:
                # Roughly even length: still race hard so we don't get outgrown.
                score -= fdist * 10.0 * _fw
            elif want_food:
                # Not comfortably longer (lead < 3) or moderate health: pursue food.
                score -= fdist * 7.0
            elif my_len < 12:
                score -= fdist * 2.0

            # OWNED-FOOD SECURING: reward stepping ONTO food we own (reach first)
            # when not comfortably ahead -> lock in the growth & deny the opponent.
            # Penalize stepping onto enemy-owned food when we are healthy (the
            # enemy grabs it first / we walk into a contested loss). Both gated so
            # low-health starvation still eats anything.
            if not _giant and _length_lead < 3 and c["reaches_food"]:
                cellf = c["cell"]
                if cellf in owned_food and health >= 20:
                    score += 40.0
                elif cellf in contested_lose_food and health >= 50:
                    score -= 55.0

            # HUGE-LEAD FOOD AVOIDANCE: when we are ENORMOUSLY longer than the
            # opponent, growing further only risks self-coil (eremetic-eric loss
            # mode: our snake grew to len 55-91 on a 121-cell board flooded with
            # food, then coiled itself to death while the opponent stayed small &
            # waited). A giant snake must STOP eating and cap at a survivable
            # size. Push the head AWAY from food (positive weight) so it does not
            # keep eating. Fires only when massively ahead (lead >= 8) and not
            # starving; strength scales with how oversized we are.
            if (not _giant) and _length_lead >= 8 and health >= 40 and my_len >= 15:
                score += fdist * 3.0

        # Center pull: base weak pull, but stronger when we are short and
        # behind on length. Camping the perimeter keeps us safe but starves us
        # of the central food the enemy uses to outgrow us -> we lose H2H.
        cpull = 0.4
        if want_food and _length_lead < 2:
            cpull = 1.2
        score -= cdist * cpull
        if c["loses_h2h"]:
            # An EQUAL-length h2h is only a TIE. When short & hungry, penalize it
            # only mildly (a tie beats starvation); a LONGER enemy h2h stays a hard loss.
            if _shungry and c["h2h_len"] == my_len:
                score -= 20.0
            else:
                score -= 100.0

        if best is None or score > best_key:
            best = c
            best_key = score

    return best["name"] if best else pool2[0]["name"]


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
