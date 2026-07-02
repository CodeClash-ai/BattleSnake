"""FamishedFrank battlesnake ported from coreyja/battlesnake-rs (famished_frank.rs).

Faithful reimplementation of the A* ("a-prime") based move logic:
 - Target length = height*2 + width.
 - If our body is shorter than target length, targets = all food.
   Otherwise targets = the four board corners (stall/survive by circling).
 - Filter out targets that are on our own body.
 - Run A* from head toward nearest target; take first step.
 - Fallback 1: A* toward our own tail.
 - Fallback 2: a random reasonable move (in-bounds, not into snake body).
Hazard penalty = 100, food penalty = 1 (defaults), NEIGHBOR_DISTANCE = 1.
"""

import heapq
import random

NEIGHBOR_DISTANCE = 1
HEURISTIC_MAX = 500


def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#FFBB33",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _heuristic(start_pos, targets):
    if not targets:
        return None
    return min(_manhattan(t, start_pos) for t in targets)


def _neighbors(coord, width, height):
    x, y = coord
    out = []
    for nx, ny in ((x, y + 1), (x, y - 1), (x - 1, y), (x + 1, y)):
        if 0 <= nx < width and 0 <= ny < height:
            out.append((nx, ny))
    return out


def _a_prime_next_direction(start_pos, targets, board, hazard_penalty=100, food_penalty=1):
    """Return the first step (a neighbor coordinate) along the shortest path, or None."""
    targets = set(targets)
    if not targets:
        return None

    width = board["width"]
    height = board["height"]
    hazards = set((h["x"], h["y"]) for h in board.get("hazards", []))
    food = set((f["x"], f["y"]) for f in board.get("food", []))
    # All snake body cells (used to block passage, except when a cell is itself a target).
    body_cells = set()
    for s in board["snakes"]:
        for p in s["body"]:
            body_cells.add((p["x"], p["y"]))

    # Dijkstra/A* with min-heap.
    known_score = {start_pos: 0}
    paths_from = {start_pos: None}
    # heap entries: (priority_cost, tiebreak_index, coordinate)
    counter = 0
    heap = [(0, counter, start_pos)]

    best_target = None
    while heap:
        _, _, coordinate = heapq.heappop(heap)

        if coordinate in targets:
            best_target = coordinate
            break

        if coordinate in hazards:
            neighbor_distance = hazard_penalty + NEIGHBOR_DISTANCE
        elif coordinate in food:
            neighbor_distance = NEIGHBOR_DISTANCE + food_penalty
        else:
            neighbor_distance = NEIGHBOR_DISTANCE

        tentative = known_score.get(coordinate, float("inf")) + neighbor_distance

        for neighbor in _neighbors(coordinate, width, height):
            # A neighbor is traversable if it's a target OR the *current* cell is
            # not a snake body cell (mirrors the Rust filter which checks the
            # current coordinate, allowing us to start from our own head).
            if not (neighbor in targets or coordinate not in body_cells):
                continue
            if tentative < known_score.get(neighbor, float("inf")):
                known_score[neighbor] = tentative
                paths_from[neighbor] = coordinate
                counter += 1
                h = _heuristic(neighbor, targets)
                if h is None:
                    h = HEURISTIC_MAX
                heapq.heappush(heap, (tentative + h, counter, neighbor))

    if best_target is None:
        return None

    # Reconstruct path back to start; the step after start is our move.
    path = []
    cur = best_target
    while cur is not None:
        path.append(cur)
        cur = paths_from.get(cur)
    path.reverse()
    if len(path) >= 2:
        return path[1]
    return None


def _random_reasonable_move(head, board):
    """A random in-bounds move that doesn't go into any snake body."""
    width = board["width"]
    height = board["height"]
    body_cells = set()
    for s in board["snakes"]:
        for p in s["body"]:
            body_cells.add((p["x"], p["y"]))
    candidates = [
        n for n in _neighbors(head, width, height) if n not in body_cells
    ]
    if candidates:
        return random.choice(candidates)
    return None


def _dir_from_step(head, step):
    hx, hy = head
    sx, sy = step
    if sy > hy:
        return "up"
    if sy < hy:
        return "down"
    if sx < hx:
        return "left"
    return "right"


def _safe_fallback(head, board):
    """Guaranteed in-bounds move; prefer non-body cells (tails are enterable)."""
    width = board["width"]
    height = board["height"]
    # Bodies excluding tails (tails will move away, so they are enterable).
    blocked = set()
    for s in board["snakes"]:
        body = s["body"]
        for p in body[:-1]:
            blocked.add((p["x"], p["y"]))
    nbrs = _neighbors(head, width, height)
    for n in nbrs:
        if n not in blocked:
            return _dir_from_step(head, n)
    if nbrs:
        return _dir_from_step(head, nbrs[0])
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        you = game_state["you"]
        width = board["width"]
        height = board["height"]

        you_body = [(p["x"], p["y"]) for p in you["body"]]
        head = you_body[0]

        target_length = height * 2 + width

        if len(you_body) < target_length:
            targets = [(f["x"], f["y"]) for f in board.get("food", [])]
        else:
            targets = [
                (0, 0),
                (width - 1, 0),
                (0, height - 1),
                (width - 1, height - 1),
            ]

        body_set = set(you_body)
        targets = [t for t in targets if t not in body_set]

        step = _a_prime_next_direction(head, targets, board)

        if step is None:
            # Fallback 1: head toward our own tail.
            tail = you_body[-1]
            step = _a_prime_next_direction(head, [tail], board)

        if step is None:
            # Fallback 2: random reasonable move.
            step = _random_reasonable_move(head, board)

        if step is None:
            return {"move": _safe_fallback(head, board)}

        return {"move": _dir_from_step(head, step)}
    except Exception:
        try:
            board = game_state["board"]
            head = (game_state["you"]["body"][0]["x"], game_state["you"]["body"][0]["y"])
            return {"move": _safe_fallback(head, board)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
