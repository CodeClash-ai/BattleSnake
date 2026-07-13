"""
Port of `gigantic_george` from https://github.com/coreyja/battlesnake-rs
(battlesnake-rs/src/gigantic_george.rs), owner handle: coreyja.

GiganticGeorge delegates its core movement to EremeticEric (eremetic_eric.rs),
adding a board-filling (Hamiltonian completion) step only when the board has no
empty squares. Both rely on the A* pathfinder in a_prime.rs.

Strategy (EremeticEric), reproduced faithfully:
  - A* (`shortest_path`) over the wire board: neighbors blocked if they are any
    snake body (unless they are a target); moving onto food costs +1.
  - Evaluate each food's closest own-body-part and cost; compute a `health_cost`
    heuristic to decide whether to chase food or keep looping around own tail.
  - If head is the closest body part AND can't survive another loop -> path to
    best food. If turn < 3 -> path to nearest food. Otherwise -> path toward own
    tail (with a food penalty of 1).

GiganticGeorge extras:
  - The PATH: shout-following mechanic requires persistent shout state that the
    stateless CodeClash arena does not provide, so it is inert here (matches the
    real behavior when no such shout exists).
  - When the board has no empty squares, attempt a DFS Hamiltonian completion
    (`path_to_full_board`); on failure, fall through to EremeticEric. This is
    depth-limited for time safety.

FIDELITY: approximate -- move logic is faithful; the persistent PATH shout state
machine cannot be reproduced statelessly, and the Hamiltonian DFS is
depth/time-limited. Core A* + food/loop decision is a direct port.

Modern v1 API: bottom-left origin, y-up. up=y+1, down=y-1, left=x-1, right=x+1.
"""

import heapq
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ---- Move helpers -----------------------------------------------------------

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def _neighbors(pos, width, height):
    x, y = pos
    result = []
    for dx, dy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            result.append((nx, ny))
    return result


def _move_name_from_delta(dx, dy):
    for name, (mx, my) in MOVES.items():
        if (mx, my) == (dx, dy):
            return name
    return None


# ---- A* (port of a_prime.rs Game::a_prime_inner) ----------------------------

NEIGHBOR_DISTANCE = 1
HEURISTIC_MAX = 500


def _manhattan_to_targets(pos, targets):
    if not targets:
        return HEURISTIC_MAX
    return min(abs(pos[0] - t[0]) + abs(pos[1] - t[1]) for t in targets)


def _a_prime_inner(start, targets, width, height, food_set, hazard_set,
                   body_set, food_penalty=1, hazard_penalty=1):
    """Returns (best_cost, paths_from, best_target) or None."""
    if not targets:
        return None
    target_set = set(targets)

    to_search = []  # (priority_cost, tiebreak, coordinate)
    counter = 0
    heapq.heappush(to_search, (0, counter, start))
    known_score = {start: 0}
    paths_from = {start: None}

    while to_search:
        _, _, coordinate = heapq.heappop(to_search)

        if coordinate in target_set:
            return (known_score[coordinate], paths_from, coordinate)

        if coordinate in hazard_set:
            neighbor_distance = hazard_penalty + NEIGHBOR_DISTANCE
        elif coordinate in food_set:
            neighbor_distance = NEIGHBOR_DISTANCE + food_penalty
        else:
            neighbor_distance = NEIGHBOR_DISTANCE

        tentative = known_score.get(coordinate, float("inf")) + neighbor_distance

        for neighbor in _neighbors(coordinate, width, height):
            # neighbor allowed if it's a target OR not any snake body
            if not (neighbor in target_set or neighbor not in body_set):
                continue
            if tentative < known_score.get(neighbor, float("inf")):
                known_score[neighbor] = tentative
                paths_from[neighbor] = coordinate
                counter += 1
                priority = tentative + _manhattan_to_targets(neighbor, targets)
                heapq.heappush(to_search, (priority, counter, neighbor))

    return None


def _shortest_path(start, targets, width, height, food_set, hazard_set,
                   body_set, food_penalty=1, hazard_penalty=1):
    result = _a_prime_inner(start, targets, width, height, food_set,
                            hazard_set, body_set, food_penalty, hazard_penalty)
    path = []
    if result is not None:
        _, paths_from, current = result
        while current is not None:
            path.append(current)
            current = paths_from.get(current)
    path.reverse()
    return path


def _shortest_distance(start, targets, width, height, food_set, hazard_set,
                       body_set, food_penalty=1, hazard_penalty=1):
    result = _a_prime_inner(start, targets, width, height, food_set,
                            hazard_set, body_set, food_penalty, hazard_penalty)
    if result is None:
        return None
    return result[0]


def _shortest_path_next_direction(start, targets, width, height, food_set,
                                  hazard_set, body_set, food_penalty=1,
                                  hazard_penalty=1):
    path = _shortest_path(start, targets, width, height, food_set, hazard_set,
                          body_set, food_penalty, hazard_penalty)
    if len(path) < 2:
        return None
    nxt = path[1]
    dx = nxt[0] - start[0]
    dy = nxt[1] - start[1]
    return _move_name_from_delta(dx, dy)


# ---- Fallback safe move -----------------------------------------------------

def _safe_move(head, body_list, all_snake_bodies, width, height):
    """Any in-bounds move not into a snake body; tails are enterable."""
    occupied = set()
    for snake_body in all_snake_bodies:
        # tail (last segment) is enterable (it moves away), unless health-fed;
        # we conservatively allow tail entry per problem spec.
        for seg in snake_body[:-1]:
            occupied.add(tuple(seg))
    for name, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in occupied:
            return name
    # nothing safe; pick any in-bounds
    for name, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        if 0 <= nx < width and 0 <= ny < height:
            return name
    return "up"


# ---- Hamiltonian completion DFS (port of path_to_full_board) ----------------

_DFS_NODE_LIMIT = 20000
_DFS_WALL_CLOCK = 0.3  # seconds; bound the exponential DFS for arena time safety


def _path_to_full_board(reversed_body, width, height, counter):
    # counter = [node_count, deadline_monotonic]
    max_size = width * height
    if len(reversed_body) == max_size:
        return []
    counter[0] += 1
    if counter[0] > _DFS_NODE_LIMIT or time.monotonic() > counter[1]:
        return None
    body_set = set(reversed_body)
    last = reversed_body[-1]
    for coor in _neighbors(last, width, height):
        if coor in body_set:
            continue
        new_body = reversed_body + [coor]
        sub = _path_to_full_board(new_body, width, height, counter)
        if sub is not None:
            dx = coor[0] - last[0]
            dy = coor[1] - last[1]
            sub.append((_move_name_from_delta(dx, dy), coor))
            return sub
    return None


# ---- EremeticEric make_move (faithful port) ---------------------------------

def _eremetic_eric_move(game_state):
    you = game_state["you"]
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    turn = game_state.get("turn", 0)

    body = [(p["x"], p["y"]) for p in you["body"]]
    head = body[0]
    health = you["health"]

    food_set = set((f["x"], f["y"]) for f in board.get("food", []))
    hazard_set = set((h["x"], h["y"]) for h in board.get("hazards", []))
    all_food = list(food_set)

    all_snake_bodies = [[(p["x"], p["y"]) for p in s["body"]]
                        for s in board["snakes"]]
    body_set = set()
    for sb in all_snake_bodies:
        body_set.update(sb)

    tail = body[-1]

    # Build modified board: push tail along the shortest path back to complete
    # the circle (extend own body along that path). Used for the "back to tail"
    # distance estimate.
    path_to_complete = _shortest_path(head, [tail], width, height, food_set,
                                      hazard_set, body_set)
    modified_body_set = set(body_set)
    # path_to_complete_circle.reverse() then push_tail each not-in-body cell
    for c in reversed(path_to_complete):
        if c not in body:
            modified_body_set.add(c)

    if not all_food:
        return _safe_move(head, body, all_snake_bodies, width, height)

    def dist_between(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # food_options: for each food, the closest body part(s) by manhattan dist.
    food_options = []  # (food, (body_part, best_cost))
    for food in all_food:
        body_options = [(bp, dist_between(food, bp)) for bp in body]
        best = min(body_options, key=lambda x: x[1])
        for bp, cost in body_options:
            if cost == best[1]:
                food_options.append((food, (bp, best[1])))

    best_cost = min(fo[1][1] for fo in food_options)
    matching_cost_foods = [fo for fo in food_options if fo[1][1] == best_cost]

    cost_to_loop = len(body)

    matching_food_options = []  # ((food,(closest_bp,best_cost)), (health_cost, food))
    for (food, (closest_body_part, _)) in matching_cost_foods:
        closest_index = body.index(closest_body_part)
        tail_index = len(body) - 1 if closest_index == 0 else closest_index - 1
        would_be_tail = body[tail_index]

        d = _shortest_distance(food, [would_be_tail], width, height, food_set,
                               hazard_set, modified_body_set)
        dist_back_from_food_to_tail = d if d is not None else 5000

        cost_to_get_to_closest = 0 if closest_index == 0 else (cost_to_loop - closest_index)
        cost_to_get_to_nearest_food = cost_to_get_to_closest + best_cost
        cost_to_get_food_and_back = best_cost + dist_back_from_food_to_tail

        if health >= cost_to_get_to_nearest_food:
            health_when_at_closest = health - cost_to_get_to_closest
            health_cost = health_when_at_closest + cost_to_get_food_and_back
        else:
            health_cost = 6666

        matching_food_options.append(
            ((food, (closest_body_part, best_cost)), (health_cost, food))
        )

    # sorted_by_key on (health_cost, food); food is a tuple -> stable ordering
    matching_food_options.sort(key=lambda x: (x[1][0], x[1][1]))

    (best_food, (closest_body_part, best_cost2)) = matching_food_options[0][0]

    cant_survive_another_loop = health < cost_to_loop + best_cost2
    you_head = head

    # If head is the closest body part and we can't survive another loop -> food
    if you_head == closest_body_part and cant_survive_another_loop:
        d = _shortest_path_next_direction(you_head, [best_food], width, height,
                                          food_set, hazard_set, body_set)
        if d is not None:
            return d

    # Early game: go for nearest food
    if turn < 3:
        d = _shortest_path_next_direction(you_head, all_food, width, height,
                                          food_set, hazard_set, body_set)
        if d is not None:
            return d

    # Default: loop -- path toward own tail, with food penalty of 1
    d = _shortest_path_next_direction(you_head, [tail], width, height,
                                      food_set, hazard_set, body_set,
                                      food_penalty=1)
    if d is not None:
        return d

    return _safe_move(head, body, all_snake_bodies, width, height)


# ---- GiganticGeorge make_move ----------------------------------------------

def _contains_empty_squares(board):
    occupied = set()
    for f in board.get("food", []):
        occupied.add((f["x"], f["y"]))
    for s in board["snakes"]:
        for c in s["body"]:
            occupied.add((c["x"], c["y"]))
    full_size = board["height"] * board["width"]
    return full_size != len(occupied)


def _gigantic_george_move(game_state):
    you = game_state["you"]
    board = game_state["board"]
    width = board["width"]
    height = board["height"]

    # (PATH: shout-following requires persistent state the arena doesn't give;
    # inert here, matching real behavior when no such shout exists.)

    if not _contains_empty_squares(board):
        body = [(p["x"], p["y"]) for p in you["body"]]
        # reversed_body: pop current tail, reverse
        reversed_body = body[:-1]
        reversed_body.reverse()
        if reversed_body:
            deadline = time.monotonic() + _DFS_WALL_CLOCK
            path = _path_to_full_board(reversed_body, width, height,
                                       [0, deadline])
            if path is not None and path:
                new = path.pop()  # first move to make
                return new[0]

    return _eremetic_eric_move(game_state)


# ---- v1 API entry points ----------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#FFBB33",
        "head": "trans-rights-scarf",
        "tail": "default",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def move(game_state):
    try:
        m = _gigantic_george_move(game_state)
        if m not in MOVES:
            raise ValueError("invalid move")
        return {"move": m}
    except Exception:
        try:
            you = game_state["you"]
            board = game_state["board"]
            head = (you["body"][0]["x"], you["body"][0]["y"])
            body = [(p["x"], p["y"]) for p in you["body"]]
            all_bodies = [[(p["x"], p["y"]) for p in s["body"]]
                          for s in board["snakes"]]
            return {"move": _safe_move(head, body, all_bodies,
                                       board["width"], board["height"])}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
