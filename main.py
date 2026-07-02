"""Port of Xe's "since" Battlesnake bot (Nim) to a self-contained Python main.py.

Reproduces the production move logic in src/since.nim + src/sincePkg/pathing.nim +
src/sincePkg/base(battlesnake).nim. The bot picks a target (food / hunt / tail /
random) then A*-paths to it using a cost map that penalises snake bodies and the
tiles enemies might move into, and emits the first step of that path.

Coordinate remap: the original Nim code assumes a top-left origin with y growing
downward (its `->` maps l.y>r.y to "up"). The current Battlesnake v1 API uses a
bottom-left origin with y growing upward. Only the y direction mapping differs, so
the direction helper is flipped accordingly; all other geometry is orientation
independent.
"""

import heapq
import random

# Cost constants (from pathing.nim).
GOOD = 1
ENEMY_THERE = 999
SELF_THERE = 9999
POTENTIAL_ENEMY_MOVEMENT = 50
DANGEROUS_PLACE = 100


# ---------------------------------------------------------------------------
# Coordinate helpers (battlesnake.nim / base.nim)
# ---------------------------------------------------------------------------

def _cp(x, y):
    return (x, y)


def _direction(l, r):
    """`->` from battlesnake.nim, remapped to v1 (y-up) coords.

    Nim (y-down): l.y > r.y -> up, l.y < r.y -> down.
    v1 (y-up):    moving up is y+1, so r.y > l.y -> up.
    """
    lx, ly = l
    rx, ry = r
    if lx < rx:
        return "right"
    if lx > rx:
        return "left"
    if ry > ly:
        return "up"
    if ry < ly:
        return "down"
    return None


def _in_bounds(state, p):
    x, y = p
    return 0 <= x < state["width"] and 0 <= y < state["height"]


def _is_deadly(board_snakes, p):
    """Faithful port of base.nim isDeadly.

    NOTE: the original Nim has a well-known bug: the inner loop `return false`
    lives inside the first iteration, so it only ever inspects the *first*
    segment of the *first* snake before returning. We reproduce that behaviour
    exactly so pathing/targeting decisions match the original bot.
    """
    for enemy in board_snakes:
        for seg in enemy["body"]:
            if seg == p:
                return True
            return False
    return False


def _all_neighbors(state, p):
    x, y = p
    for n in (_cp(x - 1, y), _cp(x + 1, y), _cp(x, y - 1), _cp(x, y + 1)):
        if _in_bounds(state, n):
            yield n


def _neighbors_safe(state, p):
    """pathing.nim neighbors: in-bounds and not isDeadly."""
    for n in _all_neighbors(state, p):
        if not _is_deadly(state["snakes"], n):
            yield n


def _is_dangerous(state, p):
    """base.nim isDangerous: any neighbor of p is an enemy head."""
    for loc in _all_neighbors(state, p):
        for sn in state["snakes"]:
            if loc == sn["head"]:
                return True
    return False


def _is_edge(state, p):
    x, y = p
    return x == 0 or y == 0 or x == state["width"] - 1 or y == state["height"] - 1


def _manhattan(a, b):
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))


# ---------------------------------------------------------------------------
# A* (astar module analogue) with pathing.nim cost + heuristic
# ---------------------------------------------------------------------------

def _cost(state, b):
    """pathing.nim cost(st, a, b): cost of entering tile b (a is unused there)."""
    result = 0.0
    snakes = state["snakes"]
    for s in snakes:
        for cp in s["body"]:
            if b == cp:
                result += ENEMY_THERE
                if s["id"] == state["you_id"]:
                    result += SELF_THERE
            for ne in _neighbors_safe(state, cp):
                if b == ne:
                    result += POTENTIAL_ENEMY_MOVEMENT
                for ne2 in _neighbors_safe(state, ne):
                    if b == ne2:
                        result += POTENTIAL_ENEMY_MOVEMENT
    result += GOOD
    return result


def _astar(state, source, target):
    """A* over safe neighbors, returning path incl. source and target, or []."""
    if source == target:
        return [source]
    open_heap = [(0.0, source)]
    came_from = {}
    g_score = {source: 0.0}
    closed = set()
    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == target:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        if current in closed:
            continue
        closed.add(current)
        for nb in _neighbors_safe(state, current):
            if nb in closed:
                continue
            tentative = g_score[current] + _cost(state, nb)
            if nb not in g_score or tentative < g_score[nb]:
                came_from[nb] = current
                g_score[nb] = tentative
                f = tentative + _manhattan(nb, target)
                heapq.heappush(open_heap, (f, nb))
    return []


# ---------------------------------------------------------------------------
# Target selection (pathing.nim)
# ---------------------------------------------------------------------------

def _find_food(state):
    foods = []
    head = state["you_head"]
    for cp in state["food"]:
        foods.append((_manhattan(head, cp), cp))
    lowest = 999999.9999
    result = None
    for cost, point in foods:
        if cost < lowest:
            lowest = cost
            result = point
    return result


def _random_safe_tile(state):
    for _ in range(1000):
        result = _cp(random.randint(0, state["width"]), random.randint(0, state["height"]))
        if not _in_bounds(state, result):
            continue
        if not _is_deadly(state["snakes"], result) and not _is_edge(state, result):
            return result
    # deterministic fallback: any in-bounds non-deadly tile
    for x in range(state["width"]):
        for y in range(state["height"]):
            p = _cp(x, y)
            if not _is_deadly(state["snakes"], p):
                return p
    return state["you_head"]


def _find_safe_neighbor(state, p):
    for ne in _neighbors_safe(state, p):
        return ne
    return None


def _find_tail(state):
    return _find_safe_neighbor(state, state["you_tail"])


def _find_target(state):
    """pathing.nim findTarget -> (cp, desc, victim)."""
    cp = _cp(-1, -1)
    desc = "invalid"
    victim = ""

    total_len = 0
    biggest_len = 0
    snakes = state["snakes"]
    for snake in snakes:
        total_len += len(snake["body"])
        if len(snake["body"]) > biggest_len:
            biggest_len = len(snake["body"])
    avg_len = total_len / len(snakes) if snakes else 0.0

    you_len = len(state["you_body"])

    def do_food():
        return (_find_food(state), "food", "")

    def do_hunt():
        r = (cp, desc, victim)
        for snake in snakes:
            if len(snake["body"]) < you_len:
                r = (_find_safe_neighbor(state, snake["head"]), "hunting", snake["id"])
        return r

    def do_random():
        return (_random_safe_tile(state), "random", "")

    def do_tail():
        return (_find_tail(state), "tail", "")

    if len(state["food"]) >= 1:
        if you_len < biggest_len or state["you_health"] <= 30:
            cp, desc, victim = do_food()
        if state["turn"] == 0:
            cp, desc, victim = do_food()
    elif float(you_len) > avg_len:
        cp, desc, victim = do_hunt()
    elif len(snakes) == 2 and you_len == biggest_len:
        cp, desc, victim = do_hunt()
    else:
        cp, desc, victim = do_tail()

    if cp is not None and _is_deadly(snakes, cp):
        cp, desc, victim = do_random()

    if desc == "invalid":
        if random.randint(0, 2) == 1:
            cp, desc, victim = do_tail()
        else:
            cp, desc, victim = do_food()

    if cp is None:
        cp, desc, victim = do_random()

    return (cp, desc, victim)


def _find_path(state, source, target):
    if target is None:
        return []
    result = _astar(state, source, target)
    if len(result) >= 2 and _is_deadly(state["snakes"], result[1]):
        return _astar(state, source, _random_safe_tile(state))
    return result


# ---------------------------------------------------------------------------
# State normalisation + move flow (since.nim /move handler)
# ---------------------------------------------------------------------------

def _norm(game_state):
    board = game_state["board"]
    you = game_state["you"]

    def pt(d):
        return _cp(d["x"], d["y"])

    snakes = []
    for sn in board.get("snakes", []):
        body = [pt(s) for s in sn.get("body", [])]
        head = pt(sn["head"]) if "head" in sn and sn["head"] else (body[0] if body else None)
        snakes.append({
            "id": sn.get("id", ""),
            "name": sn.get("name", ""),
            "health": sn.get("health", 0),
            "body": body,
            "head": head,
        })

    you_body = [pt(s) for s in you.get("body", [])]
    you_head = pt(you["head"]) if you.get("head") else you_body[0]

    return {
        "turn": game_state.get("turn", 0),
        "width": board.get("width", 11),
        "height": board.get("height", 11),
        "food": [pt(f) for f in board.get("food", [])],
        "snakes": snakes,
        "you_id": you.get("id", ""),
        "you_head": you_head,
        "you_tail": you_body[-1] if you_body else you_head,
        "you_body": you_body,
        "you_health": you.get("health", 0),
    }


def _safe_fallback_move(state):
    """Robustness net: return an in-bounds move that avoids all snake bodies
    (tails allowed) if one exists, else any in-bounds move, else 'up'."""
    head = state["you_head"]
    occupied = set()
    tails = set()
    for sn in state["snakes"]:
        body = sn["body"]
        for i, seg in enumerate(body):
            # A tail is enterable unless the snake just ate (tail overlaps body).
            if i == len(body) - 1 and body.count(seg) == 1:
                tails.add(seg)
            else:
                occupied.add(seg)
    hx, hy = head
    candidates = [
        ("up", _cp(hx, hy + 1)),
        ("down", _cp(hx, hy - 1)),
        ("left", _cp(hx - 1, hy)),
        ("right", _cp(hx + 1, hy)),
    ]
    in_bounds = [(m, p) for m, p in candidates if _in_bounds(state, p)]
    best = [m for m, p in in_bounds if p not in occupied]
    if best:
        return random.choice(best)
    if in_bounds:
        return random.choice([m for m, _ in in_bounds])
    return "up"


def move(game_state):
    try:
        state = _norm(game_state)
        source = state["you_head"]

        # Stateless reimplementation: since.nim persisted target state in redis
        # across turns; here we recompute the target every turn (equivalent to
        # the turn==0 branch each time).
        target, desc, victim = _find_target(state)

        if desc == "tail":
            target = state["you_tail"]
        elif desc == "hunting":
            found = False
            for sn in state["snakes"]:
                if sn["id"] == victim:
                    target = sn["head"]
                    found = True
                    break
            if not found:
                target, desc, victim = _find_target(state)

        if source == target or (target is not None and _is_deadly(state["snakes"], target)):
            target, desc, victim = _find_target(state)

        my_path = _find_path(state, source, target)
        attempts = 0
        while len(my_path) == 0 and attempts < 50:
            target = _random_safe_tile(state)
            my_path = _find_path(state, source, target)
            attempts += 1

        if len(my_path) >= 2:
            my_move = _direction(source, my_path[1])
            if my_move is None:
                my_move = _safe_fallback_move(state)
        else:
            my_move = _safe_fallback_move(state)

        # Final safety guard: never step into a body / out of bounds if avoidable.
        hx, hy = source
        dest = {
            "up": _cp(hx, hy + 1),
            "down": _cp(hx, hy - 1),
            "left": _cp(hx - 1, hy),
            "right": _cp(hx + 1, hy),
        }.get(my_move)
        if dest is None or not _in_bounds(state, dest):
            my_move = _safe_fallback_move(state)
        else:
            occupied = set()
            tails = set()
            for sn in state["snakes"]:
                body = sn["body"]
                for i, seg in enumerate(body):
                    if i == len(body) - 1 and body.count(seg) == 1:
                        tails.add(seg)
                    else:
                        occupied.add(seg)
            if dest in occupied:
                my_move = _safe_fallback_move(state)

        return {"move": my_move}
    except Exception:
        try:
            return {"move": _safe_fallback_move(_norm(game_state))}
        except Exception:
            return {"move": random.choice(["up", "left", "right", "down"])}


# ---------------------------------------------------------------------------
# Battlesnake v1 API surface
# ---------------------------------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "Xe",
        "color": "#FFD600",   # snakeColor from since.nim /start
        "head": "beluga",     # headType from since.nim /start
        "tail": "skinny",     # tailType from since.nim /start
    }


def start(game_state):
    return None


def end(game_state):
    return None


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
