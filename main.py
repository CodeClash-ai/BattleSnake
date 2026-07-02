"""
Port of xtagon/nagini (Elixir, 2019) to a self-contained Python main.py
against the current Battlesnake v1 API.

Faithful reimplementation of Nagini.Solver / Nagini.Helper:
  - Evaluate the 4 directions, scoring each move by:
      * collision_avoidance (primary sort key)
      * food_seeking       (secondary sort key)
  - collision_avoidance:
      * -1 if the move goes out of bounds (wall)
      * otherwise value_of_collision_with_snake():
          - for each snake, check_collision() produces an outcome:
              :lose  (direct body impact, or head-to-head losing) -> weight -1
              :draw  (head-to-head, equal length)                 -> weight -0.5
              :win   (head-to-head, we are longer)                -> weight +1
              :free                                               -> weight  0
            probability = 1 for direct impact, 1/3 for possible head-to-head, else 0
            value = weight * probability
          - collisions with outcome :free are dropped
          - if any remaining collision: take worst (min value); if worst <= 0
            use worst value else use the average value; else 0
  - food_seeking = probability_of_eating_food():
      * 0 if no food
      * 1 if food is on the target cell (distance 0)
      * else 1 / (nearest manhattan distance)
  - Optional recursive lookahead (max_depth, default 0 as in production): simulate
    opponent moves (each opponent solved greedily at depth 0) then our move, and
    add the best future collision_avoidance to the current one.

Coordinate remap: the original Elixir code used a top-left / y-down board
(step up = y-1, down = y+1). The v1 API is bottom-left / y-up. Since every
scoring function except `step` is symmetric under a y-flip, we only need a
v1-correct `step` (up=y+1, down=y-1, left=x-1, right=x+1). The strategy is
otherwise identical.
"""

DIRECTIONS = ["up", "down", "left", "right"]


# ---------- coordinate / basic helpers ----------

def step(coord, direction):
    x, y = coord["x"], coord["y"]
    if direction == "up":
        return {"x": x, "y": y + 1}
    if direction == "down":
        return {"x": x, "y": y - 1}
    if direction == "left":
        return {"x": x - 1, "y": y}
    if direction == "right":
        return {"x": x + 1, "y": y}
    return {"x": x, "y": y}


def head_of(snake):
    return snake["body"][0]


def step_snake(snake, direction):
    return step(head_of(snake), direction)


def out_of_bounds(board, target):
    if target["y"] < 0 or target["x"] < 0:
        return True
    if target["y"] >= board["height"]:
        return True
    if target["x"] >= board["width"]:
        return True
    return False


def coords_equal(a, b):
    return a["x"] == b["x"] and a["y"] == b["y"]


def manhattan_distance(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def adjacent(a, b):
    return ((a["x"] == b["x"] and abs(a["y"] - b["y"]) == 1) or
            (a["y"] == b["y"] and abs(a["x"] - b["x"]) == 1))


def food_at(board, coord):
    return any(coords_equal(f, coord) for f in board["food"])


# ---------- collision analysis (Helper.check_collision) ----------

def check_collision(you, target, other_snake):
    you_are_other = (you["id"] == other_snake["id"] and
                     you["body"] == other_snake["body"])

    body = other_snake["body"]
    last = body[-1]
    second_last = body[-2] if len(body) >= 2 else None

    # Reject the tail cell when it is enterable (tail == last and last will move,
    # i.e. last != second_last). Otherwise the cell is a solid body part.
    solid_parts = []
    for part in body:
        is_free_tail = (coords_equal(part, last) and
                        (second_last is None or not coords_equal(part, second_last)))
        if not is_free_tail:
            solid_parts.append(part)

    direct_impact = any(coords_equal(p, target) for p in solid_parts)

    other_head = body[0]
    possible_head_to_head = (not you_are_other) and adjacent(other_head, target)

    if direct_impact:
        probability = 1.0
    elif possible_head_to_head:
        probability = 1.0 / 3.0
    else:
        probability = 0.0

    if direct_impact:
        outcome = "lose"
    elif possible_head_to_head:
        if len(other_snake["body"]) == len(you["body"]):
            outcome = "draw"
        elif len(other_snake["body"]) < len(you["body"]):
            outcome = "win"
        else:
            outcome = "lose"
    else:
        outcome = "free"

    weight = {"win": 1.0, "draw": -0.5, "free": 0.0, "lose": -1.0}[outcome]
    value = weight * probability

    return {"outcome": outcome, "value": value, "probability": probability}


def value_of_collision_with_snake(board, you, target):
    collisions = [check_collision(you, target, s) for s in board["snakes"]]
    collisions = [c for c in collisions if c["outcome"] != "free"]

    if len(collisions) > 0:
        worst = min(collisions, key=lambda c: c["value"])
        average = sum(c["value"] for c in collisions) / len(collisions)
        if worst["value"] <= 0:
            return worst["value"]
        return average
    return 0.0


def probability_of_eating_food(board, target):
    if not board["food"]:
        return 0.0
    nearest = min(manhattan_distance(f, target) for f in board["food"])
    if nearest == 0:
        return 1.0
    return 1.0 / nearest


# ---------- move analysis / sorting (Solver) ----------

def value_of_move(world, direction):
    you = world["you"]
    board = world["board"]
    target = step_snake(you, direction)

    if out_of_bounds(board, target):
        collision_avoidance = -1.0
    else:
        collision_avoidance = value_of_collision_with_snake(board, you, target)

    return {
        "collision_avoidance": collision_avoidance,
        "food_seeking": probability_of_eating_food(board, target),
    }


def analyze_move(world, direction):
    return {"direction": direction, "value": value_of_move(world, direction)}


def sort_solutions_by_value(solutions):
    # Sort ascending by food_seeking then collision_avoidance, then reverse
    # -> descending by collision_avoidance (primary), food_seeking (secondary).
    s = sorted(solutions, key=lambda x: x["value"]["food_seeking"])
    s = sorted(s, key=lambda x: x["value"]["collision_avoidance"])
    s.reverse()
    return s


# ---------- world simulation for lookahead ----------

def simulate_your_move(world, direction):
    you = world["you"]
    board = world["board"]
    new_head = step_snake(you, direction)
    updated_body = [new_head] + you["body"][:-1]
    updated_you = dict(you)
    updated_you["body"] = updated_body
    updated_you["head"] = new_head
    updated_you["length"] = len(updated_body)

    updated_snakes = []
    for snake in board["snakes"]:
        if you["id"] == snake["id"] and you["body"] == snake["body"]:
            updated_snakes.append(updated_you)
        else:
            updated_snakes.append(snake)

    new_board = dict(board)
    new_board["snakes"] = updated_snakes
    return {**world, "you": updated_you, "board": new_board}


def simulate_opponent_move(world, opponent):
    board = world["board"]
    direction = solve_for_opponent(world, opponent)
    new_head = step_snake(opponent, direction)
    did_eat = food_at(board, new_head)
    updated_body = [new_head] + opponent["body"][:-1]
    if did_eat:
        updated_body = updated_body + [updated_body[-1]]
    updated_opp = dict(opponent)
    updated_opp["body"] = updated_body
    updated_opp["head"] = new_head
    updated_opp["length"] = len(updated_body)

    updated_snakes = []
    for snake in board["snakes"]:
        if opponent["id"] == snake["id"] and opponent["body"] == snake["body"]:
            updated_snakes.append(updated_opp)
        else:
            updated_snakes.append(snake)

    new_board = dict(board)
    new_board["snakes"] = updated_snakes
    return {**world, "board": new_board}


def simulate_opponent_moves(world):
    you = world["you"]
    opponents = [s for s in world["board"]["snakes"]
                 if not (s["id"] == you["id"] and s["body"] == you["body"])]
    w = world
    for opp in opponents:
        # re-fetch current opponent state from the (possibly updated) board
        w = simulate_opponent_move(w, opp)
    return w


def solve_for_opponent(world, opponent):
    opponent_world = {**world, "you": opponent}
    return solve(opponent_world, 0, 0) or "up"


# ---------- solver (Solver.solve) ----------

def solve(world, max_depth=0, depth=0):
    solutions = [analyze_move(world, d) for d in DIRECTIONS]
    solutions = sort_solutions_by_value(solutions)

    dont_kill_me = [s for s in solutions if s["value"]["collision_avoidance"] > -1]
    not_dead_yet = len(dont_kill_me) > 0

    if depth < max_depth and not_dead_yet:
        future_base = simulate_opponent_moves(world)
        revised = []
        for solution in dont_kill_me:
            future_world = simulate_your_move(future_base, solution["direction"])
            best_future = solve(future_world, max_depth, depth + 1)
            if best_future:
                revised.append({
                    "direction": solution["direction"],
                    "value": {
                        "food_seeking": solution["value"]["food_seeking"],
                        "collision_avoidance": (best_future["value"]["collision_avoidance"]
                                                + solution["value"]["collision_avoidance"]),
                    },
                })
            else:
                revised.append(solution)
        solutions = revised

    solutions = sort_solutions_by_value(solutions)
    best_solution = solutions[0] if solutions else None

    if depth == 0:
        return best_solution["direction"] if best_solution else None
    return best_solution


# ---------- Battlesnake v1 API ----------

def info():
    return {
        "apiversion": "1",
        "author": "xtagon",
        "color": "#6b46c1",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        world = {
            "board": game_state["board"],
            "turn": game_state.get("turn", 0),
            "you": game_state["you"],
        }
        # Production default: max_depth = 0 (single-ply greedy).
        chosen = solve(world, max_depth=0)
        if chosen in DIRECTIONS:
            return {"move": chosen}
        return {"move": _safe_fallback(game_state)}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


def _safe_fallback(game_state):
    """Return any in-bounds move that does not enter a snake body (tails ok)."""
    board = game_state["board"]
    you = game_state["you"]
    head = you["body"][0]

    occupied = set()
    for snake in board["snakes"]:
        body = snake["body"]
        # tail cell is enterable unless the snake just grew (tail == prev cell)
        for i, part in enumerate(body):
            is_tail = (i == len(body) - 1)
            if is_tail and len(body) >= 2 and not coords_equal(body[-1], body[-2]):
                continue
            occupied.add((part["x"], part["y"]))

    for d in DIRECTIONS:
        t = step(head, d)
        if out_of_bounds(board, t):
            continue
        if (t["x"], t["y"]) in occupied:
            continue
        return d
    return "up"


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
