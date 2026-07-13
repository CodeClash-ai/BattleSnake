import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""Port of jackisherwood/battleSnakeElon (JavaScript, 2019) to Battlesnake v1 API.

Faithful reimplementation of smorts.js / floodFill.js / server.js move logic.

Coordinate remap: the original used a top-left / y-down system, where the
`whatDir`/`getCurrentDir` helpers treated smaller y as "up". The v1 API uses a
bottom-left / y-up system (up = y+1, down = y-1). Only the direction-naming in
those two helpers depends on this, so they are remapped accordingly. All other
geometry (neighbor generation, distances, floodfill) is orientation-agnostic
and ported verbatim.
"""

import math


# ---------- helpers.js ----------

def get_neighbors(position):
    x, y = position["x"], position["y"]
    return [
        {"x": x, "y": y + 1},
        {"x": x, "y": y - 1},
        {"x": x + 1, "y": y},
        {"x": x - 1, "y": y},
    ]


# ---------- smorts.js ----------

def pos_diff(arr1, arr2):
    """differenceWith by (x,y): elements of arr1 not present in arr2."""
    key2 = {(p["x"], p["y"]) for p in arr2}
    return [p for p in arr1 if (p["x"], p["y"]) not in key2]


def remove_oob(arr, width, height):
    return [p for p in arr if 0 <= p["x"] < width and 0 <= p["y"] < height]


def abs_point_difference(p1, p2):
    return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])


def py_diff(p1, p2):
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)


def smallest_py_dist(point, point_array):
    if not point_array:
        return float("inf")
    return min(py_diff(point, p) for p in point_array)


def smallest_distance(point, point_array):
    if not point_array:
        return float("inf")
    return min(abs_point_difference(point, p) for p in point_array)


def what_dir(head, nxt):
    # v1-remapped: up = larger y, down = smaller y
    if nxt["x"] > head["x"]:
        return "right"
    elif nxt["x"] < head["x"]:
        return "left"
    elif nxt["y"] > head["y"]:
        return "up"
    else:
        return "down"


def get_hungry(food):
    hungry_mod = 40 - (len(food) * 4)
    if hungry_mod < 0:
        hungry_mod = 0
    elif hungry_mod > 40:
        hungry_mod = 40
    return 50 + hungry_mod


def get_current_dir(head, prev):
    x_dir = head["x"] - prev["x"]
    y_dir = head["y"] - prev["y"]
    if x_dir < 0:
        return "left"
    elif x_dir > 0:
        return "right"
    elif y_dir > 0:  # v1-remapped: moved up
        return "up"
    else:
        return "down"


def collision_avoider(move_options, snek_parts, my_body, head):
    tail = my_body[-1]
    # _.reverse(_.sortBy(x, distToSnek, distToTail)) => descending by
    # (distToSnek, distToTail) with sortBy stability reversed.
    sorted_opts = _reverse_sort_by(
        move_options,
        [lambda x: smallest_py_dist(x, snek_parts),
         lambda x: abs_point_difference(tail, x)],
    )
    return what_dir(head, sorted_opts[0])


def tail_chaser(move_options, my_body, head):
    tail = my_body[-1]
    current_dir = get_current_dir(head, my_body[1]) if len(my_body) > 1 else None
    sorted_opts = _sort_by(
        move_options,
        [lambda x: abs_point_difference(tail, x),
         lambda x: 1 if what_dir(head, x) != current_dir else -1],
    )
    chosen = sorted_opts[0] if sorted_opts else tail
    return what_dir(head, chosen)


def food_seeker(move_options, board_food, head):
    sorted_opts = _sort_by(
        move_options, [lambda x: smallest_distance(x, board_food)]
    )
    return what_dir(head, sorted_opts[0])


def get_move_options(all_snakes, head, width, height):
    gen_options = get_neighbors(head)
    return remove_oob(pos_diff(gen_options, all_snakes), width, height)


# lodash sortBy is a stable sort by a tuple of iteratee results.
def _sort_by(arr, iteratees):
    return sorted(arr, key=lambda x: tuple(f(x) for f in iteratees))


def _reverse_sort_by(arr, iteratees):
    # lodash _.reverse(_.sortBy(...)): sort ascending (stable), then reverse.
    return list(reversed(_sort_by(arr, iteratees)))


# ---------- floodFill.js ----------

def _valid(width, height, snake_parts, flooded, position):
    x, y = position["x"], position["y"]
    if x < 0 or y < 0 or x >= width or y >= height:
        return False
    if snake_parts.get((x, y)):
        return False
    if flooded.get((x, y)):
        return False
    return True


def flood_from(width, height, snake_parts, mx, position):
    flooded = {}
    space = 0
    stack = [position]
    while space < mx + 1 and len(stack) > 0:
        current = stack.pop()
        space += 1
        flooded[(current["x"], current["y"])] = True
        neighbors = get_neighbors(current)
        valid_neighbors = [
            n for n in neighbors if _valid(width, height, snake_parts, flooded, n)
        ]
        for n in valid_neighbors:
            stack.append(n)
    return space


# ---------- server.js /move ----------

def move(game_state):
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return _safe_fallback(game_state)


def _decide(game_state):
    turn = game_state["turn"]
    board = game_state["board"]
    food = board["food"]
    you = game_state["you"]

    health = you["health"]
    my_body = you["body"]
    head = my_body[0]

    all_snakes = []
    for s in board["snakes"]:
        all_snakes.extend(s["body"])

    snake_obj = {(p["x"], p["y"]): True for p in all_snakes}

    snek_parts = pos_diff(all_snakes, my_body)
    move_options = get_move_options(all_snakes, head, board["width"], board["height"])

    # Floodfill to avoid dead ends
    threshold = len(my_body) + 5
    new_move_options = [
        x for x in move_options
        if flood_from(board["width"], board["height"], snake_obj, threshold, x)
        >= threshold
    ]
    if len(new_move_options) > 0:
        move_options = new_move_options
    elif move_options:
        move_options = [
            sorted(
                move_options,
                key=lambda x: -flood_from(
                    board["width"], board["height"], snake_obj, len(my_body), x
                ),
            )[0]
        ]

    head_to_snek = smallest_distance(head, snek_parts)
    hungry = 200 if turn < 10 else get_hungry(food)

    my_move = "up"

    if head_to_snek <= 3:  # scared state
        my_move = collision_avoider(move_options, snek_parts, my_body, head)
    elif health <= hungry and len(food) > 0:  # hungry state
        my_move = food_seeker(move_options, food, head)
    else:  # wimpy state
        my_move = tail_chaser(move_options, my_body, head)

    if len(move_options) == 0:
        my_move = what_dir(head, my_body[-1])

    # Safety net: ensure the returned move is legal if at all possible.
    return _ensure_legal(my_move, game_state)


def _neighbor_for(head, direction):
    if direction == "up":
        return {"x": head["x"], "y": head["y"] + 1}
    if direction == "down":
        return {"x": head["x"], "y": head["y"] - 1}
    if direction == "left":
        return {"x": head["x"] - 1, "y": head["y"]}
    return {"x": head["x"] + 1, "y": head["y"]}


def _blocked_cells(game_state):
    """Occupied cells; tails are enterable (excluded) unless the snake just ate."""
    board = game_state["board"]
    blocked = set()
    for s in board["snakes"]:
        body = s["body"]
        just_ate = s.get("health", 0) == 100
        cells = body if just_ate else body[:-1]
        for p in cells:
            blocked.add((p["x"], p["y"]))
    return blocked


def _is_legal(direction, game_state):
    board = game_state["board"]
    head = game_state["you"]["body"][0]
    n = _neighbor_for(head, direction)
    if not (0 <= n["x"] < board["width"] and 0 <= n["y"] < board["height"]):
        return False
    return (n["x"], n["y"]) not in _blocked_cells(game_state)


def _ensure_legal(my_move, game_state):
    if _is_legal(my_move, game_state):
        return my_move
    for d in ("up", "down", "left", "right"):
        if _is_legal(d, game_state):
            return d
    return my_move


def _safe_fallback(game_state):
    try:
        for d in ("up", "down", "left", "right"):
            if _is_legal(d, game_state):
                return {"move": d}
    except Exception:
        pass
    return {"move": "up"}


# ---------- v1 API scaffolding ----------

def info():
    return {
        "apiversion": "1",
        "author": "jackisherwood",
        "color": "#FEFEFE",
        "head": "beluga",
        "tail": "pixel",
    }


def start(game_state):
    return None


def end(game_state):
    return None


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
