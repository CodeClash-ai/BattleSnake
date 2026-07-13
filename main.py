"""A conservative Battlesnake for CodeClash.

The round-0 bot was an exact clone of the opponent's very simple strategy
(blindly move toward the farthest food).  This version focuses on one thing
that clone does not do: stay alive.  Against the Kotlin SimpleSnake opponent,
most games end in the first few turns because it drives into walls/bodies; if
we avoid immediate deaths and obvious head-to-heads we should win far more than
chance.
"""

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "gpt-5-5",
        "color": "#2ecc71",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    # Reset stateful local opponent predictors between games.
    try:
        from tools import vulture_snake_opponent
        vulture_snake_opponent.start(game_state)
    except Exception:
        pass
    return None


def end(game_state):
    return None


def _pt(p):
    return (p["x"], p["y"])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _in_bounds(p, w, h):
    return 0 <= p[0] < w and 0 <= p[1] < h


def _neighbors(p):
    for d in MOVES.values():
        yield _add(p, d)


def _occupied_cells(snakes, food_cells=frozenset()):
    """Cells that are unsafe to move into this turn.

    BattleSnake removes tails before resolving body collisions, so a tail square
    is normally safe.  If that snake's head is already on food its tail will be
    duplicated this turn, so keep that tail blocked.  This approximation handles
    the common case and is intentionally a little optimistic around enemy tails
    to avoid needless wall moves.
    """
    occ = set()
    for sn in snakes:
        body = [_pt(p) for p in sn.get("body", [])]
        if not body:
            continue
        tail_moves = body[-1] not in food_cells
        blocked = body[:-1] if tail_moves else body
        occ.update(blocked)
    return occ


def _flood_count(start, w, h, blocked, limit=200):
    """How much open space is reachable from start (capped for speed)."""
    if not _in_bounds(start, w, h):
        return 0
    if start in blocked:
        blocked = set(blocked)
        blocked.discard(start)
    seen = {start}
    q = [start]
    qi = 0
    while qi < len(q) and len(seen) < limit:
        p = q[qi]
        qi += 1
        for n in _neighbors(p):
            if _in_bounds(n, w, h) and n not in blocked and n not in seen:
                seen.add(n)
                q.append(n)
    return len(seen)



def _distance_map(starts, w, h, blocked, limit=200):
    """Breadth-first distances from one or more starts through unblocked cells."""
    b = set(blocked)
    dist = {}
    q = []
    for st in starts:
        if st is not None and _in_bounds(st, w, h) and st not in dist:
            b.discard(st)
            dist[st] = 0
            q.append(st)
    qi = 0
    while qi < len(q) and len(dist) < limit:
        p = q[qi]
        qi += 1
        nd = dist[p] + 1
        for n in _neighbors(p):
            if _in_bounds(n, w, h) and n not in b and n not in dist:
                dist[n] = nd
                q.append(n)
    return dist


def _territory_count(my_start, enemy_heads, w, h, blocked, my_len, enemy_max_len):
    """Approximate Voronoi cells we can reach before the enemy.

    This helps in rare long games against real pathing bots: pure flood-fill can
    overvalue large regions that a nearby equal/larger opponent actually controls.
    Equal-time cells are only credited when we are longer and can win the
    head-to-head.
    """
    myd = _distance_map([my_start], w, h, blocked, limit=w * h)
    if not enemy_heads:
        return len(myd)
    ed = _distance_map(enemy_heads, w, h, blocked, limit=w * h)
    terr = 0
    for cell, d in myd.items():
        e = ed.get(cell)
        if e is None or d < e or (d == e and my_len > enemy_max_len):
            terr += 1
    return terr


def _articulation_risk(pos, w, h, blocked):
    """Penalty for stepping into a narrow connector with few exits.

    Flood fill alone can prefer walking along walls through a one-cell-wide
    corridor that a nearby opponent can later cut.  Penalize low-degree cells
    when there is a roomier alternative.
    """
    exits = 0
    second = 0
    for n in _neighbors(pos):
        if _in_bounds(n, w, h) and n not in blocked:
            exits += 1
            for nn in _neighbors(n):
                if nn != pos and _in_bounds(nn, w, h) and nn not in blocked:
                    second += 1
    if exits <= 1:
        return 3
    if exits == 2 and second <= 2:
        return 1
    return 0

def _nearest_food_distance(pos, food):
    if not food:
        return 99
    return min(_manhattan(pos, f) for f in food)



def _nearest_uncontested_food_distance(pos, food, enemy_heads, my_len, enemy_max_len):
    """Nearest food we can plausibly claim before an equal/longer enemy.

    Against competent area bots, heavily chasing food that the opponent reaches
    first causes us to walk into their body wall.  Manhattan timing is crude but
    catches the common case where a longer enemy is adjacent to the same food.
    """
    if not food:
        return 99
    best = 99
    for f in food:
        md = _manhattan(pos, f)
        if not enemy_heads:
            best = min(best, md)
            continue
        ed = min(_manhattan(eh, f) for eh in enemy_heads)
        # Equal-time food is unsafe when we cannot win the resulting head race.
        if md < ed or (md == ed and my_len > enemy_max_len):
            best = min(best, md)
    return best


def _food_contested_from(pos, food_cells, enemy_heads, my_len, enemy_max_len):
    if pos not in food_cells or not enemy_heads:
        return False
    ed = min(_manhattan(eh, pos) for eh in enemy_heads)
    return ed <= 1 and enemy_max_len >= my_len


def _shortest_food_distance(pos, food_cells, w, h, blocked):
    """True BFS distance to food through currently open cells (99 if unreachable)."""
    if not food_cells:
        return 99
    b = set(blocked)
    b.discard(pos)
    seen = {pos}
    q = [(pos, 0)]
    qi = 0
    while qi < len(q):
        cur, d = q[qi]
        qi += 1
        if cur in food_cells:
            return d
        nd = d + 1
        for n in _neighbors(cur):
            if _in_bounds(n, w, h) and n not in b and n not in seen:
                seen.add(n)
                q.append((n, nd))
    return 99


def _enemy_reachable_count(start, enemy_heads, w, h, blocked, limit=200):
    """Reachable cells for larger enemies, allowing them to start at their heads."""
    if not enemy_heads:
        return 0
    b = set(blocked)
    for eh in enemy_heads:
        b.discard(eh)
    seen = set()
    q = []
    for eh in enemy_heads:
        if _in_bounds(eh, w, h) and eh not in seen:
            seen.add(eh)
            q.append(eh)
    qi = 0
    while qi < len(q) and len(seen) < limit:
        p = q[qi]
        qi += 1
        for n in _neighbors(p):
            if _in_bounds(n, w, h) and n not in b and n not in seen:
                seen.add(n)
                q.append(n)
    return len(seen)


def _simple_opponent_target_move(head, food, w, h):
    """Predict the known opponent: farthest-food (or center) with x priority."""
    if food:
        target = max(food, key=lambda f: _manhattan(head, f))
    else:
        target = ((w - 1) // 2, (h - 1) // 2)
    hx, hy = head
    tx, ty = target
    if hx > tx:
        return (hx - 1, hy)
    if hx < tx:
        return (hx + 1, hy)
    if hy > ty:
        return (hx, hy - 1)
    return (hx, hy + 1)



def _continuation_or_default_move(enemy, w, h):
    """Predict a simple bot that keeps moving straight; stacked starts default up."""
    body = [_pt(p) for p in enemy.get("body", [])]
    if not body:
        return None
    head = body[0]
    if len(body) > 1:
        neck = body[1]
        dx, dy = head[0] - neck[0], head[1] - neck[1]
        if (dx, dy) in MOVES.values():
            return (head[0] + dx, head[1] + dy)
    return (head[0], head[1] + 1)


def _nettogrof_serpentine_move(enemy, food, w, h, blocked=frozenset()):
    """Predict observed Nettogrof Java bot: vertical lawnmower sweep.

    Round logs show it usually travels straight up/down a column, shifts left
    at the top/bottom edge, then reverses vertical direction.  This prediction
    is only used as a tactical hint; generic safety checks still dominate.
    """
    body = [_pt(p) for p in enemy.get("body", [])]
    if not body:
        return None
    head = body[0]
    neck = body[1] if len(body) > 1 else head

    def ok(p):
        return _in_bounds(p, w, h) and p not in blocked

    hx, hy = head
    # While moving vertically, continue until the wall, then shift left/right.
    if len(body) > 1 and neck[0] == hx:
        if neck[1] < hy:  # moving up
            prefs = [(hx, hy + 1), (hx - 1, hy), (hx + 1, hy), (hx, hy - 1)]
        elif neck[1] > hy:  # moving down
            prefs = [(hx, hy - 1), (hx - 1, hy), (hx + 1, hy), (hx, hy + 1)]
        else:
            prefs = [(hx, hy + 1), (hx - 1, hy), (hx + 1, hy), (hx, hy - 1)]
    else:
        # Immediately after a horizontal shift on an edge it reverses direction.
        if hy >= h - 1:
            prefs = [(hx, hy - 1), (hx - 1, hy), (hx + 1, hy), (hx, hy + 1)]
        elif hy <= 0:
            prefs = [(hx, hy + 1), (hx - 1, hy), (hx + 1, hy), (hx, hy - 1)]
        else:
            prefs = [(hx, hy + 1), (hx, hy - 1), (hx - 1, hy), (hx + 1, hy)]

    for p in prefs:
        if ok(p):
            return p
    return prefs[0]




def _jump_flooding_predicted_move(enemy, snakes, w, h):
    """Predict coreyja jump-flooding's greedy Manhattan-Voronoi move.

    The reference bot scores legal moves by seeding its moved head first, then
    other heads, and counting the whole board by Manhattan distance (bodies are
    used only as a legal-move filter).  Matching this one-ply choice lets us
    distinguish the exact head-to-head square from merely-adjacent squares in
    cramped edge endgames.
    """
    body = [_pt(p) for p in enemy.get("body", [])]
    if not body:
        return None
    my_id = enemy.get("id")
    head = body[0]

    blocked = set()
    for s in snakes:
        b = [_pt(p) for p in s.get("body", [])]
        n = len(b)
        for idx, cell in enumerate(b):
            if idx == n - 1 and n >= 2:
                # Tail is enterable unless it is duplicated (just grew).
                if b[n - 2] == cell:
                    blocked.add(cell)
            else:
                blocked.add(cell)
    if len(body) >= 2:
        blocked.add(body[1])

    others = []
    for s in snakes:
        if s.get("id") == my_id:
            continue
        b = s.get("body", [])
        if b:
            others.append((s.get("id"), _pt(b[0])))

    def terr_score(candidate):
        heads = [(my_id, candidate)] + others
        mine = 0
        total = 0
        for x in range(w):
            for y in range(h):
                best_id = None
                best_d = None
                for sid, hp in heads:
                    d = abs(x - hp[0]) + abs(y - hp[1])
                    if best_d is None or d < best_d:
                        best_d = d
                        best_id = sid
                total += 1
                if best_id == my_id:
                    mine += 1
        return mine / total if total else 0

    best = None
    best_score = None
    for name, d in MOVES.items():  # original order: up, down, left, right
        p = _add(head, d)
        if not _in_bounds(p, w, h) or p in blocked:
            continue
        sc = terr_score(p)
        if best_score is None or sc > best_score:
            best_score = sc
            best = p
    return best

def _ccsnake2018_predicted_move(enemy, game_state, w, h):
    """Predict ccSnake2018 by running the local faithful port with `you` swapped.

    ccSnake usually avoids generic adjacent head-to-heads, so we do not want to
    blanket-block every square next to it.  But production round-1 losses were
    often exact head-to-heads on the move ccSnake's security/nearest-food logic
    chose.  The copied reference port is deterministic and fast enough for one
    opponent, and falling back to None preserves the older conservative scoring.
    """
    try:
        from tools import ccsnake_opponent
        gs = dict(game_state)
        gs["you"] = enemy
        move_name = ccsnake_opponent.move(gs).get("move")
        if move_name in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            pred = _add(head, MOVES[move_name])
            if _in_bounds(pred, w, h):
                return pred
    except Exception:
        return None
    return None



def _amphibious_arthur_predicted_move(enemy, game_state, w, h):
    """Predict coreyja Amphibious Arthur by running the copied local port.

    Arthur's production logs show a deterministic low-latency space/health
    recursion bot (balanced directions, long games).  A direct one-ply
    prediction helps avoid exact equal/longer head collisions while the generic
    adjacent-head rule still stays conservative because Arthur does not model
    our possible next head squares.
    """
    try:
        from tools import amphibious_arthur_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = amphibious_arthur_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None

def _btas_predicted_move(enemy, game_state, w, h):
    """Predict rdbrck BTAS by running the copied original port as that snake.

    BTAS is a real pathing bot; generic straight/farthest-food predictors miss
    its tactical turns (including logged head-to-head losses).  The local port is
    deterministic and fast enough for one-ply prediction, so ask it for its move
    with ``you`` swapped to the enemy and translate the move to a next cell.
    """
    try:
        from tools import btas_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = btas_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None


def _vulture_predicted_move(enemy, game_state, w, h):
    """Predict Spenca Vulture Snake by running the copied 2017 port as enemy.

    Vulture has stateful food-circling behavior that generic nearest/straight
    predictors miss in the rare long games.  The local port keeps module-global
    state; ``start`` resets it at game boundaries and this function is called
    once per turn, so it usually tracks the production opponent closely enough
    for tactical head/space scoring.
    """
    try:
        from tools import vulture_snake_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = vulture_snake_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None

def _xe_since_predicted_move(enemy, target, snakes, food, w, h):
    """One-step predictor for Xe__since: A* toward nearest food when behind/hungry,
    otherwise hunt our head when it is at least tied for biggest.  The original
    neighbor order is left,right,down,up; matching that helps avoid forced
    adjacent head-to-head losses in endgames.
    """
    body = [_pt(p) for p in enemy.get("body", [])]
    if not body:
        return None
    head = body[0]
    elen = enemy.get("length", len(body))
    lengths = [sn.get("length", len(sn.get("body", []))) for sn in snakes]
    biggest = max(lengths or [elen])
    # If behind or hungry, Xe chooses nearest food; otherwise in a 2-snake tied/
    # leading game it hunts the opponent head.
    if food and (elen < biggest or enemy.get("health", 100) <= 30):
        target = min(food, key=lambda f: _manhattan(head, f))
    if target is None:
        return None
    occ = set()
    for sn in snakes:
        for p in sn.get("body", []):
            occ.add(_pt(p))
    # Its port only treats occupied heads as strictly deadly in neighbor filtering
    # due to an original bug, but a final safety guard avoids bodies.  Predict a
    # safe, in-bounds first A* step with the original directional tie-break.
    prefs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    best = None
    best_key = None
    for i, d in enumerate(prefs):
        p = _add(head, d)
        if not _in_bounds(p, w, h) or p in occ:
            continue
        danger = 0
        for sn in snakes:
            if sn.get("id") == enemy.get("id"):
                continue
            sh = _pt(sn["head"] if "head" in sn else sn["body"][0])
            if _manhattan(p, sh) == 1:
                danger += 50
        key = (_manhattan(p, target) + danger, i)
        if best_key is None or key < best_key:
            best_key = key
            best = p
    return best

def move(game_state):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        you = game_state["you"]
        my_id = you.get("id")
        my_head = _pt(you["head"] if "head" in you else you["body"][0])
        my_len = you.get("length", len(you.get("body", [])))
        health = you.get("health", 100)
        food = [_pt(f) for f in board.get("food", [])]
        food_cells = set(food)
        snakes = board.get("snakes", [])

        occupied = _occupied_cells(snakes, food_cells)
        # Our current head is occupied in the board state, but all candidate
        # moves leave it, so only candidate destination membership matters.

        enemies = [s for s in snakes if s.get("id") != my_id]
        enemy_heads = [_pt(s["head"] if "head" in s else s["body"][0]) for s in enemies]
        enemy_max_len = max([s.get("length", len(s.get("body", []))) for s in enemies] or [0])
        enemy_next_pred = []
        enemy_possible_next = set()
        random_longer_enemy_next = set()
        random_direct_enemy_next = []
        has_randomish_enemy = False
        randomish_equal_threat = False
        has_jump_flooding_enemy = False
        has_vulture_enemy = False
        for e in enemies:
            eh = _pt(e["head"] if "head" in e else e["body"][0])
            elen = e.get("length", len(e.get("body", [])))
            ename = e.get("name", "")
            is_xe = "Xe" in ename or "since" in ename.lower()
            preds = set()
            is_ccsnake = "ccsnake" in ename.lower() or "ccsnake2018" in ename.lower()
            if is_xe:
                pred = _xe_since_predicted_move(e, my_head, snakes, food, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "jump-flooding" in ename.lower():
                has_jump_flooding_enemy = True
                pred = _jump_flooding_predicted_move(e, snakes, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_ccsnake:
                pred = _ccsnake2018_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "amphibious-arthur" in ename.lower() or "amphibious" in ename.lower():
                pred = _amphibious_arthur_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "rdbrck" in ename.lower() or "btas" in ename.lower():
                pred = _btas_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "vulture" in ename.lower() or "spenca" in ename.lower():
                pred = _vulture_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            else:
                preds.add(_simple_opponent_target_move(eh, food, w, h))
                straight = _continuation_or_default_move(e, w, h)
                if straight is not None and _in_bounds(straight, w, h):
                    preds.add(straight)
            if "Nettogrof" in ename:
                pred = _nettogrof_serpentine_move(e, food, w, h, occupied)
                if pred is not None:
                    preds.add(pred)
            for pred in preds:
                enemy_next_pred.append((pred, elen))
            # Any legal enemy move may immediately partition space even if we
            # win head-to-heads against shorter snakes.  Use these cells as a
            # conservative one-ply space estimate below.
            is_randomish = ("bombastic-bob" in ename.lower() or "scape-goat" in ename.lower() or "awesome-snake" in ename.lower() or "tim-hub" in ename.lower() or "vulture" in ename.lower() or "spenca" in ename.lower() or "pinky-snek" in ename.lower() or "moxuz" in ename.lower())
            awesome_like = ("awesome-snake" in ename.lower() or "tim-hub" in ename.lower())
            vulture_like = ("vulture" in ename.lower() or "spenca" in ename.lower())
            awesome_scores = {}
            if is_randomish:
                has_randomish_enemy = True
                if vulture_like:
                    has_vulture_enemy = True
                # Awesome-Snake chooses randomly among the highest immediate
                # cell scores: adjacent food beats empty, empty beats body/wall.
                # Bob/Scape-Goat are closer to random-legal, handled by using
                # all legal next heads as direct collision candidates.
                raw_body = set()
                for sn0 in snakes:
                    for seg0 in sn0.get("body", []):
                        raw_body.add(_pt(seg0))
                for d0 in MOVES.values():
                    ep0 = _add(eh, d0)
                    if not _in_bounds(ep0, w, h):
                        awesome_scores[ep0] = -100
                    elif ep0 in raw_body:
                        awesome_scores[ep0] = -1
                    elif ep0 in food_cells:
                        awesome_scores[ep0] = 1
                    else:
                        awesome_scores[ep0] = 0
                best_awesome_score = max(awesome_scores.values() or [-100])
            for d in MOVES.values():
                ep = _add(eh, d)
                if _in_bounds(ep, w, h) and ep not in occupied:
                    enemy_possible_next.add(ep)
                    if is_randomish:
                        # Direct head collision risk: for Awesome only the max-
                        # scored cells are actually chosen; for the purely random
                        # bots any legal cell can be selected.
                        if elen >= my_len and ((not awesome_like) or awesome_scores.get(ep, -100) == best_awesome_score):
                            random_direct_enemy_next.append((ep, elen))
                        # Random-ish bots become dangerous as soon as they are
                        # equal/longer, including the turn after they take
                        # adjacent food.  Logged Awesome-Snake losses came from
                        # following a length-1-short enemy into an edge pocket
                        # just before it ate and became equal/longer.
                        if elen >= my_len or ((not vulture_like) and elen + 1 >= my_len and ep in food_cells):
                            random_longer_enemy_next.add(ep)
                        if elen >= (my_len if vulture_like else my_len - 1):
                            randomish_equal_threat = True

        candidates = []
        for name, delta in MOVES.items():
            nxt = _add(my_head, delta)
            if not _in_bounds(nxt, w, h):
                continue
            if nxt in occupied:
                continue

            # Avoid squares an equal/longer enemy head could also choose.  This
            # is the main source of ties in the clone-vs-clone logs.
            h2h_risk = False
            h2h_soft_penalty = 0
            for e in enemies:
                eh = _pt(e["head"] if "head" in e else e["body"][0])
                elen = e.get("length", len(e.get("body", [])))
                # ccSnake2018 already treats our possible next head cells as
                # danger and usually will not intentionally take generic
                # adjacent head-to-heads.  Overblocking every adjacent square
                # caused logged losses where we chose a one-cell self-trap
                # instead of the large safe region next to ccSnake.  Keep the
                # stricter generic rule for hunting/minimax-style opponents.
                # jump-flooding has an exact greedy Voronoi predictor; broad
                # adjacent blocking trapped us in logged corner losses.  BTAS also
                # has a predictor, but the copied port can miss occasional moves;
                # use a soft adjacent-head penalty for BTAS instead of a blanket ban.
                ename = e.get("name", "").lower()
                if "rdbrck" in ename or "btas" in ename:
                    if _manhattan(nxt, eh) == 1 and elen >= my_len:
                        h2h_soft_penalty = max(h2h_soft_penalty, 150)
                    continue
                if "ccsnake" in ename or "ccsnake2018" in ename or "jump-flooding" in ename or "awesome-snake" in ename or "tim-hub" in ename or "pinky-snek" in ename or "moxuz" in ename:
                    continue
                if _manhattan(nxt, eh) == 1 and elen >= my_len:
                    h2h_risk = True
                    break

            # For space evaluation, pretend our new head becomes blocked and
            # all moving tails are free.
            future_blocked = set(occupied)
            future_blocked.add(nxt)
            area = _flood_count(nxt, w, h, future_blocked, limit=w * h)
            contested_blocked = set(future_blocked)
            contested_blocked.update(enemy_possible_next)
            # If we are moving onto a predicted enemy square while longer, keep
            # that square available for the attack; otherwise treat all enemy
            # next-step options as temporary walls.
            if my_len > enemy_max_len:
                contested_blocked.discard(nxt)
            safe_area = _flood_count(nxt, w, h, contested_blocked, limit=w * h)
            territory = _territory_count(nxt, enemy_heads, w, h, future_blocked, my_len, enemy_max_len)
            nearest_food = _nearest_food_distance(nxt, food)
            path_food = _shortest_food_distance(nxt, food_cells, w, h, future_blocked)
            safe_food = _nearest_uncontested_food_distance(nxt, food, enemy_heads, my_len, enemy_max_len)
            center_dist = _manhattan(nxt, ((w - 1) // 2, (h - 1) // 2))
            edge_dist = min(nxt[0], nxt[1], w - 1 - nxt[0], h - 1 - nxt[1])
            choke_risk = _articulation_risk(nxt, w, h, future_blocked)

            score = 0
            score += area * 80                  # never trap ourselves
            score += safe_area * (140 if enemies else 0)  # account for enemy cuts
            if enemies and safe_area < min(18, my_len + 2):
                score -= (min(18, my_len + 2) - safe_area) * 1800
            score += territory * (18 if enemies else 0)  # prefer space we reach first
            # If a much larger opponent survives into the endgame, avoid
            # voluntarily entering tiny one/two-cell pockets it controls.
            # This is deliberately a late/tactical penalty so early wall-
            # crashing opponents are still beaten by pure survival.
            bigger_heads = [
                _pt(e["head"] if "head" in e else e["body"][0])
                for e in enemies
                if e.get("length", len(e.get("body", []))) >= my_len + 3
            ]
            if bigger_heads and area <= max(6, my_len // 3):
                score -= (max(6, my_len // 3) + 1 - area) * 2500
            score += edge_dist * 32              # prefer room away from walls
            if enemies and enemy_max_len >= my_len + 2:
                # A longer area bot can use board edges as a wall to box us in;
                # bias back toward the interior before the trap becomes forced.
                score += edge_dist * 120
                if edge_dist == 0:
                    score -= 1200
                elif edge_dist == 1:
                    score -= 300
            if has_randomish_enemy and randomish_equal_threat:
                # Random legal-move opponents do not deliberately give us safe
                # inward exits; when lengths are close, board edges/corners make
                # one unlucky random step enough to seal us in.  Bias toward the
                # interior before the trap is forced.
                near_random_dist = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                if near_random_dist <= 8:
                    edge_mul = 0.45 if has_vulture_enemy else 1.0
                    score += edge_dist * int(600 * edge_mul)
                    if edge_dist == 0:
                        score -= int(8000 * edge_mul)
                    elif edge_dist == 1:
                        score -= int(2500 * edge_mul)
                    # Also avoid one-cell-wide corridors close to the enemy body,
                    # even if they are not on the board edge yet.
                    if area < 30 or choke_risk:
                        score -= int(((30 - min(area, 30)) * 650 + choke_risk * 9000) * edge_mul)
                    if safe_area < 35:
                        score -= int((35 - safe_area) * 500 * edge_mul)
            if has_jump_flooding_enemy and enemy_max_len >= my_len and edge_dist == 0:
                # Jump-flooding's Voronoi bot often chases us along the outer row/
                # column and lets the board edge close the trap.  When it is at
                # least as long and already nearby, strongly prefer edge moves that
                # run back toward mid-board instead of deeper into a corner.
                if enemy_heads and min(_manhattan(nxt, eh) for eh in enemy_heads) <= 3:
                    corner_dist = min(
                        nxt[0] + nxt[1],
                        nxt[0] + (h - 1 - nxt[1]),
                        (w - 1 - nxt[0]) + nxt[1],
                        (w - 1 - nxt[0]) + (h - 1 - nxt[1]),
                    )
                    score += corner_dist * 4000 - 7500
            if enemies and area > 20:
                score -= choke_risk * 2200
            if random_longer_enemy_next:
                future_safe_exits = 0
                for nn in _neighbors(nxt):
                    if not _in_bounds(nn, w, h) or nn in future_blocked:
                        continue
                    # Next-turn destinations adjacent to longer/equal random heads
                    # can become forced losing head-to-heads; count only clean exits.
                    if any(_manhattan(nn, ep) <= 1 for ep in random_longer_enemy_next):
                        continue
                    future_safe_exits += 1
                if future_safe_exits == 0:
                    score -= 60000
                elif future_safe_exits == 1:
                    score -= 9000
            score -= center_dist * 2            # stay roughly central
            # Food urgency.  In long games against area/Voronoi bots, the main
            # remaining failure mode is starving while our large space terms keep
            # us orbiting a safe-looking region.  Make low-health food pressure
            # nonlinear, but leave healthy early-game behaviour mostly unchanged.
            if health < 8:
                food_weight = 4000
            elif health < 15:
                food_weight = 1800
            elif health < 30:
                food_weight = 260
            elif health < 50:
                food_weight = 35
            else:
                food_weight = 16
            # Against competent area bots (not wall-crashers), falling behind in
            # length makes every future head-to-head and territory split worse.
            # Add controlled food pressure when an enemy is as long/longer; the
            # large space terms above still prevent obvious traps.
            food_dist = path_food if health < 30 else nearest_food
            if enemies and my_len <= enemy_max_len:
                food_weight += min(160, 45 + (enemy_max_len - my_len) * 20)
                # Do not let catch-up pressure drag us toward food a longer
                # opponent can reach first; use uncontested food unless starving.
                if health >= 30:
                    if safe_food < 99:
                        food_dist = safe_food
                    else:
                        food_weight = min(food_weight, 25)
            score -= food_dist * food_weight
            if health < 15:
                # In production Pinky losses we sometimes orbited safe space until
                # health 1 even with reachable food nearby; at critical health,
                # a real path to food must dominate roomy-but-starving moves.
                if path_food >= 99:
                    score -= 250000
                elif path_food >= health:
                    score -= (path_food - health + 1) * 35000
                else:
                    score += (health - path_food) * 8000
            if nxt in food_cells:
                if health >= 30 and _food_contested_from(nxt, food_cells, enemy_heads, my_len, enemy_max_len):
                    score -= 1800
                else:
                    score += (2500 if health < 15 else (1200 if health < 30 else (260 if health < 60 else 120))) + (1400 if enemies and my_len <= enemy_max_len else 0)
            if h2h_risk:
                score -= 500000000
            if h2h_soft_penalty:
                score -= h2h_soft_penalty
            for ep, elen in random_direct_enemy_next:
                if nxt == ep and my_len <= elen:
                    score -= 500000000
            for eh, e in zip(enemy_heads, enemies):
                elen = e.get("length", len(e.get("body", [])))
                if my_len >= elen + 3 and _manhattan(nxt, eh) == 1 and area >= my_len + 8:
                    score += 120  # pressure much shorter snakes without overriding space safety
            # Known opponent often deterministically moves into one square.
            # Avoid equal/longer head-to-heads, but if we are longer this is a
            # controlled attack and should be preferred.
            for pred, elen in enemy_next_pred:
                if nxt == pred:
                    if my_len >= elen + 3 and area >= my_len + 8:
                        score += 1200
                    elif my_len > elen:
                        score += 50
                    else:
                        score -= 50000000
            candidates.append((score, name, nxt, area, h2h_risk))

        if candidates:
            # Deterministic tie-break: high score, then a gentle clockwise bias.
            order = {"up": 3, "right": 2, "down": 1, "left": 0}
            candidates.sort(key=lambda x: (x[0], order[x[1]]), reverse=True)
            return {"move": candidates[0][1]}

        # Last resort: choose any in-bounds move, then any legal word.
        for name, delta in MOVES.items():
            if _in_bounds(_add(my_head, delta), w, h):
                return {"move": name}
        return {"move": "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
