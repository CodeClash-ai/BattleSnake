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

def _nearest_food_distance(pos, food):
    if not food:
        return 99
    return min(_manhattan(pos, f) for f in food)


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
        for e in enemies:
            eh = _pt(e["head"] if "head" in e else e["body"][0])
            elen = e.get("length", len(e.get("body", [])))
            preds = {_simple_opponent_target_move(eh, food, w, h)}
            straight = _continuation_or_default_move(e, w, h)
            if straight is not None and _in_bounds(straight, w, h):
                preds.add(straight)
            if "Nettogrof" in e.get("name", ""):
                pred = _nettogrof_serpentine_move(e, food, w, h, occupied)
                if pred is not None:
                    preds.add(pred)
            for pred in preds:
                enemy_next_pred.append((pred, elen))

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
            for e in enemies:
                eh = _pt(e["head"] if "head" in e else e["body"][0])
                elen = e.get("length", len(e.get("body", [])))
                if _manhattan(nxt, eh) == 1 and elen >= my_len:
                    h2h_risk = True
                    break

            # For space evaluation, pretend our new head becomes blocked and
            # all moving tails are free.
            future_blocked = set(occupied)
            future_blocked.add(nxt)
            area = _flood_count(nxt, w, h, future_blocked, limit=w * h)
            territory = _territory_count(nxt, enemy_heads, w, h, future_blocked, my_len, enemy_max_len)
            nearest_food = _nearest_food_distance(nxt, food)
            center_dist = _manhattan(nxt, ((w - 1) // 2, (h - 1) // 2))
            edge_dist = min(nxt[0], nxt[1], w - 1 - nxt[0], h - 1 - nxt[1])

            score = 0
            score += area * 100                 # never trap ourselves
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
            score += edge_dist * 8              # prefer room away from walls
            score -= center_dist * 2            # stay roughly central
            score -= nearest_food * (20 if health < 50 else 16)
            if nxt in food_cells:
                score += 60 if health < 60 else 15
            if h2h_risk:
                score -= 10000
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
                        score -= 5000
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
