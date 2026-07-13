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

# Per-game "stuck" tracker (module-level, persists across move() calls within
# the same long-lived server process -- see README_agent.md "Round (this
# session) -- opponent = coreyja__jump-flooding" for the full traced
# motivation). Keyed by game id; value = (last_turn, last_health, stuck_count).
# `stuck_count` counts consecutive turns where health did NOT increase (i.e.
# we did not eat) -- used to relax the flat head-to-head "risky_cells"
# avoidance penalty once we've gone a long time without eating while already
# low on health, so we don't starve to death in a stable mutual-avoidance
# stalemate with an opponent that happens to shadow our position (a real,
# confirmed match-losing mechanism: see the long trace in README_agent.md --
# our snake and a territory-maximizing opponent fell into a ~22-turn
# repeating mirrored cycle near a food-poor corner of the board, and our
# blanket -1000 "never risk a possible head-to-head" penalty made every
# route back toward food score worse than continuing the cycle, all the way
# down to starvation).
_stuck_state = {}


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


def _flood_fill_reach(start, blocked, width, height, cap, target=None):
    """Like _flood_fill_size, but also reports whether `target` cell is
    reachable within the explored region. Returns (count, reached_target).

    This directly targets the "self-coil" failure mode documented
    extensively in README_agent.md across many rounds: a candidate move
    can have a large *raw* flood-fill area (lots of nominally-reachable
    board cells) while still being a fatal self-trap, because that area
    calculation doesn't check whether it's actually connected back to
    where our own tail currently is. Since our own tail cell is normally
    *not* in `blocked` (it's assumed to vacate next turn, see
    _build_blocked), a path back to the tail is a cheap, well-known
    proxy for "this region isn't a disconnected pocket that will seal
    behind me as my body advances" -- if you can always reach your own
    tail, you can (approximately) always retrace your own body's path
    to escape, since the tail vacates as you move. It's not a perfect
    guarantee (the tail keeps moving too), but it is a much stronger
    signal than raw area alone against slow multi-turn self-coils, which
    is exactly the pattern traced in real match losses vs several past
    opponents (see README_agent.md "self-coil" sections)."""
    if start in blocked:
        return 0, False
    seen = {start}
    reached = (start == target)
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
            if nxt == target:
                reached = True
            q.append(nxt)
    return count, reached


def _greedy_self_room(start, blocked, width, height, steps_needed, tie_break="max_deg"):
    """Bounded, opponent-independent 'can my own body actually fit here'
    check. Starting at `start`, greedily walk up to `steps_needed` more
    cells, at each step picking an unvisited/unblocked neighbor according
    to `tie_break` (a cheap proxy for how our own body might continue --
    not a claim of optimal pathing). Cells visited by this virtual walk
    are treated as newly blocked (simulating our body extending along
    it), same as the real snake's future body would.

    `tie_break` options:
      - "max_deg": prefer the neighbor with the most free neighbors of
        its own (original, default rule -- "head toward the most-open
        local space").
      - "min_deg": prefer the neighbor with the FEWEST (but nonzero) free
        neighbors -- i.e. clear out tight/narrow branches first, saving
        open space for later. A different, complementary greedy
        assumption -- found (via a round's traced loss, see
        README_agent.md "coreyja__amphibious-arthur ... false-negative"
        section) to sometimes get stuck early in a region where
        "max_deg" incorrectly reports full room, since a single
        deterministic walk isn't guaranteed to find/avoid every real
        dead end even when using a plausible rule.
      - "far": prefer the neighbor that maximizes Manhattan distance from
        `start` -- a "keep spreading outward" rule, another independent
        proxy that can catch different dead-end shapes than the other two.

    Returns the number of steps successfully taken before getting stuck
    (no legal neighbor left at all), capped at `steps_needed`.

    Motivation (see README_agent.md, many rounds' "self-coil" write-ups):
    a candidate can have a large raw flood-fill area *and* pass the
    tail-reachability check while still leading into a region that is
    only wide enough for a fraction of our own body to actually fit
    without folding back on itself -- raw area only counts total open
    cells, not whether there's a real, walkable multi-step path through
    them for a body of our exact length. This is a cheap (<= my_length
    extra BFS-neighbor-degree checks, negligible cost on an 11x11 board)
    approximation of that, meant to complement (not replace) the
    existing hard-trap/tail-reachability checks -- used only as a soft,
    additive penalty below, never as a hard gate, to avoid repeating the
    already-documented mistake of an overly aggressive pessimistic-area
    heuristic overriding the real safety metrics (see the extensive
    "opp_territory"/"area_pess" history earlier in README_agent.md).

    See `_greedy_self_room_multi` below for the combined, more-robust
    multi-tie-break version actually used in the scoring loop."""
    if start in blocked:
        return 0
    visited = {start}
    cur = start
    steps = 0
    while steps < steps_needed:
        best_nb = None
        best_key = None
        for dx, dy in DIRS.values():
            nb = (cur[0] + dx, cur[1] + dy)
            if nb in visited or nb in blocked or not _in_bounds(nb, width, height):
                continue
            deg = 0
            for ddx, ddy in DIRS.values():
                nb2 = (nb[0] + ddx, nb[1] + ddy)
                if _in_bounds(nb2, width, height) and nb2 not in blocked and nb2 not in visited:
                    deg += 1
            if tie_break == "min_deg":
                key = -deg
            elif tie_break == "far":
                key = abs(nb[0] - start[0]) + abs(nb[1] - start[1])
            else:
                key = deg
            if best_key is None or key > best_key:
                best_key = key
                best_nb = nb
        if best_nb is None:
            break
        visited.add(best_nb)
        cur = best_nb
        steps += 1
    return steps


def _greedy_self_room_multi(start, blocked, width, height, steps_needed):
    """Run `_greedy_self_room` with a few different tie-break rules and
    return the MINIMUM steps achieved across them (i.e. the most
    pessimistic/conservative estimate, not the most optimistic).

    Rationale: a single deterministic greedy walk found a concrete false
    negative in local-benchmark testing against `coreyja__amphibious-arthur`
    (a candidate reported "full room" -- steps == my_length -- via the
    "max_deg" rule, that in the real game still led to a forced dead end
    just 1 turn later). Since the actual danger we're trying to detect is
    "this region doesn't really have room for my body", taking the MIN
    across several independent plausible-continuation rules is more
    conservative and more likely to catch a real dead end that any single
    rule's specific path happens to avoid seeing -- at the cost of
    possibly being slightly more pessimistic than necessary in some safe
    cases (acceptable: this only ever feeds a soft, additive, capped
    penalty below, never a hard gate, so it can't override the real
    safety metrics the way an overly aggressive pessimistic heuristic did
    in a previously-documented, since-fixed bug -- see the "opp_territory"
    history in README_agent.md). Cost: 3x a single walk, still just a
    handful of neighbor-degree checks capped at `steps_needed` -- cheap on
    an 11x11 board (see many earlier rounds' timing notes in
    README_agent.md for `_greedy_self_room` itself, this is a small
    constant-factor increase, not a different complexity class)."""
    best = None
    for tb in ("max_deg", "min_deg", "far"):
        s = _greedy_self_room(start, blocked, width, height, steps_needed, tb)
        if best is None or s < best:
            best = s
        if best == 0:
            break
    return best


def _voronoi_area(my_start, opp_starts, blocked, width, height):
    """Multi-source BFS 'race' partition: returns the number of cells
    strictly closer (by shortest-path BFS distance, avoiding `blocked`)
    to `my_start` than to any of `opp_starts` (each opponent's current
    head). Cells reached at the exact same distance by both sides are
    treated as contested (owned by neither) -- a conservative choice.

    This directly answers "how much board space can I actually claim
    before an opponent could contest it?", which a plain single-source
    flood fill cannot: a huge nominally-reachable region can still be a
    losing bet if an opponent is closer to the corridor/chokepoint that
    leads into most of it (found via a real traced match loss -- see
    README_agent.md for the concrete example this was built to fix).
    """
    if my_start in blocked:
        return 0
    dist = {my_start: 0}
    owner = {my_start: "me"}
    frontier = [my_start]
    for opp in opp_starts:
        if opp in blocked:
            continue
        if opp not in dist:
            dist[opp] = 0
            owner[opp] = "opp"
            frontier.append(opp)
        else:
            owner[opp] = None  # started on the same cell somehow -- contested
    d = 0
    while frontier:
        next_candidates = {}
        for cell in frontier:
            o = owner[cell]
            if o is None:
                continue
            for dx, dy in DIRS.values():
                nb = (cell[0] + dx, cell[1] + dy)
                if nb in dist or nb in blocked or not _in_bounds(nb, width, height):
                    continue
                next_candidates.setdefault(nb, set()).add(o)
        next_frontier = []
        for cell, owners in next_candidates.items():
            dist[cell] = d + 1
            owner[cell] = next(iter(owners)) if len(owners) == 1 else None
            next_frontier.append(cell)
        frontier = next_frontier
        d += 1
    return sum(1 for o in owner.values() if o == "me")


def _advance_body(body, move_to, food_set):
    """Simulate one snake advancing to `move_to` (a tuple). Returns the new
    body (list of tuples) reflecting standard Battlesnake growth rules: if
    `move_to` is a food cell, the snake grows (keeps its whole previous body
    plus the new head); otherwise the tail cell is dropped as usual."""
    ate = move_to in food_set
    if ate:
        return [move_to] + list(body)
    return [move_to] + list(body[:-1])


def _blocked_from_bodies(bodies, exclude_body=None):
    """Build a blocked-cell set from a list of bodies (each a list of (x,y)
    tuples), using the same tail-vacates-next-turn approximation as
    `_build_blocked` (a snake that just grew -- duplicate last two segments
    -- keeps its tail blocked). If `exclude_body` is one of the bodies in
    the list (by identity), that body's OWN HEAD (index 0) is skipped when
    blocking -- used so a flood fill can validly start at a snake's own new
    head cell without it appearing blocked."""
    blocked = set()
    for body in bodies:
        if not body:
            continue
        n = len(body)
        just_ate = n >= 2 and body[-1] == body[-2]
        for i, seg in enumerate(body):
            if body is exclude_body and i == 0:
                continue
            if i == n - 1 and not just_ate:
                continue
            blocked.add(seg)
    return blocked


def _opponent_worst_case_area(nxt, my_new_body, opp, blocked_now, other_bodies,
                               width, height, food_set, cap):
    """Real (not speculative-territory) 1-ply adversarial lookahead: assume
    the single `opp` snake gets to pick its own next move AFTER seeing that
    we've committed to `nxt`, choosing whichever of its own legal moves
    minimizes OUR resulting flood-fill area the most (a paranoid/minimax
    worst-case assumption -- cheap since there's normally exactly one
    opponent in this game format).

    This directly targets the many-rounds-documented "genuine 1-ply tie"
    failure class (see README_agent.md -- dozens of traced examples across
    many opponents, most recently and persistently OliverMKing__astar-snake,
    where two candidate moves have IDENTICAL raw flood-fill area/Voronoi
    territory at the moment of decision, and only diverge in safety once an
    opponent's very next real move seals a chokepoint). Unlike the old,
    already-removed `opp_territory`/`area_pess` mechanism (which pessimistically
    blocked every cell an opponent could reach within a fixed multi-move
    horizon -- found to be uninformative/actively harmful on a small board,
    see README_agent.md history), this simulates the opponent's actual
    *single* next legal move, not a many-move reachable-set, so it cannot
    inflate an entire large open region into looking dangerous merely
    because an opponent could eventually wander into part of it.

    Returns the minimum resulting area across the opponent's legal moves
    (or None if the opponent has no legal moves / doesn't exist, i.e. no
    extra info available)."""
    opp_body = [(seg["x"], seg["y"]) for seg in opp["body"]]
    opp_head = opp_body[0]
    worst = None
    for dx, dy in DIRS.values():
        opp_nxt = (opp_head[0] + dx, opp_head[1] + dy)
        if not _in_bounds(opp_nxt, width, height):
            continue
        if opp_nxt in blocked_now:
            continue
        opp_new_body = _advance_body(opp_body, opp_nxt, food_set)
        leaf_bodies = [my_new_body, opp_new_body] + other_bodies
        leaf_blocked = _blocked_from_bodies(leaf_bodies, exclude_body=my_new_body)

        # Genuine 2-ply extension (this round): rather than leaf-evaluating
        # immediately after the opponent's (worst-case-for-us) move, let
        # OURSELVES respond with our own best next move from `nxt` first,
        # and use THAT resulting area as the leaf value. This is a real,
        # bounded minimax step deeper than the previous 1-ply version (our
        # move -> opponent's worst move -> OUR best response -> assess),
        # directly targeting the many-rounds-documented "genuine tie that
        # only resolves 2+ plies out" failure class (see README_agent.md,
        # many traced examples e.g. against rdbrck__btas/ccSnake2018/
        # OliverMKing__astar-snake, where even a 1-ply-adversarial check
        # sometimes isn't deep enough because the two candidates were tied
        # for multiple consecutive turns, not just one). Cost is bounded:
        # at most 4 extra flood-fills per opponent-move branch (16 total
        # per candidate, 64 per move() call) -- still cheap on an 11x11
        # board per this file's many earlier timing notes elsewhere.
        best_our_followup = 0
        for fdx, fdy in DIRS.values():
            my_nxt2 = (nxt[0] + fdx, nxt[1] + fdy)
            if not _in_bounds(my_nxt2, width, height):
                continue
            if my_nxt2 in leaf_blocked:
                continue
            area2 = _flood_fill_size(my_nxt2, leaf_blocked, width, height, cap)
            if area2 > best_our_followup:
                best_our_followup = area2
        area = best_our_followup
        if worst is None or area < worst:
            worst = area
    return worst


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

        # Own tail cell + whether we just ate (duplicate tail segment) --
        # used below for the tail-reachability anti-self-coil check. If we
        # just ate, the tail cell doesn't vacate this coming turn (it's
        # already excluded from `blocked` correctly by _build_blocked in
        # that case, i.e. it stays blocked), so a "reach my own tail" check
        # would be meaningless/misleading right after eating -- skip it
        # that turn (my_tail = None disables the check below).
        _n_body = len(my_body)
        _just_ate = _n_body >= 2 and my_body[-1]["x"] == my_body[-2]["x"] and my_body[-1]["y"] == my_body[-2]["y"]
        my_tail = None if _just_ate else (my_body[-1]["x"], my_body[-1]["y"])

        snakes = board["snakes"]

        # Length-deficit awareness: if the biggest opponent is
        # significantly longer than us, that power gap is a leading
        # indicator of exactly the "forced head-to-head loss" pattern
        # traced repeatedly across many rounds' loss analyses in
        # README_agent.md (most recently vs tim-hub__awesome-snake,
        # sim_0.jsonl turn 108: our snake, stuck at length 5-6, got
        # legitimately boxed into a corner where BOTH remaining legal
        # moves were risky_cells against an opponent that had grown to
        # length 11 mostly unopposed). We can't retroactively fix a
        # specific forced 50/50 collision, but we CAN reduce how often we
        # end up far behind in length in the first place by mildly
        # increasing our own food urgency when a real length gap exists,
        # even while health is otherwise fine -- catching up in length
        # shrinks the opponent's structural advantage in any future
        # head-to-head and gives us more mass to contest territory with.
        # Small and capped so it can't override genuine safety terms.
        _opp_lengths = [s["length"] for s in snakes if s["id"] != my_id]
        _max_opp_length = max(_opp_lengths) if _opp_lengths else 0
        length_deficit = max(0, _max_opp_length - my_length)

        food = board.get("food", [])
        food_set = {(f["x"], f["y"]) for f in food}
        hazards = board.get("hazards", [])
        hazard_set = {(h["x"], h["y"]) for h in hazards}

        blocked = _build_blocked(snakes)

        # Update the stuck-tracker for this game (see module-level comment
        # above _stuck_state for the full rationale). We consider ourselves
        # "stuck" (not making food progress) for a turn if health did not
        # increase relative to the immediately preceding turn we recorded
        # (a simple, cheap proxy for "we did not eat this turn" that works
        # even across the rare double-decrement-from-hazard cases, since we
        # only care about "not increasing", not the exact decrement size).
        gid = game_state.get("game", {}).get("id", "default")
        turn_num = game_state.get("turn", 0)
        prev = _stuck_state.get(gid)
        if prev is None or turn_num <= prev[0]:
            stuck_count = 0
        else:
            last_turn, last_health, sc = prev
            if turn_num == last_turn + 1 and my_health <= last_health:
                stuck_count = sc + 1
            else:
                stuck_count = 0
        _stuck_state[gid] = (turn_num, my_health, stuck_count)

        # Cells an equal-or-longer opponent could move into this turn.
        # Cells only a strictly-shorter opponent could reach (a winnable
        # head-to-head for us) are tracked separately for a small
        # aggression bonus.
        risky_cells = set()
        winnable_cells = set()
        opp_heads = []
        for s in snakes:
            if s["id"] == my_id:
                continue
            ohx, ohy = s["head"]["x"], s["head"]["y"]
            opp_heads.append((ohx, ohy))
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

        # For space/area evaluation only (not for the legal-move filter), also
        # treat any cell an opponent could move into *next* turn (regardless of
        # relative length) as blocked. This is a cheap 1-extra-ply pessimistic
        # widening of the flood-fill that catches opponents actively cutting off
        # a corridor a turn before it would otherwise become visible (a real
        # failure mode found via local-benchmark loss analysis: a big open area
        # computed from a candidate cell can collapse to almost nothing the very
        # next turn once an opponent's head advances into a chokepoint). We
        # exclude the candidate cell itself from this extra blocking (that
        # specific head-to-head risk is already handled separately via
        # risky_cells / winnable_cells below).
        opp_next_cells = risky_cells | winnable_cells

        # Setup for a real (not speculative-territory) 1-ply adversarial
        # opponent-response lookahead -- see _opponent_worst_case_area's
        # docstring above for the full rationale. Only meaningful/cheap to
        # do exactly in the standard 1v1 format (2 snakes total); with more
        # opponents we'd need to pick which one to model adversarially, so
        # we conservatively skip this extra term rather than guess (falls
        # back to the existing, already-validated single-ply heuristics --
        # zero behavior change in that rarer case).
        my_body_t = [(seg["x"], seg["y"]) for seg in my_body]
        _other_snakes = [s for s in snakes if s["id"] != my_id]
        single_opp = _other_snakes[0] if len(_other_snakes) == 1 else None

        best_name = None
        best_score = float("-inf")
        for name, nxt in candidates:
            score = 0.0

            # Primary space metric: RAW flood-fill area, blocked only by
            # actual current snake bodies (never by speculative opponent-
            # territory guesses). This must drive the hard-trap / soft-
            # margin thresholds below, because it reflects real, currently
            # true reachability.
            #
            # IMPORTANT (bug found + fixed this round, see README_agent.md
            # for the full traced example): an earlier version used
            # min(area, area_pess) -- a heavily opponent-pessimistic
            # estimate (blocking every cell an opponent could reach within
            # several moves) -- as the value driving the *hard* trap
            # penalty. Traced two real match losses directly to this: a
            # wide-open, genuinely safe 90+-cell region got its pessimistic
            # estimate collapsed to ~1 cell (because the opponent could
            # *eventually* reach deep into that region within a many-move
            # horizon, even though it posed no real, current threat), which
            # made the hard-trap penalty score it *worse* than an actual
            # small dead-end pocket the bot then walked into and died in.
            # See sim_246.jsonl turn 124 and sim_248.jsonl turn 269 in
            # /logs/rounds/0 for the exact reproduced traces.
            # Correctness fix (found this round via trace-replay against a
            # real match loss, zacpez__scape-goat sim_80.jsonl turn 72 in
            # /logs/rounds/0): if this candidate cell itself is food, we
            # will EAT this turn, which means our own tail segment does
            # NOT vacate this turn (growth keeps it occupied one extra
            # turn) -- unlike the general `blocked` set built by
            # _build_blocked, which assumes (correctly, for the *other*
            # snakes, and for us on a non-eating move) that every tail
            # vacates. Without this fix, a food cell that seals off our
            # own tail-reachability looked identical (area/tail_reachable
            # both fine) to a genuinely safe food pickup, because the
            # flood fill treated our own tail cell as free space it could
            # walk back through even though eating there means that cell
            # stays occupied by our own body next turn. Confirmed via
            # direct replay: at the traced turn, this fix flips
            # tail_reachable from True to (correctly) False for the
            # fatal "grab the corner food" candidate, while leaving the
            # safer alternatives (which don't eat) unaffected.
            # BUG FIX (found this round via trace-replay against a real
            # match starvation loss, tim-hub__awesome-snake sim_100.jsonl
            # turns 98-118 in /logs/rounds/1 -- our snake cycled in a small
            # 10-turn loop, walking directly ADJACENT to food repeatedly
            # (food-dist 0/1 every turn) but never actually eating it,
            # starving to death from health 20 down to 0 while food sat
            # right next to it the whole time). Root cause: the previous
            # eat_blocked fix (correctly) adds our own tail cell to the
            # blocked set when this candidate eats food, to reflect that
            # eating keeps that tail segment occupied one extra turn. But
            # the tail-reachability check was then still called with
            # target=my_tail -- i.e. it asked "can I reach `my_tail`"
            # using a blocked-set that already contains `my_tail` itself,
            # which _flood_fill_reach can NEVER answer "yes" to (a
            # blocked cell is never added to `seen`/marked reached,
            # regardless of area). This made EVERY food-eating candidate
            # unconditionally register tail_reachable=False and eat the
            # -my_length*8 anti-self-coil penalty, even for a completely
            # safe, wide-open food pickup -- confirmed directly: replaying
            # the exact turn-99 board state from sim_100.jsonl showed the
            # candidate that eats immediately-adjacent food scored ~10-12
            # points LOWER than non-eating alternatives purely from this
            # spurious penalty, despite otherwise-identical area/voronoi/
            # edge/degree terms, causing the bot to systematically avoid
            # eating nearby food turn after turn. Fix: when a candidate
            # eats, skip the (now-meaningless) tail-reachability penalty
            # entirely for that candidate -- the area computation still
            # correctly uses eat_blocked (that part was fine), only the
            # reachability *check/penalty* is skipped.
            eating = nxt in food_set
            eat_blocked = blocked
            if my_tail is not None and eating:
                eat_blocked = blocked | {my_tail}
            area, tail_reachable = _flood_fill_reach(
                nxt, eat_blocked, width, height, cap,
                target=(None if eating else my_tail),
            )
            area_for_score = area

            # Anti-self-coil: if our own tail is NOT reachable from this
            # candidate (and we have a tail to check, i.e. we didn't just
            # eat), that's a strong warning sign that this region may seal
            # off from the rest of the board as our own body advances --
            # exactly the mechanism traced in a real match loss this round
            # (sim_106.jsonl vs coreyja__bombastic-bob: our snake spiraled
            # along the top edge into the top-right corner over ~10 turns,
            # each individual move having a large *raw* flood-fill area
            # right up until the final couple of turns, by which point it
            # was already a forced dead end -- see README_agent.md for the
            # full turn-by-turn trace). This is a well-known heuristic used
            # by many strong Battlesnake bots ("can I still reach my own
            # tail") as a cheap, much-earlier-firing proxy for "is this
            # move part of a slow self-coil", well before raw area alone
            # would show any danger. Penalty scales with our length (a
            # short snake's tail is close and this rarely matters; a long
            # snake failing this check is a much bigger red flag).
            if my_tail is not None and not eating and not tail_reachable:
                score -= my_length * 8

            # Voronoi "race" territory: cells strictly closer (BFS distance,
            # avoiding current bodies) to this candidate than to any
            # opponent's current head. This is a principled fix for the
            # "corridor race" failure mode that the old opp_territory/
            # area_pess mechanism tried (and largely failed) to catch: that
            # mechanism blocked every cell any opponent could reach within a
            # fixed move horizon, which on a small board makes almost the
            # *entire* open region look equally "pessimistic" (uninformative
            # -- verified directly: it collapsed to the same value for every
            # candidate in a real traced loss, see README_agent.md), so it
            # never actually influenced the decision in the case that
            # mattered. Voronoi partition instead asks "who gets to each
            # cell first?", which correctly shrinks our claimed area when a
            # candidate walks toward a chokepoint the opponent is closer to
            # (confirmed via direct trace replay against a real match loss:
            # see README_agent.md for the exact turn-by-turn numbers -- the
            # move the bot actually took had voronoi territory collapsing
            # turn over turn while the safer alternative kept 2-3x more).
            voronoi_mine = _voronoi_area(nxt, opp_heads, blocked, width, height)
            score += voronoi_mine * 6

            # Real 1-ply adversarial opponent-response lookahead (only in
            # the standard 1v1 case -- see setup comment above and
            # _opponent_worst_case_area's docstring for full rationale).
            # This is the many-rounds-recurring "real multi-ply lookahead"
            # idea, finally attempted here in a narrowly-scoped, low-risk
            # form: rather than trying to model the opponent's full
            # heuristic, just assume they play adversarially against OUR
            # space (a standard, safe paranoid/minimax assumption), one
            # real move deep. This directly targets the single most
            # persistent traced failure across this file's history: two
            # candidates that are EXACTLY tied on every current-turn metric
            # (raw area, Voronoi territory) but diverge as soon as the
            # opponent's very next move is accounted for (e.g. one path's
            # only chokepoint back to open space is one cell the opponent
            # can reach next turn; the other's isn't). Purely additive --
            # cannot override the hard-trap/soft-margin gates above, which
            # are still driven by the *raw*, non-speculative area, so this
            # cannot repeat the previously-documented "pessimistic area
            # override" bug class (see the extensive opp_territory/area_pess
            # history elsewhere in this file).
            if single_opp is not None:
                my_new_body = _advance_body(my_body_t, nxt, food_set)
                opp_worst_area = _opponent_worst_case_area(
                    nxt, my_new_body, single_opp, blocked, [],
                    width, height, food_set, cap,
                )
                if opp_worst_area is not None:
                    score += min(opp_worst_area, area_for_score) * 4
                    # Give this real teeth for the specific "genuine 1-ply
                    # tie" failure class this whole mechanism targets: if
                    # the opponent's single best (for them) response would
                    # leave us with LESS reachable area than our own body
                    # length -- i.e. a predicted future trap, not just a
                    # smaller-but-still-safe region -- add a meaningful
                    # extra penalty. Weighted below the same-turn guaranteed
                    # hard-trap penalty (100x, used when area_for_score
                    # itself is already < my_length, a certainty) since this
                    # is a 1-ply *prediction* of the opponent's move (they
                    # might not actually play their worst-case-for-us move),
                    # but still large enough to decisively break ties among
                    # candidates that look identical on every current-turn
                    # metric (raw area, Voronoi territory) -- exactly the
                    # repeated failure pattern documented at length in
                    # README_agent.md across many opponents, most
                    # persistently OliverMKing__astar-snake. The previous
                    # `* 4` linear term alone was too weak to reliably flip
                    # such ties (e.g. area 100 vs 100, opp_worst 100 vs 5
                    # only nets a 380-point gap once combined with the
                    # existing area*5 term -- helpful, but this adds a
                    # sharper, more targeted signal specifically for the
                    # "collapses below body length" case).
                    if opp_worst_area < my_length:
                        score -= (my_length - opp_worst_area) * 30
            # Heavily penalize getting trapped in a space smaller than our body
            # (would starve/box us in for certain).
            if area_for_score < my_length:
                score -= (my_length - area_for_score) * 100
            # Softer penalty gradient below a 2.2x buffer -- avoids shaving
            # margin so tight that a self-coil a few moves later (which
            # 1-ply flood fill can't see coming) becomes fatal. Widened
            # from 1.5x -> 2.2x after a local-benchmark loss where the bot
            # hugged its own body along the board perimeter for ~15 turns
            # (area shrinking turn over turn but staying just above the
            # 1.5x threshold until an opponent sealed the only remaining
            # exit) -- see README_agent.md "self-coil" notes for the full
            # trace. A wider margin makes the bot react earlier/more
            # conservatively while area is still comfortably large.
            elif area_for_score < my_length * 2.2:
                score -= (my_length * 2.2 - area_for_score) * 12
            score += area_for_score * 5

            # Bounded, opponent-independent "does my body actually fit"
            # check (see _greedy_self_room docstring above for full
            # rationale). Only bother running it when the region already
            # looks nominally safe (area_for_score >= my_length) -- if it's
            # already smaller than our body, the hard-trap penalty above
            # already fires much harder, so this would be redundant. Soft,
            # additive-only penalty (never a hard gate) so it can't repeat
            # the previously-documented "pessimistic area override" bug.
            if area_for_score >= my_length:
                room_steps = _greedy_self_room_multi(nxt, blocked, width, height, my_length)
                if room_steps < my_length:
                    score -= (my_length - room_steps) * 7

            if nxt in risky_cells:
                # Relax the flat -1000 "never risk a possible head-to-head"
                # penalty once we're low on health AND have gone a long
                # stretch without eating (see the stuck-tracker comment
                # above _stuck_state, and README_agent.md for the full
                # traced starvation-via-mutual-avoidance-cycle example
                # against coreyja__jump-flooding). Only kicks in when
                # health < 50 (matching the existing food-urgency gating
                # elsewhere in this loop) -- at healthy health levels the
                # full -1000 is unchanged, so this cannot make the bot more
                # reckless in the common case, only when actually starving
                # and stuck.
                if my_health < 50:
                    risky_penalty = max(40, 1000 - stuck_count * 25)
                else:
                    risky_penalty = 1000
                score -= risky_penalty

            dist = _bfs_nearest_food_dist(nxt, blocked, width, height, food_set)
            if dist is not None:
                # Steeper urgency curve as health drops -- fixes the same
                # traced starvation loop as the free_degree deficit fix
                # above (see the long comment there): at critically low
                # health, food-seeking must dominate other heuristic terms
                # (edge/degree/voronoi tie-breaks) much more strongly than
                # the old flat "4 if <50 else 1.5" weight did, or the bot
                # can get stuck cycling near food it never commits to
                # eating. Confirmed via direct trace-replay: with the old
                # weight=4, the bot cycled in a 6-cell loop near a food
                # item at health 8 down to health 1 and starved; replaying
                # the exact same board states with this steeper curve
                # picks the food-adjacent move instead.
                if my_health < 15:
                    weight = 10
                elif my_health < 30:
                    weight = 6
                elif my_health < 50:
                    weight = 4
                else:
                    weight = 1.5
                # Small, capped boost when we're behind in length (see
                # length_deficit comment above) -- at most +1.5 extra
                # weight (deficit>=5), so it can nudge food-seeking a bit
                # harder without ever overriding the health-based curve
                # or safety terms.
                weight += min(length_deficit * 0.3, 1.5)
                # Additional capped boost when we've gone a long stretch
                # without making any health progress (stuck_count, computed
                # above), REGARDLESS of current health level -- targets a
                # distinct traced failure mode from the low-health
                # starvation loop above: a healthy snake that wanders far
                # from any food for 20+ turns (every individual step looked
                # locally fine/safe at the time) and, purely by chance,
                # ends up colliding with an opponent's independent path or
                # self-coiling into a pocket several turns later, with no
                # food ever having been a strong enough draw to redirect it
                # sooner (see README_agent.md, "Spenca__vulture-snake"
                # sections, for several traced real-match losses matching
                # this exact shape -- health declining steadily for 20+
                # turns with no eating, well before health<50 kicks in the
                # existing urgency curve above). Capped at +3.0 (reached at
                # stuck_count>=20) so it can only ever nudge tie-breaks
                # among already-safe candidates, never override the
                # hard-trap/risky_cells/voronoi safety terms elsewhere in
                # this loop.
                weight += min(stuck_count * 0.15, 3.0)
                score -= dist * weight
                if dist == 0:
                    score += 20  # immediate food bonus

            # Local mobility bonus: how many immediately-free neighbor cells
            # does the candidate cell itself have (degree in the free-space
            # graph, ignoring the direction we came from)? A cell with only
            # 1 free neighbor is either a genuine dead end or the mouth of a
            # narrow corridor -- even if the *flood-fill area* beyond it
            # looks huge (which it will, right up until our own body seals
            # the corridor behind us as we walk down it -- a concrete,
            # confirmed loss mechanism: local benchmark vs m-schier/kreuzotter
            # this round, our snake tied on raw flood-fill area between two
            # candidates (both ~106 cells) but one had degree 1 (walled-in
            # peninsula) and the other had degree 3 (real open space); the
            # food-seeking bonus alone tipped the tie toward the degree-1
            # option, which is exactly the fatal one -- see README_agent.md
            # for the full traced example). This is a cheap, local, purely
            # additive nudge meant to win exactly this kind of tie-break
            # *before* committing to a move that only looks safe because the
            # flood-fill snapshot doesn't yet reflect our own future body.
            # Deficit-based (relative to the max POSSIBLE neighbors for this
            # board position, not an absolute count) -- fixes a real,
            # confirmed bug found this round via trace-replay against
            # coreyja__coreyja-rs (a local benchmark loss, sim/game
            # /tmp/game_3.json turns 90-99): the old code rewarded raw
            # free_degree, which is *intrinsically* lower for edge/corner
            # cells (an edge cell has at most 3 in-bounds neighbors, a
            # corner at most 2) purely due to board geometry, regardless of
            # any actual danger. Combined with the edge-penalty term below,
            # this made the bot systematically avoid food sitting near an
            # edge/corner even while critically low on health, and it got
            # caught in a stable back-and-forth cycle a few cells away from
            # a food item at (6,0) for 8+ turns until it starved to death
            # (confirmed via direct main.move() replay on the literal
            # logged board state -- see README_agent.md for the full
            # trace). Using the deficit (max_possible - actual) instead
            # gives identical scoring to before for interior-cell ties
            # (where max_possible is 4 for both candidates, so the relative
            # difference is unchanged) but removes the spurious edge/corner
            # bias, since a corner cell with both its 2 possible neighbors
            # free now scores the same (deficit 0) as an open interior cell
            # with all 4 free.
            max_free_degree = 0
            free_degree = 0
            for ddx, ddy in DIRS.values():
                nb = (nxt[0] + ddx, nxt[1] + ddy)
                if _in_bounds(nb, width, height):
                    max_free_degree += 1
                    if nb not in blocked:
                        free_degree += 1
            score -= (max_free_degree - free_degree) * 22

            # Preference to stay away from edges/corners (more escape routes).
            # Strengthened + length-scaled after a traced real-match loss
            # (local benchmark vs Xe__since this round): our snake walked
            # up the left board edge (x=0/1) for ~15 consecutive turns,
            # coiling itself into the top-left corner with no opponent
            # forcing it -- a pure self-inflicted wall-hugging trap that
            # the old flat +0.5/cell edge bonus was far too weak to
            # discourage (voronoi/area/food scoring along that corridor
            # kept looking fine turn over turn until it was already fatal).
            # Scale by length: hugging edges is fine/harmless for a short
            # snake grabbing nearby food, but increasingly dangerous once
            # long, since a self-coil against a wall has nowhere to
            # unwind. See README_agent.md for the traced example + the
            # earlier ladder-history precedent (a parallel session facing
            # this same opponent found and fixed the identical pattern).
            x, y = nxt
            edge_dist = min(x, width - 1 - x, y, height - 1 - y)
            on_v_edge = x == 0 or x == width - 1
            on_h_edge = y == 0 or y == height - 1
            len_scale = 1.0 + max(0, my_length - 4) * 0.15
            score += edge_dist * 2.2
            if on_v_edge or on_h_edge:
                score -= 9.0 * len_scale
                if on_v_edge and on_h_edge:
                    score -= 35.0 * len_scale  # actual corner cell

            # Self-corridor ("edge run") penalty: continuing to travel along
            # the same board edge for many consecutive turns is a
            # recurring, confirmed failure mode (see README_agent.md --
            # traced losses vs ccSnake2018__ccsnake this round: our snake
            # followed the top edge / bottom edge toward a food item
            # sitting in the far corner for 5-10 consecutive turns while a
            # comparable-or-longer opponent converged along a parallel
            # interior lane, sealing the only escape route and leaving
            # zero legal moves once we reached the corner). The existing
            # flat per-cell edge/corner penalty doesn't grow with
            # commitment, so a persistent food-distance benefit can offset
            # it turn after turn even as the trap deepens. Count how many
            # of our own current body segments (starting at the head)
            # already lie on the same edge as the candidate cell, and
            # penalize super-linearly (worse when a same-or-longer
            # opponent is nearby, since that's when a corridor race is
            # actually live) -- a short one-or-two-cell touch of an edge
            # stays cheap, but continuing to hug it for many turns becomes
            # increasingly expensive, biasing the bot to break back toward
            # open interior space earlier, while there is still room to.
            # NOTE (this round's fix): the old version only counted a "run"
            # when consecutive segments shared the EXACT same x (vertical
            # edge) or EXACT same y (horizontal edge), and only considered
            # a cell "on an edge" at all when x/y == 0 or width/height-1
            # exactly. This missed two real, confirmed cases traced in a
            # local-benchmark loss vs coreyja__coreyja-rs this round
            # (/tmp/game_1.json, died turn 113): (a) our snake hugged the
            # column ONE cell in from the true edge (x=1 on an 11-wide
            # board) for ~10 consecutive turns -- `on_v_edge` was False
            # the entire time (x=1 != 0), so NO penalty accrued at all;
            # (b) when the path then turned a corner (from the x=1 column
            # onto the true top edge y=10), the run counter reset to 1
            # because the segments no longer shared the same exact x OR y
            # -- so a single continuous ~15-turn wall-hugging trap was
            # scored as if it were two separate 1-cell touches. Both
            # combined meant the self-corridor penalty essentially never
            # fired during the entire fatal approach. Fixed by tracking a
            # general "near-wall run": how many consecutive own body
            # segments (from the head) have edge_dist <= 1 (true edge OR
            # one cell in), regardless of whether they're on the same
            # exact edge -- this correctly keeps accumulating across a
            # corner turn and starts counting one cell earlier (at
            # distance 1, not just distance 0).
            near_wall = edge_dist <= 1
            wall_run = 0
            if near_wall:
                wall_run = 1
                for seg in my_body:
                    seg_edge_dist = min(
                        seg["x"], width - 1 - seg["x"],
                        seg["y"], height - 1 - seg["y"],
                    )
                    if seg_edge_dist <= 1:
                        wall_run += 1
                    else:
                        break
            if wall_run > 0:
                nearest_opp_dist = min(
                    (abs(x - ox) + abs(y - oy) for ox, oy in opp_heads),
                    default=99,
                )
                proximity_mult = 2.0 if nearest_opp_dist <= 10 else 1.0
                score -= wall_run * wall_run * 2.5 * len_scale * proximity_mult

            # Avoid hazard cells (extra health drain per turn in maps/rulesets
            # that have them, e.g. Royale). No-op on rulesets with no hazards
            # (hazard_set is empty then), so this is a free/safe addition.
            if nxt in hazard_set:
                score -= 40

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
