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



def _tail_path_distance(pos, tail, w, h, blocked):
    """BFS distance from pos to our tail, allowing the tail square as a target.

    In long games where we are much longer than Eremetic Eric, the safest
    strategy is to keep a route back to our own tail instead of consuming every
    food pellet and filling the board.
    """
    if tail is None:
        return 99
    b = set(blocked)
    b.discard(pos)
    b.discard(tail)
    seen = {pos}
    q = [(pos, 0)]
    qi = 0
    while qi < len(q):
        cur, d = q[qi]
        qi += 1
        if cur == tail:
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



def _nbw_ruby_predicted_move(enemy, game_state, w, h):
    """Predict nbw-ruby by running the copied faithful port as that snake.

    Production nbw-ruby losses are mostly long-game tactical head pressure from a
    real weighted-paint/path-search bot.  Exact one-ply prediction is safer than
    broad retuning: keep generic adjacent-head avoidance, but add a large penalty
    for the square ruby itself is likely to take.
    """
    try:
        from tools import nbw_ruby_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = nbw_ruby_opponent.move(pseudo).get("move")
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


def _eremetic_eric_predicted_move(enemy, game_state, w, h):
    """Predict coreyja Eremetic Eric by running the copied coiling/tail-chase port.

    Eric mostly follows its own tail and only eats when its loop/health model says
    it must.  A direct one-ply prediction is useful in the rare equal-length end
    games where generic adjacent-head avoidance cannot distinguish the actual
    square it will choose.
    """
    try:
        from tools import eremetic_eric_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = eremetic_eric_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None


def _flipez_crystal_predicted_move(enemy, game_state, w, h):
    """Predict Flipez Crystal by running the copied original port as enemy.

    Flipez is a nearest-food/center bot that also avoids predicted longer/equal
    enemy head squares.  It grows well in long games, so exact one-ply
    prediction is useful for tactical head pressure without changing the
    survival-first core.
    """
    try:
        from tools import flipez_crystal_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = flipez_crystal_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None


def _battlesnake_elon_predicted_move(enemy, game_state, w, h):
    """Predict jackisherwood battlesnake-elon by running the copied faithful port.

    Elon alternates between tail-chasing, food-seeking, and collision-avoidance
    with deterministic lodash-style tie breaks.  Round-0 failures were mostly
    exact head-to-heads near edges where our broad adjacent-head rule could not
    distinguish the square Elon would actually choose.
    """
    try:
        from tools import battlesnake_elon_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = battlesnake_elon_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None

def _tantilla_predicted_move(enemy, game_state, w, h):
    """Run the copied MorganConrad/tantilla port for a one-ply prediction."""
    try:
        import copy
        from tools import tantilla_opponent
        gs = copy.deepcopy(game_state)
        gs["you"] = copy.deepcopy(enemy)
        chosen = tantilla_opponent.calculate_move(gs)
        d = chosen.get("dir") if isinstance(chosen, dict) else None
        if d in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[d])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None



def _cornelius_predicted_move(enemy, game_state, w, h):
    """Predict ChaelCodes Cornelius by running the copied faithful port.

    Cornelius is a deterministic scorer: it strongly likes non-zero-edge cells,
    food, and enough flood-fill space, with an equal/longer adjacent-head
    penalty.  Production losses are long games, so exact one-ply prediction is
    useful for head/tactical scoring while separate self-lookahead avoids our
    own boxes.
    """
    try:
        from tools import cornelius_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = cornelius_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None



def _famished_frank_predicted_move(enemy, game_state, w, h):
    """Predict coreyja Famished Frank by running the copied A* food/corner port.

    Frank greedily A* paths to food until target length, then corners, with
    tail/random fallbacks.  Production losses are often exact longer-head
    pressure after Frank outgrows us, so feed its one-ply next cell into the
    existing predicted-collision scoring.
    """
    try:
        from tools import famished_frank_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = famished_frank_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None

def _beames_predicted_move(enemy, game_state, w, h):
    """Predict kentmacdonald2 Beames by running the copied A*/food port."""
    try:
        from tools import beames_opponent
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = beames_opponent.move(pseudo).get("move")
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        return None
    return None

def _battlejake2019_predicted_move(enemy, game_state, w, h):
    """Predict joshhartmann11 battleJake2019 by running the copied 2019 port.

    BattleJake is mostly deterministic filters (wall/body/head danger, food when
    hungry/small, flee heads, go straight) with a random fallback.  A one-ply
    copy is useful for exact longer/equal head collisions; strategic scoring
    below handles its remaining edge/self-box endgames.
    """
    try:
        import random
        from tools import battlejake2019_opponent
        # Make the port's rare random fallback deterministic and side-effect light.
        state = random.getstate()
        random.seed(17 + int(game_state.get("turn", 0)))
        pseudo = {
            "game": game_state.get("game", {}),
            "turn": game_state.get("turn", 0),
            "board": game_state.get("board", {}),
            "you": enemy,
        }
        mv = battlejake2019_opponent.move(pseudo).get("move")
        random.setstate(state)
        if mv in MOVES:
            head = _pt(enemy["head"] if "head" in enemy else enemy["body"][0])
            nxt = _add(head, MOVES[mv])
            if _in_bounds(nxt, w, h):
                return nxt
    except Exception:
        try:
            random.setstate(state)
        except Exception:
            pass
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
        my_body = [_pt(p) for p in you.get("body", [])]
        my_tail = my_body[-1] if my_body else None
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
        has_nbw_ruby_enemy = False
        has_eremetic_enemy = False
        has_gigantic_george_enemy = False
        has_flipez_crystal_enemy = False
        has_battlesnake_elon_enemy = False
        has_tantilla_enemy = False
        has_cornelius_enemy = False
        has_battlejake_enemy = False
        has_famished_frank_enemy = False
        has_beames_enemy = False
        for e in enemies:
            eh = _pt(e["head"] if "head" in e else e["body"][0])
            elen = e.get("length", len(e.get("body", [])))
            ename = e.get("name", "")
            is_xe = "Xe" in ename or "since" in ename.lower()
            preds = set()
            is_ccsnake = "ccsnake" in ename.lower() or "ccsnake2018" in ename.lower()
            is_flipez = "flipez" in ename.lower() or "flipez-crystal" in ename.lower()
            is_tantilla = "tantilla" in ename.lower() or "morganconrad" in ename.lower()
            is_cornelius = "cornelius" in ename.lower() or "chaelcodes" in ename.lower()
            is_battlejake = "battlejake" in ename.lower() or "joshhartmann11" in ename.lower()
            is_famished = "famished-frank" in ename.lower() or "famished" in ename.lower()
            is_beames = "beames" in ename.lower() or "kentmacdonald2" in ename.lower()
            if is_beames:
                has_beames_enemy = True
                pred = _beames_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_famished:
                has_famished_frank_enemy = True
                pred = _famished_frank_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_battlejake:
                has_battlejake_enemy = True
                pred = _battlejake2019_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_cornelius:
                has_cornelius_enemy = True
                pred = _cornelius_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_tantilla:
                has_tantilla_enemy = True
                pred = _tantilla_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_flipez:
                has_flipez_crystal_enemy = True
                pred = _flipez_crystal_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif is_xe:
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
            elif "nbw-ruby" in ename.lower():
                has_nbw_ruby_enemy = True
                pred = _nbw_ruby_predicted_move(e, game_state, w, h)
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
            elif "gigantic-george" in ename.lower() or "gigantic" in ename.lower() or "george" in ename.lower():
                has_gigantic_george_enemy = True
                pred = _eremetic_eric_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "eremetic-eric" in ename.lower() or "eremetic" in ename.lower():
                has_eremetic_enemy = True
                pred = _eremetic_eric_predicted_move(e, game_state, w, h)
                if pred is not None:
                    preds.add(pred)
            elif "beames" in ename.lower() or "kentmacdonald2" in ename.lower():
                # Exact predictor already added above; keep generic adjacent-head rule.
                pass
            elif "battlesnake-elon" in ename.lower() or "jackisherwood" in ename.lower() or "elon" in ename.lower():
                has_battlesnake_elon_enemy = True
                pred = _battlesnake_elon_predicted_move(e, game_state, w, h)
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
                if "rdbrck" in ename or "btas" in ename or "battlesnake-elon" in ename or "jackisherwood" in ename or "elon" in ename:
                    if _manhattan(nxt, eh) == 1 and elen >= my_len:
                        # For deterministic predicted bots, an exact predicted
                        # collision is penalized below; adjacent non-predicted
                        # squares are risky but often the only escape from edge
                        # pockets, so do not blanket-ban them.
                        h2h_soft_penalty = max(h2h_soft_penalty, 250 if ("elon" in ename or "jackisherwood" in ename) else 150)
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
            tail_dist = _tail_path_distance(nxt, my_tail, w, h, future_blocked)
            # One-ply self-lookahead using our actual shifted body.  Static
            # flood-fill can overvalue cells inside a nearly closed loop because
            # it treats moving tails optimistically; in Cornelius logs several
            # losses were simply moving into a square with no legal next move.
            my_next_body = [nxt] + my_body
            if nxt not in food_cells and my_next_body:
                my_next_body = my_next_body[:-1]
            next_self_blocked = set()
            for sn0 in snakes:
                if sn0.get("id") == my_id:
                    continue
                b0 = [_pt(p) for p in sn0.get("body", [])]
                if b0:
                    next_self_blocked.update(b0[:-1])
            next_self_blocked.update(my_next_body[:-1])
            self_next_exits = sum(
                1 for nn in _neighbors(nxt)
                if _in_bounds(nn, w, h) and nn not in next_self_blocked
            )

            score = 0
            score += area * 80                  # never trap ourselves
            score += safe_area * (140 if enemies else 0)  # account for enemy cuts
            if enemies and safe_area < min(18, my_len + 2):
                score -= (min(18, my_len + 2) - safe_area) * 1800
            if self_next_exits == 0:
                score -= 90000000
            elif self_next_exits == 1 and enemies and safe_area < max(24, my_len + 4):
                score -= 18000
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
            if has_battlejake_enemy and health >= 55 and my_len >= enemy_max_len + 7:
                # BattleJake2019 can survive long while staying much shorter; our
                # round-0 losses while ahead were self-boxes from taking/continuing
                # corner-edge routes.  Once safely ahead, stop valuing optional
                # growth and strongly prefer interior, tail-reachable, non-choke
                # moves so the shorter opponent eventually crashes first.
                score += edge_dist * 1200
                if edge_dist == 0:
                    score -= 18000
                elif edge_dist == 1:
                    score -= 4500
                if tail_dist >= 99:
                    score -= 90000
                else:
                    score += max(0, 34 - tail_dist) * 1500
                    if tail_dist <= 7:
                        score += 10000
                need_area = max(18, my_len // 2)
                if area < need_area:
                    score -= (need_area - area) * 6500
                if safe_area < max(22, my_len // 2):
                    score -= (max(22, my_len // 2) - safe_area) * 1200
                if choke_risk:
                    score -= choke_risk * 7000
            if has_battlejake_enemy and health >= 65 and my_len >= enemy_max_len + 4:
                # Round-1 BattleJake losses were all long edge/corner self-boxes,
                # often with only a +4..+6 length lead so the stricter optional-
                # food suppression above did not engage.  Keep this intentionally
                # light: a little more interior/tail preference and rejection of
                # zero-exit edge pockets, without overpowering the normal space
                # and food terms that local BattleJake samples rely on.
                score += edge_dist * 180
                if edge_dist == 0:
                    score -= 3500
                elif edge_dist == 1:
                    score -= 900
                if tail_dist < 99:
                    score += max(0, 18 - tail_dist) * 220
                clean_exits = 0
                for nn in _neighbors(nxt):
                    if not _in_bounds(nn, w, h) or nn in future_blocked:
                        continue
                    if any(_manhattan(nn, ep) <= 1 for ep in enemy_possible_next):
                        continue
                    clean_exits += 1
                if clean_exits == 0:
                    score -= 25000
                elif clean_exits == 1 and edge_dist == 0 and safe_area < 22:
                    score -= 6000
                if choke_risk and edge_dist <= 1 and safe_area < 30:
                    score -= choke_risk * 1800
            if has_cornelius_enemy and my_len >= enemy_max_len + 4 and health >= 45:
                # Cornelius often stays smaller while we overgrow; production
                # losses were self-boxes along edges/top loops, not starvation.
                # When safely ahead, de-emphasize optional food and keep a route
                # to our tail/interior.
                score += edge_dist * 520
                if edge_dist == 0:
                    score -= 9000
                elif edge_dist == 1:
                    score -= 2200
                if tail_dist >= 99:
                    score -= 60000
                else:
                    score += max(0, 28 - tail_dist) * 900
                if choke_risk:
                    score -= choke_risk * 4200
            if has_cornelius_enemy and health >= 45 and enemy_max_len >= my_len + 2:
                # When Cornelius is clearly longer, avoid letting its sweep/body wall
                # herd us into an edge pocket.  Keep this narrower than the safely-
                # ahead mode above; broad equal-length edge penalties hurt local play.
                near_corn = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                if near_corn <= 6 or edge_dist <= 1:
                    clean_exits = 0
                    for nn in _neighbors(nxt):
                        if not _in_bounds(nn, w, h) or nn in future_blocked:
                            continue
                        if any(_manhattan(nn, ep) <= 1 for ep in enemy_possible_next):
                            continue
                        clean_exits += 1
                    if clean_exits == 0:
                        score -= 65000
                    elif clean_exits == 1 and (edge_dist <= 1 or near_corn <= 3):
                        score -= 16000
                    score += edge_dist * 160
                    if edge_dist == 0:
                        score -= 5000
                    elif edge_dist == 1:
                        score -= 1200
                    if safe_area < 26:
                        score -= (26 - safe_area) * 450
                    if choke_risk and safe_area < 34:
                        score -= choke_risk * 3500
            if has_famished_frank_enemy and health >= 45 and enemy_max_len >= my_len - 1:
                # Famished Frank greedily paths to food and often becomes longer,
                # then uses its body plus board edges to squeeze us.  Production
                # losses are commonly optional edge-food/corridor entries while
                # we are healthy but not longer.  Add a targeted interior/escape
                # bias only for this matchup/length regime; exact predicted head
                # collisions are still handled separately below.
                near_frank = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                if near_frank <= 7 or edge_dist <= 1:
                    clean_exits = 0
                    for nn in _neighbors(nxt):
                        if not _in_bounds(nn, w, h) or nn in future_blocked:
                            continue
                        if any(_manhattan(nn, ep) <= 1 for ep in enemy_possible_next):
                            continue
                        clean_exits += 1
                    score += edge_dist * 260
                    if edge_dist == 0:
                        score -= 6500
                    elif edge_dist == 1:
                        score -= 1600
                    if clean_exits == 0:
                        score -= 55000
                    elif clean_exits == 1 and (edge_dist <= 1 or near_frank <= 4):
                        score -= 14000
                    if safe_area < 28:
                        score -= (28 - safe_area) * 550
                    if choke_risk and safe_area < 40:
                        score -= choke_risk * 4200
                    # Frank's longer food-path body often turns medium-size edge
                    # regions into one-way boxes.  Prefer candidates that preserve
                    # a route to our moving tail, even when raw area is similar.
                    if tail_dist >= 99:
                        score -= 12000
                        if self_next_exits <= 1:
                            score -= 22000
                    else:
                        score += max(0, 20 - tail_dist) * 450
            if has_flipez_crystal_enemy and enemy_max_len >= my_len:
                # Flipez-crystal is a competent nearest-food/center chaser.
                # Logged losses usually had us shorter and crowded near a wall,
                # so add a matchup-specific interior/safe-area bias when behind.
                near_flipez = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                if near_flipez <= 6 or edge_dist <= 1:
                    score += edge_dist * 260
                    if edge_dist == 0:
                        score -= 6500
                    elif edge_dist == 1:
                        score -= 1800
                    if safe_area < 30:
                        score -= (30 - safe_area) * 520
                    if choke_risk:
                        score -= choke_risk * 4500
                    if enemy_max_len >= my_len + 2:
                        # Round-1 Flipez losses were usually not immediate head
                        # collisions; we followed an edge/one-cell corridor while
                        # a much longer nearest-food chaser closed all exits.  Raw
                        # flood-fill overvalues these corridors because the enemy's
                        # next step is not yet a permanent wall.  Count next-turn
                        # exits that are not adjacent to any plausible enemy head
                        # move, and heavily reject candidates with no clean escape.
                        clean_exits = 0
                        for nn in _neighbors(nxt):
                            if not _in_bounds(nn, w, h) or nn in future_blocked:
                                continue
                            if any(_manhattan(nn, ep) <= 1 for ep in enemy_possible_next):
                                continue
                            clean_exits += 1
                        if clean_exits == 0:
                            score -= 45000
                        elif clean_exits == 1 and edge_dist <= 1:
                            score -= 18000
                        if safe_area < 12:
                            score -= (12 - safe_area) * 7000
                        if edge_dist == 0 and near_flipez <= 5 and safe_area < 35:
                            score -= (35 - safe_area) * 900
            if has_battlesnake_elon_enemy and enemy_max_len >= my_len:
                # BattleSnakeElon often tail-chases/collision-avoids along compact
                # body walls.  The sole round-1 production loss came from following
                # a slightly longer Elon across the top-left edge: static flood-fill
                # looked huge, but our chosen moves left zero/one clean next-turn
                # exits once Elon's plausible next head squares were considered.
                # Keep the earlier soft adjacent-head policy (exact predictor handles
                # direct collisions), but reject edge/body-pocket moves with no
                # clean escape while Elon is at least as long.
                near_elon = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                if near_elon <= 6 or edge_dist <= 1:
                    clean_exits = 0
                    for nn in _neighbors(nxt):
                        if not _in_bounds(nn, w, h) or nn in future_blocked:
                            continue
                        if any(_manhattan(nn, ep) <= 1 for ep in enemy_possible_next):
                            continue
                        clean_exits += 1
                    if clean_exits == 0:
                        score -= 70000
                    elif clean_exits == 1:
                        score -= 16000 if edge_dist <= 1 or near_elon <= 3 else 7000
                    # Small interior preference, but not so large that it overrides
                    # clear space/food in normal mid-board positions.
                    score += edge_dist * 180
                    if edge_dist == 0 and safe_area < 35:
                        score -= (35 - safe_area) * 700 + 5000
                    if choke_risk and safe_area < 40:
                        score -= choke_risk * 4500
            if has_nbw_ruby_enemy and enemy_max_len >= my_len:
                # nbw-ruby's weighted-paint bot is especially good at turning the
                # board edge plus its body into a zipper trap.  Round-1 losses were
                # mostly us continuing along the top/left edge while shorter or
                # equal until every exit was our body or a losing head race.  Make
                # the interior/escape bias much stronger for this matchup, but only
                # when ruby is not shorter so we still take safe kills/edge food
                # while ahead.
                near_nbw = min((_manhattan(nxt, eh) for eh in enemy_heads), default=99)
                nbw_edge_mul = 1.0 if enemy_max_len >= my_len + 2 else 0.55
                if near_nbw <= 8 or edge_dist <= 1:
                    score += int(edge_dist * 520 * nbw_edge_mul)
                    if edge_dist == 0:
                        score -= int(14000 * nbw_edge_mul)
                    elif edge_dist == 1:
                        score -= int(4200 * nbw_edge_mul)
                    if safe_area < 32:
                        score -= int((32 - safe_area) * 650 * nbw_edge_mul)
                    if area < 28 or choke_risk:
                        score -= int(((28 - min(area, 28)) * 500 + choke_risk * 4500) * nbw_edge_mul)
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
            if (has_eremetic_enemy or has_gigantic_george_enemy) and health >= 45 and my_len >= enemy_max_len + 5:
                # Eremetic Eric deliberately coils and stays short.  In round-0
                # losses we were usually far longer, healthy, and eventually
                # self-boxed after eating too much optional food.  When safely
                # ahead, stop chasing/eating food and win by survival/space.
                food_weight = min(food_weight, 0)
                # Also actively preserve our own tail route.  Eric is not trying
                # to outgrow us; most remaining production losses are self-boxes
                # after we become 40+ cells long.  A reachable tail is a better
                # safety signal than raw flood-fill in these endgames.
                if tail_dist >= 99:
                    score -= 30000
                else:
                    score += max(0, 30 - tail_dist) * 350
                    if area < my_len // 3:
                        score -= (my_len // 3 - area) * 500
                # Gigantic George is essentially Eremetic Eric and usually stays
                # short.  Production losses were giant-snake self-boxes after we
                # kept eating optional food and then followed the outer wall until
                # no exit remained.  In this matchup, when we are already safely
                # ahead, make *tail reachability* the dominant objective: following
                # our own tail is safer than maximizing static flood-fill, because
                # the tail will keep opening cells if we stop eating.
                if has_gigantic_george_enemy:
                    # Do not enter this mode too early: local George can still
                    # outgrow/pressure us at medium length, so preserve normal
                    # food/space play until we are a genuinely giant snake.
                    if my_len >= 35 and my_len >= enemy_max_len + 20:
                        if tail_dist >= 99:
                            score -= 150000
                        else:
                            score += 120000 - tail_dist * 2200
                            if tail_dist <= 6:
                                score += 35000
                    score += edge_dist * 3200
                    if edge_dist == 0:
                        score -= 26000
                    elif edge_dist == 1:
                        score -= 8000
                    tiny_area = max(8, my_len // 5)
                    if area < tiny_area:
                        # Do not blindly tail-chase into a one/two-cell cul-de-sac;
                        # local George losses showed that an immediately reachable
                        # tail with almost no following space is worse than taking
                        # a large open region, even if that region contains food.
                        score -= (tiny_area - area) * 30000
                    if choke_risk and (tail_dist >= 99 or my_len >= 35):
                        score -= choke_risk * 6000
                    if safe_area < max(24, my_len // 2) and tail_dist >= 99:
                        score -= (max(24, my_len // 2) - safe_area) * 900
            if has_tantilla_enemy and health >= 55 and my_len >= enemy_max_len + 8:
                # Tantilla is a tail-chasing survival bot that usually stays
                # short.  The round-0 losses were not tactical collisions; we
                # had grown to 17-36 cells, kept taking optional food, and
                # eventually self-boxed while Tantilla remained length 6-8.
                # Once safely ahead, stop growing and make tail reachability /
                # non-edge space the main objective.
                food_weight = min(food_weight, 0)
                if tail_dist >= 99:
                    score -= 120000
                else:
                    score += max(0, 35 - tail_dist) * 1800
                    if tail_dist <= 6:
                        score += 12000
                score += edge_dist * 900
                if edge_dist == 0:
                    score -= 9000
                elif edge_dist == 1:
                    score -= 2500
                need_area = max(14, my_len // 2)
                if area < need_area:
                    score -= (need_area - area) * 5000
                if choke_risk:
                    score -= choke_risk * 5000
            if enemies and my_len <= enemy_max_len:
                food_weight += min(160, 45 + (enemy_max_len - my_len) * 20)
                if has_famished_frank_enemy and health >= 30:
                    # Frank is almost entirely food-driven until length 33.  If we
                    # fall behind, raise catch-up pressure but still prefer
                    # reachable/uncontested food so we do not chase through its wall.
                    food_weight += min(260, 100 + (enemy_max_len - my_len) * 35)
                    food_dist = path_food if path_food < 99 else food_dist
                if has_flipez_crystal_enemy:
                    # Flipez wins its rare games by outgrowing us with steady
                    # nearest-food chasing.  When behind, make reachable food a
                    # first-class objective instead of letting static space terms
                    # keep us orbiting safely but shorter.
                    food_weight += min(520, 180 + (enemy_max_len - my_len) * 45)
                    food_dist = path_food
                # Do not let catch-up pressure drag us toward food a longer
                # opponent can reach first; use uncontested food unless starving.
                if health >= 30:
                    if safe_food < 99:
                        food_dist = safe_food
                    elif has_flipez_crystal_enemy:
                        food_dist = path_food
                        food_weight = max(food_weight, 140)
                    else:
                        food_weight = min(food_weight, 25)
            if has_battlejake_enemy and health >= 55 and my_len >= enemy_max_len + 7:
                food_weight = min(food_weight, 0)
            if has_cornelius_enemy and health >= 45 and my_len >= enemy_max_len + 6:
                food_weight = min(food_weight, 2)
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
                if has_battlejake_enemy and health >= 55 and my_len >= enemy_max_len + 7:
                    score -= 30000
                elif has_tantilla_enemy and health >= 55 and my_len >= enemy_max_len + 8:
                    score -= 25000
                elif has_gigantic_george_enemy and health >= 45 and my_len >= enemy_max_len + 5:
                    score -= 80000 if (my_len >= 35 and my_len >= enemy_max_len + 20) else 12000
                elif has_eremetic_enemy and health >= 45 and my_len >= enemy_max_len + 5:
                    score -= 12000
                elif has_cornelius_enemy and health >= 45 and my_len >= enemy_max_len + 6:
                    score -= 7000
                if has_famished_frank_enemy and health >= 45 and edge_dist == 0 and enemy_max_len >= my_len - 1:
                    # Healthy edge food next to Frank frequently grows us into a
                    # self-corridor while Frank keeps pathing around the outside.
                    # Still allow it when low health via the health guard above.
                    score -= 4500
                if health >= 30 and _food_contested_from(nxt, food_cells, enemy_heads, my_len, enemy_max_len):
                    score -= 1800
                else:
                    score += (2500 if health < 15 else (1200 if health < 30 else (260 if health < 60 else 120))) + (1400 if enemies and my_len <= enemy_max_len else 0) + (1800 if has_flipez_crystal_enemy and enemies and my_len <= enemy_max_len else 0)
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
