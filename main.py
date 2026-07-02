"""
Port of `eremetic_eric` from https://github.com/coreyja/battlesnake-rs
(battlesnake-rs/src/eremetic_eric.rs + a_prime.rs) to a self-contained
pure-stdlib Python BattleSnake (v1 API).

EremeticEric is a "coiling" snake: it chases its own tail (with a small food
penalty so it prefers routes that avoid food unless it needs to eat), and eats
food only when a loop calculation shows it must in order to survive another
lap.  A* pathfinding matches the wire `Game` implementation in a_prime.rs.

FIDELITY: approximate. The move-decision structure (loop/coil, food-cost
comparison, health-based "can't survive another loop" check, turn<3 food
seek, and the A* with food penalty toward the tail) is reproduced faithfully.
The exact "modified_board" tail-pushing (which extends the body along the
shortest path back to the tail before measuring the return distance) is
simplified: we push the tail along the computed path but still measure on the
resulting board, matching the intent.
"""

import heapq

# ---------------------------------------------------------------------------
# A* (mirrors a_prime.rs `impl APrimeCalculable for Game`)
# ---------------------------------------------------------------------------

NEIGHBOR_DISTANCE = 1
HEURISTIC_MAX = 500


def _dist_between(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _heuristic_wire(start, targets):
    if not targets:
        return None
    return min(_dist_between(t, start) for t in targets)


def _neighbors(pos, width, height):
    x, y = pos
    out = []
    if y + 1 < height:
        out.append((x, y + 1))
    if y - 1 >= 0:
        out.append((x, y - 1))
    if x - 1 >= 0:
        out.append((x - 1, y))
    if x + 1 < width:
        out.append((x + 1, y))
    return out


def _a_prime_inner(start, targets, board, food_penalty=1, hazard_penalty=1):
    """Returns (best_cost, paths_from, best_target) or None.

    board is a dict with: width, height, food (set), hazards (set),
    body (set of all snake body cells).
    """
    if not targets:
        return None

    targets_set = set(targets)
    width = board["width"]
    height = board["height"]
    food = board["food"]
    hazards = board["hazards"]
    snake_body = board["body"]

    to_search = []  # (cost, tie, coordinate)
    counter = 0
    heapq.heappush(to_search, (0, counter, start))
    known_score = {start: 0}
    paths_from = {start: None}

    while to_search:
        cost, _, coordinate = heapq.heappop(to_search)

        if coordinate in targets_set:
            return (cost, paths_from, coordinate)

        if coordinate in hazards:
            neighbor_distance = hazard_penalty + NEIGHBOR_DISTANCE
        elif coordinate in food:
            neighbor_distance = NEIGHBOR_DISTANCE + food_penalty
        else:
            neighbor_distance = NEIGHBOR_DISTANCE

        tentative = known_score.get(coordinate, 2 ** 31) + neighbor_distance

        for neighbor in _neighbors(coordinate, width, height):
            # matches wire Game filter: neighbor allowed if it is a target OR
            # is not occupied by any snake body.
            if not (neighbor in targets_set or neighbor not in snake_body):
                continue
            if tentative < known_score.get(neighbor, 2 ** 31):
                known_score[neighbor] = tentative
                paths_from[neighbor] = coordinate
                h = _heuristic_wire(neighbor, targets)
                if h is None:
                    h = HEURISTIC_MAX
                counter += 1
                heapq.heappush(to_search, (tentative + h, counter, neighbor))

    return None


def _shortest_distance(start, targets, board, food_penalty=1, hazard_penalty=1):
    r = _a_prime_inner(start, targets, board, food_penalty, hazard_penalty)
    return r[0] if r is not None else None


def _shortest_path(start, targets, board, food_penalty=1, hazard_penalty=1):
    r = _a_prime_inner(start, targets, board, food_penalty, hazard_penalty)
    if r is None:
        return []
    _, paths_from, best_target = r
    path = []
    current = best_target
    while current is not None:
        path.append(current)
        current = paths_from.get(current)
    path.reverse()
    return path


def _shortest_path_next_direction(start, targets, board, food_penalty=1,
                                  hazard_penalty=1):
    path = _shortest_path(start, targets, board, food_penalty, hazard_penalty)
    if len(path) < 2:
        return None
    nxt = path[1]
    return _dir_from_delta(start, nxt)


def _dir_from_delta(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    if dx == 1:
        return "right"
    if dx == -1:
        return "left"
    if dy == 1:
        return "up"
    if dy == -1:
        return "down"
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pt(d):
    return (d["x"], d["y"])


def _make_board(game_state, body_override=None):
    b = game_state["board"]
    food = set(_pt(f) for f in b.get("food", []))
    hazards = set(_pt(h) for h in b.get("hazards", []))
    body = set()
    for s in b.get("snakes", []):
        for c in s.get("body", []):
            body.add(_pt(c))
    if body_override is not None:
        body |= set(body_override)
    return {
        "width": b["width"],
        "height": b["height"],
        "food": food,
        "hazards": hazards,
        "body": body,
    }


def _safe_fallback(game_state):
    """Any in-bounds move not into a snake body (tails are enterable)."""
    b = game_state["board"]
    width = b["width"]
    height = b["height"]
    you = game_state["you"]
    head = _pt(you["head"])

    blocked = set()
    for s in b.get("snakes", []):
        body = s.get("body", [])
        # tail is enterable unless the snake just ate (health 100) - keep simple:
        # treat all but the last cell as blocked.
        for c in body[:-1]:
            blocked.add(_pt(c))

    for d in ("up", "down", "left", "right"):
        nxt = _apply_dir(head, d)
        x, y = nxt
        if 0 <= x < width and 0 <= y < height and nxt not in blocked:
            return d
    return "up"


def _apply_dir(pos, d):
    x, y = pos
    if d == "up":
        return (x, y + 1)
    if d == "down":
        return (x, y - 1)
    if d == "left":
        return (x - 1, y)
    if d == "right":
        return (x + 1, y)
    return pos


# ---------------------------------------------------------------------------
# Core move logic (mirrors eremetic_eric.rs make_move)
# ---------------------------------------------------------------------------

def _make_move(game_state):
    you = game_state["you"]
    body = [_pt(c) for c in you["body"]]
    head = body[0]
    tail = body[-1]
    health = you["health"]

    base_board = _make_board(game_state)

    all_food = list(base_board["food"])
    if not all_food:
        # Nothing to eat: chase own tail (with food penalty), coil behavior.
        d = _shortest_path_next_direction(head, [tail], base_board,
                                          food_penalty=1)
        return d if d is not None else _safe_fallback(game_state)

    # Build modified board: push tail along shortest path back to own tail,
    # completing a circle.  (a_prime path_to_complete_circle then reversed.)
    path_to_complete_circle = _shortest_path(head, [tail], base_board)
    path_to_complete_circle.reverse()
    body_set = set(body)
    pushed = list(body)
    for c in path_to_complete_circle:
        if c not in body_set:
            pushed.append(c)
            body_set.add(c)
    modified_board = _make_board(game_state, body_override=set(pushed))

    # For each food, find closest body part and its distance.
    food_options = []  # (food, (closest_body_part, best_cost))
    for food in all_food:
        body_options = [(bp, _dist_between(food, bp)) for bp in body]
        best = min(body_options, key=lambda x: x[1])
        best_c = best[1]
        for (bp, cost) in body_options:
            if cost == best_c:
                food_options.append((food, (bp, best_c)))

    # overall best cost across all food options
    best_cost = min(fo[1][1] for fo in food_options)

    matching_cost_foods = [fo for fo in food_options if fo[1][1] == best_cost]

    cost_to_loop = len(body)

    matching_food_options = []  # ((food,(bp,best_cost)),(health_cost,food))
    for (food, (closest_body_part, _bc)) in matching_cost_foods:
        closest_index = body.index(closest_body_part)
        tail_index = len(body) - 1 if closest_index == 0 else closest_index - 1
        would_be_tail = body[tail_index]

        dist_back = _shortest_distance(food, [would_be_tail], modified_board)
        if dist_back is None:
            dist_back = 5000

        cost_to_get_to_closest = 0 if closest_index == 0 \
            else (cost_to_loop - closest_index)
        best_cost_u = best_cost
        cost_to_get_to_nearest_food = cost_to_get_to_closest + best_cost_u
        cost_food_and_back = best_cost_u + dist_back

        if health >= cost_to_get_to_nearest_food:
            health_when_at_closest = health - cost_to_get_to_closest
            health_cost = health_when_at_closest + cost_food_and_back
        else:
            health_cost = 6666

        matching_food_options.append(
            ((food, (closest_body_part, best_cost)),
             (health_cost, food)))

    # sort by (health_cost, food) - food tie-break by coordinate tuple
    matching_food_options.sort(key=lambda item: (item[1][0], item[1][1]))

    best_food, (best_closest_body_part, best_cost2) = \
        matching_food_options[0][0]

    cant_survive_another_loop = health < (cost_to_loop + best_cost2)

    # If head is at the closest body part and can't survive another loop -> eat.
    if head == best_closest_body_part and cant_survive_another_loop:
        d = _shortest_path_next_direction(head, [best_food], base_board)
        if d is not None:
            return d

    # Early game: head straight for nearest food.
    if game_state["turn"] < 3:
        d = _shortest_path_next_direction(head, all_food, base_board)
        if d is not None:
            return d

    # Default: coil - chase own tail with a food penalty.
    d = _shortest_path_next_direction(
        head, [tail], base_board,
        food_penalty=1)
    if d is not None:
        return d

    return _safe_fallback(game_state)


# ---------------------------------------------------------------------------
# BattleSnake v1 API
# ---------------------------------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#FF4444",
        "head": "trans-rights-scarf",
        "tail": "default",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def move(game_state):
    try:
        d = _make_move(game_state)
        if d not in ("up", "down", "left", "right"):
            d = _safe_fallback(game_state)
        return {"move": d}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
