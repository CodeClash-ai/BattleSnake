"""
Robosnake (Redbrick's Robosnake Mk. III) ported to the Battlesnake v1 API.

Original: https://github.com/smallsco/robosnake (Lua, targeting the 2019 API).
Author of original strategy: smallsco (Scott Small) / Redbrick Technologies.

FIDELITY: faithful. This reimplements the original's core strategy:
  - alpha-beta minimax against a single chosen "enemy" snake
  - the same board heuristic (health/trap floodfill, food weighting,
    aggression toward the enemy head, tunnel avoidance, edge avoidance,
    percent-accessible score scaling)
  - the same enemy-selection logic (closest, then shortest, then arbitrary)
  - the same failsafe (floodfill neighbours, pick max free space)
Simplifications for the arena / speed budget:
  - MAX_RECURSION_DEPTH reduced from 6 to 4 with a ~0.30s wall-clock guard
  - internal grid kept in the v1 coordinate system (0,0 bottom-left); the
    grid/floodfill math is orientation-independent, only the final
    direction mapping differs from the Lua original's 2019 convention.
"""

import time

# --- Config (from config/server.prod.conf, depth reduced for speed) ---------
MAX_AGGRESSION_SNAKES = 4
MAX_RECURSION_DEPTH = 4
HUNGER_HEALTH = 40
LOW_FOOD = 8
TIME_LIMIT = 0.30  # wall-clock guard in seconds

INF = float("inf")

# Grid tile values (matching the Lua original):
#   '.' empty, 'O' food, '@' head, '#' body, '*' tail (enterable), '?' blocked
_SAFE = (".", "O", "*")


class _Timeout(Exception):
    pass


def _mdist(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def _is_safe(v, failsafe=False):
    return True if failsafe else v in _SAFE


def _build_grid(width, height, food, snakes):
    grid = [["." for _ in range(width)] for _ in range(height)]
    for f in food:
        grid[f["y"]][f["x"]] = "O"
    for snake in snakes:
        body = snake["body"]
        n = len(body)
        for j, seg in enumerate(body):
            y, x = seg["y"], seg["x"]
            if j == 0:
                grid[y][x] = "@"
            elif j == n - 1:
                if grid[y][x] not in ("@", "#"):
                    grid[y][x] = "*"
            else:
                if grid[y][x] != "@":
                    grid[y][x] = "#"
    return grid


def _neighbours(pos, grid, failsafe=False):
    height = len(grid)
    width = len(grid[0])
    x, y = pos["x"], pos["y"]
    result = []
    for nx, ny in ((x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)):
        if 0 <= nx < width and 0 <= ny < height and _is_safe(grid[ny][nx], failsafe):
            result.append({"x": nx, "y": ny})
    return result


def _floodfill(pos, grid, num_safe, depth):
    # Stack-based to avoid deep recursion; matches capped-depth semantics.
    stack = [pos]
    while stack:
        if num_safe >= depth:
            break
        p = stack.pop()
        x, y = p["x"], p["y"]
        if grid[y][x] in _SAFE:
            grid[y][x] = 1
            num_safe += 1
            for n in _neighbours(p, grid):
                stack.append(n)
    return num_safe


def _copy_grid(grid):
    return [row[:] for row in grid]


def _copy_state(state):
    def cp_snake(s):
        return {
            "id": s["id"],
            "health": s["health"],
            "body": [{"x": b["x"], "y": b["y"]} for b in s["body"]],
        }
    return {
        "me": cp_snake(state["me"]),
        "enemy": cp_snake(state["enemy"]),
        "snakes": [cp_snake(s) for s in state["snakes"]],
    }


def _direction(src, dst):
    """v1 API: up=y+1, down=y-1, left=x-1, right=x+1 (0,0 bottom-left)."""
    if dst["x"] == src["x"] + 1 and dst["y"] == src["y"]:
        return "right"
    if dst["x"] == src["x"] - 1 and dst["y"] == src["y"]:
        return "left"
    if dst["x"] == src["x"] and dst["y"] == src["y"] + 1:
        return "up"
    if dst["x"] == src["x"] and dst["y"] == src["y"] - 1:
        return "down"
    return None


def _heuristic(grid, state, my_moves, enemy_moves):
    score = 0
    me = state["me"]
    enemy = state["enemy"]
    mb = me["body"]
    eb = enemy["body"]
    height = len(grid)
    width = len(grid[0])
    total = height * width

    # Head-on-head collisions.
    if mb[0]["x"] == eb[0]["x"] and mb[0]["y"] == eb[0]["y"]:
        if len(mb) > len(eb):
            score += 2147483647
        elif len(mb) < len(eb):
            score -= 2147483648
        else:
            score -= 2147483647

    # My win/loss conditions
    if len(my_moves) == 0:
        score -= 2147483648
    if me["health"] <= 0:
        score -= 2147483648

    # collect food from grid
    food = []
    for y in range(height):
        for x in range(width):
            if grid[y][x] == "O":
                food.append({"x": x, "y": y})

    # My floodfill
    ff = _copy_grid(grid)
    ff[mb[0]["y"]][mb[0]["x"]] = "."
    ff_depth = (2 * len(mb)) + len(food)
    accessible = _floodfill(mb[0], ff, 0, ff_depth)
    if len(mb) > 1 and mb[-1]["x"] == mb[-2]["x"] and mb[-1]["y"] == mb[-2]["y"]:
        accessible += 1
    percent = accessible / total if total else 0
    if accessible <= len(mb):
        score -= 9999999 * (1 / percent) if percent else 9999999 * 1e9

    # Enemy win/loss conditions
    if len(enemy_moves) == 0:
        score += 2147483647
    if enemy["health"] <= 0:
        score += 2147483647

    # Enemy floodfill
    eff = _copy_grid(grid)
    eff[eb[0]["y"]][eb[0]["x"]] = "."
    eff_depth = (2 * len(eb)) + len(food)
    enemy_accessible = _floodfill(eb[0], eff, 0, eff_depth)
    if len(eb) > 1 and eb[-1]["x"] == eb[-2]["x"] and eb[-1]["y"] == eb[-2]["y"]:
        enemy_accessible += 1
    if enemy_accessible <= len(eb):
        score += 9999999

    # Aggression / hunger weighting
    food_weight = 0
    aggressive_weight = 100
    if len(food) <= LOW_FOOD:
        aggressive_weight = me["health"]
        food_weight = 200 - (2 * me["health"])
    else:
        if me["health"] <= HUNGER_HEALTH or len(mb) < 4:
            food_weight = 100 - me["health"]
    if len(state["snakes"]) > MAX_AGGRESSION_SNAKES:
        food_weight = 1
        aggressive_weight = 0

    if food_weight > 0:
        for i, f in enumerate(food, start=1):
            dist = _mdist(mb[0], f)
            score -= (dist * food_weight) - i

    # Hang out near the enemy's head
    kill_squares = _neighbours(eb[0], grid)
    enemy_last_direction = None
    if len(eb) > 1:
        enemy_last_direction = _direction(eb[1], eb[0])
    for ks in kill_squares:
        dist = _mdist(mb[0], ks)
        direction = _direction(eb[0], ks)
        if direction is not None and direction == enemy_last_direction:
            score -= dist * (2 * aggressive_weight)
        else:
            score -= dist * aggressive_weight

    # Avoid possible tunnels (me), try to put enemy in tunnels
    if len(_neighbours(mb[0], grid)) == 1:
        score -= 50000
    if len(_neighbours(eb[0], grid)) == 1:
        score += 50000

    # Avoid the edge of the game board (v1: edges are 0 and width-1/height-1)
    if mb[0]["x"] == 0 or mb[0]["x"] == width - 1 or mb[0]["y"] == 0 or mb[0]["y"] == height - 1:
        score -= 25000

    # Scale by percent accessible
    if score < 0:
        score = score * ((1 / percent) if percent else 1e9)
    elif score > 0:
        score = score * percent

    return score


def _advance_snake(new_grid, prev_grid, body, health, move):
    """Applies one snake's move to new_grid + body/health; mirrors Lua logic."""
    eating = False
    if prev_grid[move["y"]][move["x"]] == "O":
        eating = True
        health = 100
    else:
        health -= 1

    length = len(body)
    # remove tail from grid only if not growing (duplicated tail)
    if length > 1 and body[-1]["x"] == body[-2]["x"] and body[-1]["y"] == body[-2]["y"]:
        pass
    else:
        new_grid[body[-1]["y"]][body[-1]["x"]] = "."

    # always remove tail from state
    tail = body.pop()

    # move head on grid + state
    if length > 1:
        new_grid[body[0]["y"]][body[0]["x"]] = "#"
    body.insert(0, {"x": move["x"], "y": move["y"]})
    new_grid[move["y"]][move["x"]] = "@"

    if eating:
        body.append({"x": tail["x"], "y": tail["y"]})

    # mark tail as safe/unsafe
    length = len(body)
    if length > 1 and body[-1]["x"] == body[-2]["x"] and body[-1]["y"] == body[-2]["y"]:
        new_grid[body[-1]["y"]][body[-1]["x"]] = "#"
    else:
        new_grid[body[-1]["y"]][body[-1]["x"]] = "*"

    return health


def _alphabeta(grid, state, depth, alpha, beta, alpha_move, beta_move,
               maximizing, prev_grid, prev_enemy_moves, deadline):
    if time.monotonic() > deadline:
        raise _Timeout()

    me = state["me"]
    enemy = state["enemy"]
    my_moves = _neighbours(me["body"][0], grid)
    if maximizing:
        enemy_moves = _neighbours(enemy["body"][0], grid)
    else:
        enemy_moves = prev_enemy_moves

    moves = my_moves if maximizing else enemy_moves

    if (
        depth == MAX_RECURSION_DEPTH
        or len(moves) == 0
        or me["health"] <= 0
        or enemy["health"] <= 0
        or (me["body"][0]["x"] == enemy["body"][0]["x"]
            and me["body"][0]["y"] == enemy["body"][0]["y"])
    ):
        return (_heuristic(grid, state, my_moves, enemy_moves),
                alpha_move if maximizing else beta_move)

    # Remove tails of all snakes other than me and enemy from the grid.
    for s in state["snakes"]:
        if s["id"] != me["id"] and s["id"] != enemy["id"]:
            body = s["body"]
            length = len(body)
            if length > 1 and body[-1]["x"] == body[-2]["x"] and body[-1]["y"] == body[-2]["y"]:
                grid[body[-1]["y"]][body[-1]["x"]] = "*"
                body.pop()
            elif length == 1:
                grid[body[-1]["y"]][body[-1]["x"]] = "."
                body.pop()
            elif length > 1:
                grid[body[-1]["y"]][body[-1]["x"]] = "."
                grid[body[-2]["y"]][body[-2]["x"]] = "*"
                body.pop()

    if maximizing:
        for mv in moves:
            new_grid = _copy_grid(grid)
            new_state = _copy_state(state)
            new_state["me"]["health"] = _advance_snake(
                new_grid, new_grid, new_state["me"]["body"],
                new_state["me"]["health"], mv)
            new_alpha, _ = _alphabeta(
                new_grid, new_state, depth + 1, alpha, beta,
                alpha_move, beta_move, False, grid, enemy_moves, deadline)
            if new_alpha > alpha:
                alpha = new_alpha
                alpha_move = mv
            if beta <= alpha:
                break
        return alpha, alpha_move
    else:
        for mv in moves:
            new_grid = _copy_grid(grid)
            new_state = _copy_state(state)
            new_state["enemy"]["health"] = _advance_snake(
                new_grid, prev_grid, new_state["enemy"]["body"],
                new_state["enemy"]["health"], mv)
            new_beta, _ = _alphabeta(
                new_grid, new_state, depth + 1, alpha, beta,
                alpha_move, beta_move, True, None, None, deadline)
            if new_beta < beta:
                beta = new_beta
                beta_move = mv
            if beta <= alpha:
                break
        return beta, beta_move


def _failsafe(me, snakes, grid, food_count):
    my_moves = _neighbours(me["body"][0], grid)
    safe_moves = list(my_moves)

    for s in snakes:
        if s["id"] != me["id"] and len(s["body"]) >= len(me["body"]):
            enemy_moves = _neighbours(s["body"][0], grid)
            safe_moves = [m for m in safe_moves
                          if not any(m["x"] == e["x"] and m["y"] == e["y"] for e in enemy_moves)]

    depth = (2 * len(me["body"])) + food_count

    def pick(candidates):
        best = candidates[0]
        most = 0
        for c in candidates:
            g = _copy_grid(grid)
            acc = _floodfill(c, g, 0, depth)
            if acc > most:
                best = c
                most = acc
        return best

    if safe_moves:
        return pick(safe_moves)
    if my_moves:
        return pick(my_moves)
    return None


def _choose_enemy(me, snakes):
    possible = []
    shortest = 99999
    for s in snakes:
        if s["id"] == me["id"]:
            continue
        d = _mdist(me["body"][0], s["body"][0])
        if d == shortest:
            possible.append(s)
        elif d < shortest:
            shortest = d
            possible = [s]

    if len(possible) > 1:
        if _mdist(me["body"][0], possible[0]["body"][0]) >= 4:
            return possible[0]
        shortest_len = 99999
        reduced = []
        for p in possible:
            if len(p["body"]) == shortest_len:
                reduced.append(p)
            elif len(p["body"]) < shortest_len:
                shortest_len = len(p["body"])
                reduced = [p]
        return reduced[0]
    elif len(possible) == 1:
        return possible[0]
    return me  # only snake in game -> predict self


def info():
    return {
        "apiversion": "1",
        "author": "smallsco",
        "color": "#5D6D7E",
        "head": "bendr",
        "tail": "fat-rattle",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _safe_fallback(game_state):
    """Guaranteed in-bounds, non-body move (tails allowed)."""
    try:
        board = game_state["board"]
        you = game_state["you"]
        width, height = board["width"], board["height"]
        head = you["body"][0]

        occupied = set()
        for s in board["snakes"]:
            body = s["body"]
            n = len(body)
            for j, seg in enumerate(body):
                # tail is enterable unless the snake just ate (tail stacked on prev)
                if j == n - 1 and n > 1 and not (
                    body[-1]["x"] == body[-2]["x"] and body[-1]["y"] == body[-2]["y"]
                ):
                    continue
                occupied.add((seg["x"], seg["y"]))

        for dx, dy, name in ((0, 1, "up"), (0, -1, "down"), (-1, 0, "left"), (1, 0, "right")):
            nx, ny = head["x"] + dx, head["y"] + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in occupied:
                return {"move": name}
    except Exception:
        pass
    return {"move": "up"}


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        me = game_state["you"]
        snakes = board["snakes"]
        food = board.get("food", [])

        deadline = time.monotonic() + TIME_LIMIT

        enemy = _choose_enemy(me, snakes)

        grid = _build_grid(width, height, food, snakes)
        abgrid = _build_grid(width, height, food, snakes)

        # Block off squares a strictly-larger, non-enemy snake could move into.
        for s in snakes:
            if s["id"] != me["id"] and s["id"] != enemy["id"]:
                if len(s["body"]) > len(me["body"]):
                    for mv in _neighbours(s["body"][0], grid):
                        abgrid[mv["y"]][mv["x"]] = "?"

        state = {
            "me": {"id": me["id"], "health": me["health"],
                   "body": [{"x": b["x"], "y": b["y"]} for b in me["body"]]},
            "enemy": {"id": enemy["id"], "health": enemy["health"],
                      "body": [{"x": b["x"], "y": b["y"]} for b in enemy["body"]]},
            "snakes": [{"id": s["id"], "health": s["health"],
                        "body": [{"x": b["x"], "y": b["y"]} for b in s["body"]]}
                       for s in snakes],
        }

        best_move = None
        try:
            _, best_move = _alphabeta(
                abgrid, state, 0, -INF, INF, None, None, True, None, None, deadline)
        except _Timeout:
            best_move = None

        if best_move is None:
            best_move = _failsafe(
                {"id": me["id"], "health": me["health"],
                 "body": [{"x": b["x"], "y": b["y"]} for b in me["body"]]},
                snakes, grid, len(food))

        if best_move is None:
            return _safe_fallback(game_state)

        head = me["body"][0]
        direction = _direction(head, best_move)
        if direction is None:
            return _safe_fallback(game_state)

        # sanity: ensure resulting move is in-bounds
        if not (0 <= best_move["x"] < width and 0 <= best_move["y"] < height):
            return _safe_fallback(game_state)

        return {"move": direction}
    except Exception:
        return _safe_fallback(game_state)


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
