"""
Port of Petah's "project-z" Battlesnake (https://github.com/Petah/battle-snake-project-z)
Original: TypeScript/NodeJS. Botname: project-z. Author: Petah.

Strategy (faithful reproduction of ProjectZ snake state chain):
    states = [getFood, moveAway, smartRandomMove, randomMove]
  - getFood      -> moveTowardsFoodPf(blockHeads=True, attackHeads=True), pathfind to
                    the closest reachable food whose cell weight > 20 (A* over a weighted grid).
  - moveAway     -> move toward the board cell furthest (Manhattan) from any snake/border,
                    reachable via pathfinding.
  - smartRandomMove -> pick the free neighbour with the highest cell weight (ties random).
  - randomMove   -> any free neighbour (final fallback).

Weight model (lib/weight.ts) reproduced faithfully: snake bodies=0, dead-ends=1,
flood-fill space limits, attack-heads penalty (distance*10 within 3 of a >= length
enemy head), snake-body-adjacency (40 / tail 55), borders (35), capped at 50, hazards=5.

COORDINATES: The original used a top-left origin (its UP = y-1). This port works entirely
in the v1 bottom-left coordinate system and returns v1-correct direction strings; all
weight/flood-fill/pathfinding logic is coordinate-agnostic so fidelity is preserved.
"""

import random


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def grid_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def is_out_of_bounds(state, x, y):
    b = state["board"]
    return x < 0 or y < 0 or x >= b["width"] or y >= b["height"]


def is_free(state, x, y):
    """Cell is free if in-bounds and not occupied by any snake body part."""
    if is_out_of_bounds(state, x, y):
        return False
    for snake in state["board"]["snakes"]:
        for part in snake["body"]:
            if part["x"] == x and part["y"] == y:
                return False
    return True


def is_food(state, x, y):
    for food in state["board"]["food"]:
        if food["x"] == x and food["y"] == y:
            return True
    return False


# ---------------------------------------------------------------------------
# Flood fill (lib/weight.ts floodFill)
# ---------------------------------------------------------------------------

def flood_fill(state, cache, x, y):
    key = (x, y)
    if key in cache:
        return cache[key]
    count = 0
    nodes = [(x, y)]
    seen = {(x, y)}
    i = 0
    while i < len(nodes):
        nx, ny = nodes[i]
        i += 1
        if is_free(state, nx, ny):
            count += 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                np = (nx + dx, ny + dy)
                if np not in seen:
                    seen.add(np)
                    nodes.append(np)
    for np in nodes:
        cache[np] = count
    return count


# ---------------------------------------------------------------------------
# Weight model (lib/weight.ts)
# ---------------------------------------------------------------------------

BLOCKED_THRESHOLD = 10


def is_dead_end(state, x, y):
    return (not is_free(state, x - 1, y) and not is_free(state, x + 1, y)
            and not is_free(state, x, y - 1) and not is_free(state, x, y + 1))


def is_near_tail(state, x, y):
    for snake in state["board"]["snakes"]:
        body = snake["body"]
        part = body[-1]
        px, py = part["x"], part["y"]
        if (x == px and y == py):
            return True
        if (x + 1 == px and y == py):
            return True
        if (x - 1 == px and y == py):
            return True
        if (x == px and y + 1 == py):
            return True
        if (x == px and y - 1 == py):
            return True
    return False


def _is_squad(you, other):
    # Squad grouping only applies to same squad; in the arena there is none.
    if you["id"] == other["id"]:
        return False
    ys = you.get("squad")
    os_ = other.get("squad")
    if ys and ys == os_:
        return True
    return False


def weight(state, x, y, options, ff_cache):
    """Reproduces computeWeight from weight.ts."""
    # Hazards
    for hazard in state["board"].get("hazards") or []:
        if hazard["x"] == x and hazard["y"] == y:
            return 5

    you = state["you"]
    result = 100

    for snake in state["board"]["snakes"]:
        body = snake["body"]
        for p, part in enumerate(body):
            if part["x"] == x and part["y"] == y:
                # Is part of snake, and not the very end (tail is enterable)?
                if p != len(body) - 1:
                    # Head, and heads not blocking?
                    if p == 0 and not options.get("blockHeads"):
                        continue
                    if _is_squad(you, snake):
                        continue
                    # Stacked tail (early game): second-last == last -> body still growing
                    if (len(body) > 3 and p == len(body) - 2
                            and body[-1]["x"] == body[-2]["x"]
                            and body[-1]["y"] == body[-2]["y"]):
                        continue
                    return 0

    if options.get("avoidFood"):
        if is_food(state, x, y):
            result = min(result, 30)

    if options.get("deadEnds", True):
        if is_dead_end(state, x, y) and not is_near_tail(state, x, y):
            return 1
        fill_count = flood_fill(state, ff_cache, x, y)
        if fill_count < len(you["body"]):
            result = min(result, fill_count)

    if options.get("attackHeads"):
        for snake in state["board"]["snakes"]:
            body = snake["body"]
            for p, part in enumerate(body):
                if (snake["id"] != you["id"] and p == 0
                        and len(body) >= len(you["body"])):
                    distance = grid_distance(x, y, part["x"], part["y"])
                    if distance < 3:
                        result = min(result, distance * 10)

    if options.get("snakeBodies", True):
        for snake in state["board"]["snakes"]:
            body = snake["body"]
            for p, part in enumerate(body):
                tail_weight = 55 if p == len(body) - 1 else 40
                px, py = part["x"], part["y"]
                if x + 1 == px and y == py:
                    result = min(result, tail_weight)
                if x - 1 == px and y == py:
                    result = min(result, tail_weight)
                if x == px and y + 1 == py:
                    result = min(result, tail_weight)
                if x == px and y - 1 == py:
                    result = min(result, tail_weight)

    if options.get("borders", True):
        if x == 0:
            result = min(result, 35)
        if y == 0:
            result = min(result, 35)
        if x == state["board"]["width"] - 1:
            result = min(result, 35)
        if y == state["board"]["height"] - 1:
            result = min(result, 35)

    result = min(result, 50)
    return result


# ---------------------------------------------------------------------------
# Direction helper (v1 coordinate system: up=y+1, down=y-1)
# ---------------------------------------------------------------------------

def neighbor(x, y, direction):
    if direction == "up":
        return x, y + 1
    if direction == "down":
        return x, y - 1
    if direction == "left":
        return x - 1, y
    if direction == "right":
        return x + 1, y
    return x, y


def cell_to_direction(hx, hy, cx, cy):
    if cx == hx - 1 and cy == hy:
        return "left"
    if cx == hx + 1 and cy == hy:
        return "right"
    if cx == hx and cy == hy + 1:
        return "up"
    if cx == hx and cy == hy - 1:
        return "down"
    return None


# ---------------------------------------------------------------------------
# A* pathfinding (lib/Pather.ts). Grid blocked where weight <= BLOCKED_THRESHOLD,
# cost = 100 - weight. Returns first-step direction + path length.
# ---------------------------------------------------------------------------

def path_to(state, snake, tx, ty, options, ff_cache, weight_cache):
    b = state["board"]
    w, h = b["width"], b["height"]

    def cell_weight(x, y):
        key = (x, y)
        if key not in weight_cache:
            weight_cache[key] = weight(state, x, y, options, ff_cache)
        return weight_cache[key]

    sx, sy = snake["body"][0]["x"], snake["body"][0]["y"]

    if is_out_of_bounds(state, tx, ty):
        return None
    if cell_weight(tx, ty) <= BLOCKED_THRESHOLD and (tx, ty) != (sx, sy):
        return None

    import heapq
    start = (sx, sy)
    goal = (tx, ty)
    open_heap = [(grid_distance(sx, sy, tx, ty), 0, start)]
    g_score = {start: 0}
    came_from = {}
    closed = set()

    found = False
    while open_heap:
        _, g, cur = heapq.heappop(open_heap)
        if cur == goal:
            found = True
            break
        if cur in closed:
            continue
        closed.add(cur)
        cx, cy = cur
        for dx, dy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
            nx, ny = cx + dx, cy + dy
            if is_out_of_bounds(state, nx, ny):
                continue
            nw = cell_weight(nx, ny)
            if nw <= BLOCKED_THRESHOLD and (nx, ny) != goal:
                continue
            step_cost = 100 - nw
            if step_cost < 1:
                step_cost = 1
            ng = g + step_cost
            npos = (nx, ny)
            if npos in closed:
                continue
            if npos not in g_score or ng < g_score[npos]:
                g_score[npos] = ng
                came_from[npos] = cur
                f = ng + grid_distance(nx, ny, tx, ty)
                heapq.heappush(open_heap, (f, ng, npos))

    if not found:
        return None

    # Reconstruct path
    path = [goal]
    node = goal
    while node in came_from:
        node = came_from[node]
        path.append(node)
    path.reverse()

    if len(path) < 2:
        return None
    first = path[1]
    direction = cell_to_direction(sx, sy, first[0], first[1])
    if direction is None:
        return None
    return {"direction": direction, "distance": len(path)}


# ---------------------------------------------------------------------------
# State functions
# ---------------------------------------------------------------------------

def move_towards_food_pf(state, options, ff_cache, weight_cache):
    """lib/moveTowardsFoodPf.ts. No squads in arena => ignoreCloserSquads is a no-op."""
    food_list = state["board"]["food"]
    if not food_list:
        return None
    you = state["you"]
    sorted_food = []
    for food in food_list:
        path = path_to(state, you, food["x"], food["y"], options, ff_cache, weight_cache)
        if path:
            w = weight(state, food["x"], food["y"], options, ff_cache)
            sorted_food.append((path["distance"], path["direction"], w))
    sorted_food.sort(key=lambda e: e[0])
    for distance, direction, w in sorted_food:
        # isViable: has direction and weight > 20
        if direction and w > 20:
            return direction
    return None


def move_away(state, ff_cache, weight_cache):
    """lib/moveAway.ts. Move toward the cell furthest from any snake part / border."""
    b = state["board"]
    you = state["you"]
    w, h = b["width"], b["height"]
    options = {"blockHeads": True, "attackHeads": True}

    def closest_blocked(sx, sy):
        closest = 10000
        for snake in b["snakes"]:
            for part in snake["body"]:
                d = grid_distance(sx, sy, part["x"], part["y"])
                if d < closest:
                    closest = d
        for x in range(w):
            d = grid_distance(sx, sy, x, -1)
            if d < closest:
                closest = d
            d = grid_distance(sx, sy, x, h + 1)
            if d < closest:
                closest = d
        for y in range(h):
            d = grid_distance(sx, sy, -1, y)
            if d < closest:
                closest = d
            d = grid_distance(sx, sy, w + 1, y)
            if d < closest:
                closest = d
        return closest

    best_dist = None
    best_dir = None
    for y in range(h):
        for x in range(w):
            d = closest_blocked(x, y)
            if best_dist is None or d > best_dist:
                path = path_to(state, you, x, y, options, ff_cache, weight_cache)
                if path:
                    best_dist = d
                    best_dir = path["direction"]
    return best_dir


def smart_random_move(state, ff_cache, weight_cache):
    """lib/smartRandomMove.ts. Highest-weight free neighbour, ties broken randomly."""
    you = state["you"]
    hx, hy = you["body"][0]["x"], you["body"][0]["y"]
    options = {"blockHeads": True, "attackHeads": True}
    candidates = []
    for direction in ("left", "right", "up", "down"):
        nx, ny = neighbor(hx, hy, direction)
        if is_free(state, nx, ny):
            w = weight(state, nx, ny, options, ff_cache)
            candidates.append((direction, w))
    candidates = [c for c in candidates if c[1] > 0]
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[1], reverse=True)
    best = candidates[0][1]
    best_dirs = [c[0] for c in candidates if c[1] == best]
    random.shuffle(best_dirs)
    return best_dirs[0]


def random_move(state):
    """lib/randomMove.ts. Any free neighbour."""
    you = state["you"]
    hx, hy = you["body"][0]["x"], you["body"][0]["y"]
    directions = ["left", "right", "up", "down"]
    random.shuffle(directions)
    for direction in directions:
        nx, ny = neighbor(hx, hy, direction)
        if is_free(state, nx, ny):
            return direction
    # No free option; return last considered (kept for fidelity with original).
    return directions[-1]


# ---------------------------------------------------------------------------
# Safe fallback: never crash, never self-collide, tails enterable
# ---------------------------------------------------------------------------

def safe_fallback(state):
    you = state["you"]
    hx, hy = you["body"][0]["x"], you["body"][0]["y"]

    # Occupied cells; a tail cell is enterable unless the snake just ate
    # (i.e. tail stacked on the pre-tail cell).
    occupied = set()
    tails_enterable = set()
    for snake in state["board"]["snakes"]:
        body = snake["body"]
        for i, part in enumerate(body):
            occupied.add((part["x"], part["y"]))
        tail = body[-1]
        stacked = len(body) >= 2 and body[-1] == body[-2]
        if not stacked:
            tails_enterable.add((tail["x"], tail["y"]))

    for direction in ("up", "down", "left", "right"):
        nx, ny = neighbor(hx, hy, direction)
        if is_out_of_bounds(state, nx, ny):
            continue
        if (nx, ny) in occupied and (nx, ny) not in tails_enterable:
            continue
        return direction

    # As an absolute last resort, any in-bounds move.
    for direction in ("up", "down", "left", "right"):
        nx, ny = neighbor(hx, hy, direction)
        if not is_out_of_bounds(state, nx, ny):
            return direction
    return "up"


# ---------------------------------------------------------------------------
# Battlesnake v1 API
# ---------------------------------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "Petah",
        "color": "#e91e63",  # Color.PINK
        "head": "beluga",
        "tail": "block-bum",
    }


def start(game_state):
    return None


def move(game_state):
    try:
        state = game_state
        ff_cache = {}
        weight_cache = {}
        get_food_options = {"blockHeads": True, "attackHeads": True}

        # State chain (project-z.ts): getFood -> moveAway -> smartRandomMove -> randomMove
        direction = move_towards_food_pf(state, get_food_options, ff_cache, weight_cache)
        if not direction:
            direction = move_away(state, ff_cache, weight_cache)
        if not direction:
            direction = smart_random_move(state, ff_cache, weight_cache)
        if not direction:
            direction = random_move(state)

        # Validate the chosen move is legal (in-bounds, not into a non-tail body cell).
        if direction:
            you = state["you"]
            hx, hy = you["body"][0]["x"], you["body"][0]["y"]
            nx, ny = neighbor(hx, hy, direction)
            occupied = set()
            tails_enterable = set()
            for snake in state["board"]["snakes"]:
                body = snake["body"]
                for part in body:
                    occupied.add((part["x"], part["y"]))
                tail = body[-1]
                if not (len(body) >= 2 and body[-1] == body[-2]):
                    tails_enterable.add((tail["x"], tail["y"]))
            bad = is_out_of_bounds(state, nx, ny) or (
                (nx, ny) in occupied and (nx, ny) not in tails_enterable)
            if bad:
                direction = safe_fallback(state)
        else:
            direction = safe_fallback(state)

        if direction not in ("up", "down", "left", "right"):
            direction = safe_fallback(state)
        return {"move": direction}
    except Exception:
        try:
            return {"move": safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


def end(game_state):
    return None


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
