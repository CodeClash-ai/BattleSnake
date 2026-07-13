import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Port of tyrelh/battlesnake-python ("Zero_Cool") to Battlesnake v1 API.
#
# Original strategy (faithfully reproduced):
#   - Compute a health-minimum threshold = max(width,height)*2 (or own length if longer).
#   - If health < threshold OR we are not the biggest snake -> seek closest food (A*).
#   - Otherwise -> "kill time" by pathing toward our own tail (A*).
#   - On the first 3 turns always target the closest food.
#   - Build an integer grid: food=FOOD, snake bodies=SNAKE_BODY, enemy heads=ENEMY_HEAD,
#     and mark DANGER (or KILL_ZONE if the enemy is shorter than us) in the four cells
#     around each enemy head. Tails are cleared to SPACE unless the snake just ate.
#   - A* returns a recommended next move; best_move() then classifies the legal
#     neighbours into kill/regular/danger buckets and, using a flood-fill area count
#     (look_ahead) and a tail-reachability check (move_contains_tail), picks the best.
#
# NOTE on coordinates: the original used the OLD API (top-left origin, y increasing
# DOWNWARD), where internal UP = y-1 and DOWN = y+1. The v1 API uses a BOTTOM-LEFT
# origin (y increasing UPWARD). All internal grid/pathfinding logic is orientation
# agnostic; only the emitted direction label must be remapped:
#   internal UP  (toward lower y) -> v1 "down"
#   internal DOWN(toward higher y) -> v1 "up"
#   internal LEFT/RIGHT           -> v1 "left"/"right" (x unchanged)

# board cell states
SPACE = 0
KILL_ZONE = 1
FOOD = 2
DANGER = 3
SNAKE_BODY = 4
ENEMY_HEAD = 5

# internal direction indices (matches original)
UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3

# Map internal direction index -> v1 move string (y-axis flipped vs original).
INTERNAL_TO_V1 = {
    UP: "down",     # original UP means y-1; in v1 that is "down"
    LEFT: "left",
    DOWN: "up",     # original DOWN means y+1; in v1 that is "up"
    RIGHT: "right",
}

INITIAL_FEEDING = 3


# ------------------------------------------------------------------
# v1 -> internal data adaptation
# ------------------------------------------------------------------
def _adapt(game_state):
    """Convert a v1 game_state dict into the loose structure the ported
    logic expects: a namespace-like dict with width/height/turn/food/snakes/you
    where each snake has body as a list of {x,y} and a numeric length."""
    board = game_state["board"]
    you = game_state["you"]

    data = {
        "width": board["width"],
        "height": board["height"],
        "turn": game_state.get("turn", 0),
        "food": list(board.get("food", [])),
        "snakes": [],
        "you": None,
    }
    for snake in board.get("snakes", []):
        s = {
            "id": snake["id"],
            "length": snake.get("length", len(snake["body"])),
            "body": list(snake["body"]),
        }
        data["snakes"].append(s)
        if snake["id"] == you["id"]:
            data["you"] = s
    if data["you"] is None:
        data["you"] = {
            "id": you["id"],
            "length": you.get("length", len(you["body"])),
            "body": list(you["body"]),
        }
    return data


def get_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_coords(o):
    return (o["x"], o["y"])


def current_location(data):
    head = data["you"]["body"][0]
    return (head["x"], head["y"])


def get_tail(data):
    body = data["you"]["body"]
    return get_coords(body[-1])


def biggest(data):
    my_id = data["you"]["id"]
    my_length = data["you"]["length"]
    longest_length = 0
    for snake in data["snakes"]:
        if my_id != snake["id"]:
            if snake["length"] > longest_length:
                longest_length = snake["length"]
    if longest_length >= my_length:
        return False
    return True


def set_health_min(data):
    board_height = data["height"]
    board_width = data["width"]
    health_board = max(board_height, board_width) * 2
    health_length = data["you"]["length"]
    if health_length > health_board:
        return health_length
    return health_board


def build_map(data):
    board_height = data["height"]
    board_width = data["width"]
    my_id = data["you"]["id"]
    my_length = data["you"]["length"]
    # grid indexed [x][y]
    grid = [[SPACE for _col in range(board_height)] for _row in range(board_width)]

    # food
    for food in data["food"]:
        grid[food["x"]][food["y"]] = FOOD

    # snakes
    for snake in data["snakes"]:
        for segment in snake["body"]:
            grid[segment["x"]][segment["y"]] = SNAKE_BODY
        # clear tail unless snake just ate (tail == second-to-last)
        body = snake["body"]
        if len(body) >= 2 and body[-1] != body[-2]:
            tempX = body[-1]["x"]
            tempY = body[-1]["y"]
            grid[tempX][tempY] = SPACE
        # don't mark own head / own danger zones
        if snake["id"] == my_id:
            continue
        head = get_coords(body[0])
        grid[head[0]][head[1]] = ENEMY_HEAD
        head_zone = DANGER
        if snake["length"] < my_length:
            head_zone = KILL_ZONE
        # NOTE: original bounds checks intentionally skip board edges; reproduced.
        if head[1] + 1 < board_height - 1:
            if grid[head[0]][head[1] + 1] < head_zone:
                grid[head[0]][head[1] + 1] = head_zone
        if head[1] - 1 > 0:
            if grid[head[0]][head[1] - 1] < head_zone:
                grid[head[0]][head[1] - 1] = head_zone
        if head[0] - 1 > 0:
            if grid[head[0] - 1][head[1]] < head_zone:
                grid[head[0] - 1][head[1]] = head_zone
        if head[0] + 1 < board_width - 1:
            if grid[head[0] + 1][head[1]] < head_zone:
                grid[head[0] + 1][head[1]] = head_zone
    return grid


def closest_food(grid, data):
    my_location = current_location(data)
    close_food = None
    close_distance = 9999
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == FOOD:
                food = [i, j]
                distance = get_distance(my_location, food)
                if distance < close_distance:
                    close_food = food
                    close_distance = distance
    return close_food


class Cell:
    def __init__(self, x, y, board_width, board_height):
        self.f = 0
        self.g = 0
        self.h = 0
        self.x = x
        self.y = y
        self.state = 0
        self.neighbors = []
        self.previous = None
        if self.x < board_width - 1:
            self.neighbors.append([self.x + 1, self.y])
        if self.x > 0:
            self.neighbors.append([self.x - 1, self.y])
        if self.y < board_height - 1:
            self.neighbors.append([self.x, self.y + 1])
        if self.y > 0:
            self.neighbors.append([self.x, self.y - 1])


def build_astar_grid(data, grid):
    w = data["width"]
    h = data["height"]
    astar_grid = [[Cell(row, col, w, h) for col in range(h)] for row in range(w)]
    for i in range(w):
        for j in range(h):
            astar_grid[i][j].state = grid[i][j]
    return astar_grid


def valid_move(d, grid, data):
    board_height = data["height"]
    board_width = data["width"]
    current = current_location(data)
    if d == UP:
        if current[1] - 1 < 0:
            return False
        return grid[current[0]][current[1] - 1] <= DANGER
    if d == LEFT:
        if current[0] - 1 < 0:
            return False
        return grid[current[0] - 1][current[1]] <= DANGER
    if d == DOWN:
        if current[1] + 1 > board_height - 1:
            return False
        return grid[current[0]][current[1] + 1] <= DANGER
    if d == RIGHT:
        if current[0] + 1 > board_width - 1:
            return False
        return grid[current[0] + 1][current[1]] <= DANGER
    return True


def look_ahead(move, grid, data):
    board_height = data["height"]
    board_width = data["width"]
    area = 0
    current = current_location(data)
    given_move_coords = list(current)
    if move == UP:
        given_move_coords = [current[0], current[1] - 1]
    elif move == DOWN:
        given_move_coords = [current[0], current[1] + 1]
    elif move == LEFT:
        given_move_coords = [current[0] - 1, current[1]]
    elif move == RIGHT:
        given_move_coords = [current[0] + 1, current[1]]
    move_queue = [given_move_coords]
    checked_moves = [list(current)]
    current_l = list(current)
    while move_queue:
        for next_move in list(move_queue):
            area += 1
            move_queue.remove(next_move)
            checked_moves.append(next_move)
            neighbor_up = [next_move[0], next_move[1] - 1]
            if neighbor_up != current_l and neighbor_up not in checked_moves and neighbor_up not in move_queue:
                if neighbor_up[1] >= 0:
                    if grid[neighbor_up[0]][neighbor_up[1]] <= DANGER:
                        move_queue.append(neighbor_up)
            neighbor_down = [next_move[0], next_move[1] + 1]
            if neighbor_down != current_l and neighbor_down not in checked_moves and neighbor_down not in move_queue:
                if neighbor_down[1] < board_height:
                    if grid[neighbor_down[0]][neighbor_down[1]] <= DANGER:
                        move_queue.append(neighbor_down)
            neighbor_left = [next_move[0] - 1, next_move[1]]
            if neighbor_left != current_l and neighbor_left not in checked_moves and neighbor_left not in move_queue:
                if neighbor_left[0] >= 0:
                    if grid[neighbor_left[0]][neighbor_left[1]] <= DANGER:
                        move_queue.append(neighbor_left)
            neighbor_right = [next_move[0] + 1, next_move[1]]
            if neighbor_right != current_l and neighbor_right not in checked_moves and neighbor_right not in move_queue:
                if neighbor_right[0] < board_width:
                    if grid[neighbor_right[0]][neighbor_right[1]] <= DANGER:
                        move_queue.append(neighbor_right)
    return area


def move_contains_tail(move, grid, data):
    board_height = data["height"]
    board_width = data["width"]
    tail = get_coords(data["you"]["body"][-1])
    current = current_location(data)
    contains_tail = False
    given_move_coords = list(current)
    if move == UP:
        given_move_coords = [current[0], current[1] - 1]
    elif move == DOWN:
        given_move_coords = [current[0], current[1] + 1]
    elif move == LEFT:
        given_move_coords = [current[0] - 1, current[1]]
    elif move == RIGHT:
        given_move_coords = [current[0] + 1, current[1]]
    move_queue = [given_move_coords]
    checked_moves = [list(current)]
    current_l = list(current)
    while move_queue:
        for next_move in list(move_queue):
            if tail[0] == next_move[0] and tail[1] == next_move[1]:
                contains_tail = True
            move_queue.remove(next_move)
            checked_moves.append(next_move)
            neighbor_up = [next_move[0], next_move[1] - 1]
            if neighbor_up != current_l and neighbor_up not in checked_moves and neighbor_up not in move_queue:
                if neighbor_up[1] >= 0:
                    if grid[neighbor_up[0]][neighbor_up[1]] <= DANGER:
                        move_queue.append(neighbor_up)
            neighbor_down = [next_move[0], next_move[1] + 1]
            if neighbor_down != current_l and neighbor_down not in checked_moves and neighbor_down not in move_queue:
                if neighbor_down[1] < board_height:
                    if grid[neighbor_down[0]][neighbor_down[1]] <= DANGER:
                        move_queue.append(neighbor_down)
            neighbor_left = [next_move[0] - 1, next_move[1]]
            if neighbor_left != current_l and neighbor_left not in checked_moves and neighbor_left not in move_queue:
                if neighbor_left[0] >= 0:
                    if grid[neighbor_left[0]][neighbor_left[1]] <= DANGER:
                        move_queue.append(neighbor_left)
            neighbor_right = [next_move[0] + 1, next_move[1]]
            if neighbor_right != current_l and neighbor_right not in checked_moves and neighbor_right not in move_queue:
                if neighbor_right[0] < board_width:
                    if grid[neighbor_right[0]][neighbor_right[1]] <= DANGER:
                        move_queue.append(neighbor_right)
    return contains_tail


def calculate_direction(a, b, grid, data):
    x = a[0] - b[0]
    y = a[1] - b[1]
    direction = 0
    if x < 0:
        direction = RIGHT
    elif x > 0:
        direction = LEFT
    elif y < 0:
        direction = DOWN
    count = 0
    if not valid_move(direction, grid, data):
        if count == 3:
            return direction
        count += 1
        direction += 1
        if direction == 4:
            direction = 0
    return direction


def best_move(reccommended_move, data, grid):
    board_height = data["height"]
    board_width = data["width"]
    reg_moves = []
    danger_moves = []
    kill_moves = []
    current = current_location(data)

    # collect viable moves (grid value <= DANGER, on board)
    if current[1] - 1 >= 0 and grid[current[0]][current[1] - 1] <= DANGER:
        reg_moves.append(UP)
    if current[1] + 1 < board_height and grid[current[0]][current[1] + 1] <= DANGER:
        reg_moves.append(DOWN)
    if current[0] - 1 >= 0 and grid[current[0] - 1][current[1]] <= DANGER:
        reg_moves.append(LEFT)
    if current[0] + 1 < board_width and grid[current[0] + 1][current[1]] <= DANGER:
        reg_moves.append(RIGHT)

    if reg_moves:
        for move in list(reg_moves):
            if move == UP:
                cell = grid[current[0]][current[1] - 1]
            elif move == DOWN:
                cell = grid[current[0]][current[1] + 1]
            elif move == LEFT:
                cell = grid[current[0] - 1][current[1]]
            else:  # RIGHT
                cell = grid[current[0] + 1][current[1]]
            if cell == DANGER:
                reg_moves.remove(move)
                danger_moves.append(move)
            elif cell == KILL_ZONE:
                reg_moves.remove(move)
                kill_moves.append(move)
    else:
        return reccommended_move  # suicide

    if kill_moves:
        if len(kill_moves) >= 3 and reccommended_move in kill_moves:
            return reccommended_move
        best = reccommended_move
        best_area = 0
        if valid_move(reccommended_move, grid, data):
            best = reccommended_move
            best_area = look_ahead(reccommended_move, grid, data)
        for move in kill_moves:
            if move_contains_tail(move, grid, data):
                return move
            new_area = look_ahead(move, grid, data)
            if new_area > best_area:
                best_area = new_area
                best = move
        return best

    elif reg_moves:
        if len(reg_moves) >= 3 and reccommended_move in reg_moves:
            return reccommended_move
        best = reccommended_move
        best_area = 0
        if valid_move(reccommended_move, grid, data):
            best = reccommended_move
            best_area = look_ahead(reccommended_move, grid, data)
        for move in reg_moves:
            new_area = look_ahead(move, grid, data)
            if new_area > best_area:
                best_area = new_area
                best = move
        return best

    elif danger_moves:
        if len(danger_moves) >= 3:
            return reccommended_move
        best = reccommended_move
        best_area = 0
        if valid_move(reccommended_move, grid, data):
            best = reccommended_move
            best_area = look_ahead(reccommended_move, grid, data)
        for move in danger_moves:
            new_area = look_ahead(move, grid, data)
            if new_area > best_area:
                best_area = new_area
                best = move
        return best
    else:
        return reccommended_move  # suicide


def astar(data, grid, destination, mode):
    search_scores = build_astar_grid(data, grid)
    open_set = []
    closed_set = []
    start = current_location(data)
    start = [start[0], start[1]]

    if data["turn"] < INITIAL_FEEDING:
        cf = closest_food(grid, data)
        if cf is not None:
            destination = cf

    if destination is None:
        # no valid destination -> fall back to a defensive best move
        return best_move(DOWN, data, grid)

    open_set.append(start)
    while open_set:
        lowest_cell = [9999, 9999]
        lowest_f = 9999
        for cell in open_set:
            if search_scores[cell[0]][cell[1]].f < lowest_f:
                lowest_f = search_scores[cell[0]][cell[1]].f
                lowest_cell = cell

        if lowest_cell[0] == destination[0] and lowest_cell[1] == destination[1]:
            temp = lowest_cell
            # if destination is start itself, no path to retrace
            if temp[0] == start[0] and temp[1] == start[1]:
                return best_move(DOWN, data, grid)
            while (search_scores[temp[0]][temp[1]].previous is None or
                   search_scores[temp[0]][temp[1]].previous[0] != start[0] or
                   search_scores[temp[0]][temp[1]].previous[1] != start[1]):
                prev = search_scores[temp[0]][temp[1]].previous
                if prev is None:
                    break
                temp = prev
            next_move = calculate_direction(start, temp, grid, data)
            return next_move

        current = lowest_cell
        current_cell = search_scores[current[0]][current[1]]
        open_set.remove(lowest_cell)
        closed_set.append(current)

        for neighbor in search_scores[current[0]][current[1]].neighbors:
            neighbor_cell = search_scores[neighbor[0]][neighbor[1]]
            if neighbor[0] == destination[0] and neighbor[1] == destination[1]:
                neighbor_cell.previous = current
                temp = neighbor
                while (search_scores[temp[0]][temp[1]].previous is None or
                       search_scores[temp[0]][temp[1]].previous[0] != start[0] or
                       search_scores[temp[0]][temp[1]].previous[1] != start[1]):
                    prev = search_scores[temp[0]][temp[1]].previous
                    if prev is None:
                        break
                    temp = prev
                next_move = calculate_direction(start, temp, grid, data)
                return best_move(next_move, data, grid)
            if neighbor_cell.state < SNAKE_BODY:
                if neighbor not in closed_set:
                    temp_g = current_cell.g + 1
                    shorter = True
                    if neighbor in open_set:
                        if temp_g > neighbor_cell.g:
                            shorter = False
                    else:
                        open_set.append(neighbor)
                    if shorter:
                        neighbor_cell.g = temp_g
                        neighbor_cell.h = get_distance(neighbor, destination)
                        neighbor_cell.f = neighbor_cell.g + neighbor_cell.h
                        neighbor_cell.previous = current

    # open set empty, no path
    move = DOWN
    if mode == "food":
        tail = get_tail(data)
        return astar(data, grid, [tail[0], tail[1]], "my_tail")
    return best_move(move, data, grid)


def hungry(data):
    grid = build_map(data)
    close_food = closest_food(grid, data)
    return astar(data, grid, close_food, "food")


def kill_time(data):
    grid = build_map(data)
    tail = get_tail(data)
    return astar(data, grid, [tail[0], tail[1]], "my_tail")


# ------------------------------------------------------------------
# Robustness fallback: always return a legal in-bounds, non-body move.
# Tails are enterable (they move). Body cells (except moving tails) are blocked.
# ------------------------------------------------------------------
def _safe_fallback(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    blocked = set()
    for snake in board.get("snakes", []):
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            # last segment is a tail that will move away, unless the snake just ate
            if i == n - 1 and n >= 2 and body[-1] != body[-2]:
                continue
            blocked.add((seg["x"], seg["y"]))

    candidates = [
        ("up", hx, hy + 1),
        ("down", hx, hy - 1),
        ("left", hx - 1, hy),
        ("right", hx + 1, hy),
    ]
    for name, nx, ny in candidates:
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
            return {"move": name}
    # nothing safe; pick any in-bounds direction
    for name, nx, ny in candidates:
        if 0 <= nx < w and 0 <= ny < h:
            return {"move": name}
    return {"move": "up"}


def _is_legal(move_name, game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = game_state["you"]["body"][0]
    hx, hy = head["x"], head["y"]
    delta = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
    if move_name not in delta:
        return False
    dx, dy = delta[move_name]
    nx, ny = hx + dx, hy + dy
    if not (0 <= nx < w and 0 <= ny < h):
        return False
    # not into any snake body cell (excluding a moving tail)
    for snake in board.get("snakes", []):
        body = snake["body"]
        n = len(body)
        for i, seg in enumerate(body):
            if i == n - 1 and n >= 2 and body[-1] != body[-2]:
                continue
            if seg["x"] == nx and seg["y"] == ny:
                return False
    return True


# ------------------------------------------------------------------
# Battlesnake v1 handlers
# ------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "tyrelh",
        "color": "#27cbf0",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        data = _adapt(game_state)
        health = game_state["you"].get("health", 100)
        survival_min = set_health_min(data)

        if health < survival_min:
            direction = hungry(data)
        elif not biggest(data):
            direction = hungry(data)
        else:
            direction = kill_time(data)

        if direction is None:
            return _safe_fallback(game_state)

        move_name = INTERNAL_TO_V1.get(direction)
        if move_name is None or not _is_legal(move_name, game_state):
            return _safe_fallback(game_state)
        return {"move": move_name}
    except Exception:
        try:
            return _safe_fallback(game_state)
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
