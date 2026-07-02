import random

# Port of moxuz / chrispouliot "Battlesnake-AI-2017" (pinky-snek).
# Original strategy (old Battlesnake API, top-left/y-down board):
#   - Danger coords = all walls (off-board edges), every snake body cell,
#     plus any empty cell whose adjacent neighbors are dangerous >= 3 times
#     (avoids dead-end pockets).
#   - Safe coords = all board cells minus danger coords.
#   - Move selection: adjacent cells that are safe. If health < 30, take an
#     adjacent food cell if one exists; otherwise pick a random safe adjacent.
# Remapped here to v1 API (bottom-left / y-up) and made robust.

COORD_DANGER_LEVEL_MAX = 3
MIN_FOOD_HEALTH_LEVEL = 30


def info():
    return {
        "apiversion": "1",
        "author": "moxuz",
        "color": "#ffb6c1",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return


def end(game_state):
    return


def _adjacent(coord):
    x, y = coord
    # v1 (bottom-left origin): up = y+1, down = y-1, right = x+1, left = x-1
    return [
        [x, y + 1],
        [x, y - 1],
        [x + 1, y],
        [x - 1, y],
    ]


def _all_board_coords(width, height):
    return [[x, y] for x in range(width) for y in range(height)]


def _get_dangerous_coords(width, height, snake_coords, max_danger_level):
    danger_coords = []
    # Walls (off-board edges) are dangerous
    for x in range(width):
        danger_coords.append([x, -1])
        danger_coords.append([x, height])
    for y in range(height):
        danger_coords.append([-1, y])
        danger_coords.append([width, y])

    # Every snake body cell is dangerous (faithful to original)
    danger_coords += snake_coords

    # Empty cells surrounded by >= max_danger_level dangerous neighbors
    for empty_coord in _all_board_coords(width, height):
        num_dangerous = 0
        for adj in _adjacent(empty_coord):
            if adj in danger_coords:
                num_dangerous += 1
        if num_dangerous >= max_danger_level:
            danger_coords.append(empty_coord)

    return danger_coords


def _direction_from_coord(next_coord, curr_coord):
    nx, ny = next_coord
    cx, cy = curr_coord
    if nx < cx:
        return "left"
    elif nx > cx:
        return "right"
    elif ny > cy:
        return "up"      # v1: y+1 is up (original used "down" for y-down board)
    else:
        return "down"


def _safe_fallback(game_state):
    """Guaranteed-legal move: in bounds and not into any snake body cell
    (tails allowed since they move)."""
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    blocked = set()
    for snake in board["snakes"]:
        body = snake["body"]
        for i, seg in enumerate(body):
            # Allow the tail cell (it moves away) unless food may have grown it.
            if i == len(body) - 1:
                continue
            blocked.add((seg["x"], seg["y"]))

    options = {
        "up": (hx, hy + 1),
        "down": (hx, hy - 1),
        "left": (hx - 1, hy),
        "right": (hx + 1, hy),
    }
    for mv, (x, y) in options.items():
        if 0 <= x < width and 0 <= y < height and (x, y) not in blocked:
            return {"move": mv}
    # Last resort: any in-bounds move
    for mv, (x, y) in options.items():
        if 0 <= x < width and 0 <= y < height:
            return {"move": mv}
    return {"move": "up"}


def move(game_state):
    try:
        board = game_state["board"]
        width = board["width"]
        height = board["height"]
        you = game_state["you"]

        head = you["body"][0]
        curr_coord = [head["x"], head["y"]]
        health = you.get("health", 100)

        # Flatten all snake body coords
        snake_coords = []
        for snake in board["snakes"]:
            for seg in snake["body"]:
                snake_coords.append([seg["x"], seg["y"]])

        food_coords = [[f["x"], f["y"]] for f in board.get("food", [])]

        dangerous = _get_dangerous_coords(width, height, snake_coords, COORD_DANGER_LEVEL_MAX)
        all_coords = _all_board_coords(width, height)
        safe_coords = [c for c in all_coords if c not in dangerous]

        adjacent_coords = _adjacent(curr_coord)
        possible = [c for c in adjacent_coords if c in safe_coords]

        next_coord = None
        if health < MIN_FOOD_HEALTH_LEVEL:
            for c in possible:
                if c in food_coords:
                    next_coord = c
                    break
        if next_coord is None and possible:
            next_coord = random.choice(possible)

        if next_coord is not None:
            candidate = _direction_from_coord(next_coord, curr_coord)
            # Validate against fallback safety (in bounds, not into body)
            nx, ny = next_coord
            if 0 <= nx < width and 0 <= ny < height:
                return {"move": candidate}

        # No safe adjacent cell found; fall back to any legal move.
        return _safe_fallback(game_state)
    except Exception:
        try:
            return _safe_fallback(game_state)
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
