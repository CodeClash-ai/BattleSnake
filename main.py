"""CodeClash port of tyrelh/battlesnake2019 (https://github.com/tyrelh/battlesnake2019).

Original: JavaScript/NodeJS (2019), by tyrelh. A grid + A* + flood-fill bot with
kill/danger-zone marking. Faithful reimplementation of app/{grid,search,move,
target,self,main}.js.

COORDINATE NOTE. The 2019 code operates on a grid indexed grid[y][x] where the
2019 API used a TOP-LEFT origin: internal "up" == y-1. The current v1 API uses a
BOTTOM-LEFT origin: up == y+1. To keep every piece of the original scoring logic
byte-for-byte faithful, we build and search the grid using the raw v1 coordinates
(grid[y][x]) exactly as the JS did, then remap ONLY the final internal move index
to the correct v1 direction string:

    internal UP   (0, y-1) -> v1 "down"
    internal DOWN (1, y+1) -> v1 "up"
    internal LEFT (2, x-1) -> v1 "left"
    internal RIGHT(3, x+1) -> v1 "right"

All logic is wrapped so we never crash and always return an in-bounds, non-body
move (tails are enterable). Pure stdlib.
"""

import math

# ---------------------------------------------------------------------------
# keys.js
# ---------------------------------------------------------------------------
KILL_ZONE = 0
SPACE = 1
TAIL = 2
FOOD = 3
FUTURE_2 = 4
WALL_NEAR = 5
WARNING = 6
SMALL_DANGER = 7
DANGER = 8
SNAKE_BODY = 9
YOUR_BODY = 10
SMALL_HEAD = 11
ENEMY_HEAD = 12

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# internal-move-index -> v1 direction string (y axis flipped vs. 2019 API)
INTERNAL_TO_V1 = {UP: "down", DOWN: "up", LEFT: "left", RIGHT: "right"}

# ---------------------------------------------------------------------------
# params.js
# ---------------------------------------------------------------------------
INITIAL_FEEDING = 10
SURVIVAL_MIN = 47
LONG_GAME_ENDURANCE = 80
INITIAL_TIME_KILL = 0
WALL_NEAR_BASE_MOVE_MULTIPLIER = 12
WALL_NEAR_FILL_MULTIPLIER = 0.05
KILL_ZONE_BASE_MOVE_MULTIPLIER = 3.5
FEEDING_URGENCY_MULTIPLIER = 0.32

ASTAR_SUCCESS = 9.3
ENEMY_DISTANCE = 1.9
WALL_DISTANCE = 2.1
BASE_KILL_ZONE = 2
BASE_FOOD = 0.8
BASE_TAIL = 8.2
BASE_SPACE = 0.36
BASE_WALL_NEAR = -1.1
BASE_WARNING = -2.6
BASE_SMALL_DANGER = -7.0
BASE_DANGER = -10.0
BASE_ENEMY_HEAD = -11
FORGET_ABOUT_IT = -100
COIL = 5


# ---------------------------------------------------------------------------
# grid.js
# ---------------------------------------------------------------------------
def get_distance(a, b):
    return abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])


def init_grid(width, height, fill_value):
    return [[fill_value for _ in range(width)] for _ in range(height)]


def copy_grid(grid):
    return [row[:] for row in grid]


def same_cell(a, b):
    return a["x"] == b["x"] and a["y"] == b["y"]


def out_of_bounds(pos, grid):
    x = pos["x"]
    y = pos["y"]
    try:
        if x < 0 or y < 0 or y >= len(grid) or x >= len(grid[0]):
            return True
        return False
    except Exception:
        return True


def on_perimeter(pos, grid):
    try:
        if (pos["x"] == 0 or pos["x"] == len(grid[0]) - 1
                or pos["y"] == 0 or pos["y"] == len(grid) - 1):
            return True
    except Exception:
        pass
    return False


def near_perimeter(pos, grid):
    try:
        if (pos["x"] == 1 or pos["x"] == len(grid[0]) - 2
                or pos["y"] == 1 or pos["y"] == len(grid) - 2):
            return True
    except Exception:
        pass
    return False


def build_grid(data):
    board = data["board"]
    self = data["you"]
    grid = init_grid(board["width"], board["height"], SPACE)

    # mark edges WALL_NEAR
    try:
        for y in range(board["height"]):
            grid[y][0] = WALL_NEAR
            grid[y][board["width"] - 1] = WALL_NEAR
        for x in range(board["width"]):
            grid[0][x] = WALL_NEAR
            grid[board["height"] - 1][x] = WALL_NEAR
    except Exception:
        pass

    # fill FOOD
    try:
        for f in board["food"]:
            grid[f["y"]][f["x"]] = FOOD
    except Exception:
        pass

    try:
        # fill snake body / head cells
        for snake in board["snakes"]:
            body = snake["body"]
            for seg in body:
                if snake["id"] == self["id"]:
                    grid[seg["y"]][seg["x"]] = YOUR_BODY
                else:
                    grid[seg["y"]][seg["x"]] = SNAKE_BODY

            head = body[0]
            danger_snake = len(body) >= len(self["body"])
            if snake["id"] != self["id"]:
                if danger_snake:
                    grid[head["y"]][head["x"]] = ENEMY_HEAD
                else:
                    grid[head["y"]][head["x"]] = SMALL_HEAD

            # tail is enterable unless the snake just ate (about to grow)
            if data["turn"] > 1 and snake["health"] != 100:
                tail = body[len(body) - 1]
                grid[tail["y"]][tail["x"]] = TAIL

        # DANGER / SMALL_DANGER / KILL_ZONE zones around each enemy head
        for snake in board["snakes"]:
            if snake["id"] == self["id"]:
                continue
            body = snake["body"]
            head = body[0]
            head_zone = DANGER
            if len(self["body"]) == len(body):
                head_zone = SMALL_DANGER
            elif len(self["body"]) > len(body):
                head_zone = KILL_ZONE

            for offset in ({"x": 0, "y": -1}, {"x": 0, "y": 1},
                           {"x": -1, "y": 0}, {"x": 1, "y": 0}):
                pos = {"x": head["x"] + offset["x"], "y": head["y"] + offset["y"]}
                if not out_of_bounds(pos, grid) and grid[pos["y"]][pos["x"]] < DANGER:
                    grid[pos["y"]][pos["x"]] = head_zone

            for offset in ({"x": -1, "y": -1}, {"x": -2, "y": 0}, {"x": -1, "y": 1},
                           {"x": 0, "y": 2}, {"x": 1, "y": 1}, {"x": 2, "y": 0},
                           {"x": 1, "y": -1}, {"x": 0, "y": -2}):
                pos = {"x": head["x"] + offset["x"], "y": head["y"] + offset["y"]}
                if (not out_of_bounds(pos, grid)
                        and grid[pos["y"]][pos["x"]] <= WALL_NEAR
                        and grid[pos["y"]][pos["x"]] != FOOD):
                    grid[pos["y"]][pos["x"]] = FUTURE_2
    except Exception:
        pass

    return grid


def move_tails(moves, grid, data):
    try:
        you = data["you"]
        grid_copy = copy_grid(grid)
        for snake in data["board"]["snakes"]:
            body = snake["body"]
            for tail_offset in range(1, moves + 1):
                idx = len(body) - tail_offset
                if idx < 0:
                    continue
                grid_copy[body[idx]["y"]][body[idx]["x"]] = SPACE

            if snake["id"] == you["id"]:
                continue

            im_bigger = len(you["body"]) > len(body)
            head = body[0]
            head_zone = KILL_ZONE if im_bigger else DANGER
            for offset in ({"x": 0, "y": -1}, {"x": 0, "y": 1},
                           {"x": -1, "y": 0}, {"x": 1, "y": 0}):
                pos = {"x": head["x"] + offset["x"], "y": head["y"] + offset["y"]}
                if not out_of_bounds(pos, grid) and grid[pos["y"]][pos["x"]] < DANGER:
                    grid[pos["y"]][pos["x"]] = head_zone
            for offset in ({"x": -1, "y": -1}, {"x": -2, "y": 0}, {"x": -1, "y": 1},
                           {"x": 0, "y": 2}, {"x": 1, "y": 1}, {"x": 2, "y": 0},
                           {"x": 1, "y": -1}, {"x": 0, "y": -2}):
                pos = {"x": head["x"] + offset["x"], "y": head["y"] + offset["y"]}
                if (not out_of_bounds(pos, grid)
                        and grid[pos["y"]][pos["x"]] <= WALL_NEAR
                        and grid[pos["y"]][pos["x"]] != FOOD):
                    grid[pos["y"]][pos["x"]] = FUTURE_2
        return grid_copy
    except Exception:
        return grid


# ---------------------------------------------------------------------------
# self.js
# ---------------------------------------------------------------------------
def location(data):
    try:
        b = data["you"]["body"][0]
        return {"x": b["x"], "y": b["y"]}
    except Exception:
        return {"x": 0, "y": 0}


def tail_location(data):
    try:
        body = data["you"]["body"]
        i = len(body) - 1
        return {"x": body[i]["x"], "y": body[i]["y"]}
    except Exception:
        return {"x": 0, "y": 0}


def biggest_snake(data):
    try:
        me = data["you"]["id"]
        my_length = len(data["you"]["body"])
        for snake in data["board"]["snakes"]:
            if snake["id"] == me:
                continue
            if len(snake["body"]) >= my_length:
                return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# target.js
# ---------------------------------------------------------------------------
def closest_target(grid, start_pos, target_type):
    try:
        closest = None
        closest_distance = 9999
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == target_type:
                    target = {"x": j, "y": i}
                    distance = get_distance(start_pos, target)
                    if distance < closest_distance:
                        closest = target
                        closest_distance = distance
        return closest
    except Exception:
        return None


def closest_food(grid, start_pos):
    return closest_target(grid, start_pos, FOOD)


# ---------------------------------------------------------------------------
# search.js
# ---------------------------------------------------------------------------
def apply_move_to_pos(move_dir, pos):
    if move_dir == UP:
        return {"x": pos["x"], "y": pos["y"] - 1}
    if move_dir == DOWN:
        return {"x": pos["x"], "y": pos["y"] + 1}
    if move_dir == LEFT:
        return {"x": pos["x"] - 1, "y": pos["y"]}
    if move_dir == RIGHT:
        return {"x": pos["x"] + 1, "y": pos["y"]}
    return {"x": 0, "y": 0}


def valid_move(direction, pos, grid):
    try:
        new_pos = apply_move_to_pos(direction, pos)
        if out_of_bounds(new_pos, grid):
            return False
        return grid[new_pos["y"]][new_pos["x"]] <= DANGER
    except Exception:
        return False


def calc_direction(a, b):
    x = a["x"] - b["x"]
    y = a["y"] - b["y"]
    direction = UP
    if x < 0:
        direction = RIGHT
    elif x > 0:
        direction = LEFT
    elif y < 0:
        direction = DOWN
    return direction


def distance_from_wall(pos, grid):
    try:
        y_up = pos["y"]
        y_down = (len(grid) - 1) - pos["y"]
        x_left = pos["x"]
        x_right = (len(grid[0]) - 1) - pos["x"]
        return max(min(x_left, x_right), min(y_up, y_down))
    except Exception:
        return 0


def distance_to_center(direction, start_pos, grid, data):
    try:
        if valid_move(direction, start_pos, grid):
            return distance_from_wall(apply_move_to_pos(direction, start_pos), grid)
    except Exception:
        pass
    return 0


def distance_to_enemy(direction, grid, data, type_=ENEMY_HEAD):
    try:
        you = data["you"]
        if valid_move(direction, you["body"][0], grid):
            closest = closest_target(grid, you["body"][0], type_)
            if closest is None:
                return 0
            return get_distance(closest, apply_move_to_pos(direction, you["body"][0]))
    except Exception:
        pass
    return 0


class Cell:
    __slots__ = ("f", "g", "h", "x", "y", "state", "neighbors", "previous")

    def __init__(self, x, y, width, height, state):
        self.f = 0
        self.g = 0
        self.h = 0
        self.x = x
        self.y = y
        self.state = state
        self.neighbors = []
        self.previous = {"x": 9998, "y": 9998}
        if self.x < width - 1:
            self.neighbors.append({"x": self.x + 1, "y": self.y})
        if self.x > 0:
            self.neighbors.append({"x": self.x - 1, "y": self.y})
        if self.y < height - 1:
            self.neighbors.append({"x": self.x, "y": self.y + 1})
        if self.y > 0:
            self.neighbors.append({"x": self.x, "y": self.y - 1})


def build_astar_grid(grid):
    return [[Cell(j, i, len(grid[0]), len(grid), grid[i][j])
             for j in range(len(grid[0]))] for i in range(len(grid))]


def array_includes_pair(arr, pair):
    for item in arr:
        if same_cell(item, pair):
            return True
    return False


def astar(grid, data, destination, search_type=FOOD, alternate_start_pos=None):
    try:
        search_scores = build_astar_grid(grid)
        open_set = []
        closed_set = []

        start = location(data) if alternate_start_pos is None else alternate_start_pos
        if data["turn"] < INITIAL_FEEDING:
            destination = closest_food(grid, start)
            search_type = FOOD
        if destination is None:
            destination = tail_location(data)
            search_type = TAIL
        if destination is None:
            return None

        open_set.append(start)
        while open_set:
            lowest_cell = {"x": 9999, "y": 9999}
            lowest_f = 9999
            for cell in open_set:
                sc = search_scores[cell["y"]][cell["x"]]
                if sc.f < lowest_f:
                    lowest_f = sc.f
                    lowest_cell = {"x": cell["x"], "y": cell["y"]}

            if same_cell(lowest_cell, destination):
                temp_cell = lowest_cell
                while (search_scores[temp_cell["y"]][temp_cell["x"]].previous["x"] != start["x"]
                       or search_scores[temp_cell["y"]][temp_cell["x"]].previous["y"] != start["y"]):
                    temp_cell = search_scores[temp_cell["y"]][temp_cell["x"]].previous
                return calc_direction(start, temp_cell)

            current = lowest_cell
            current_cell = search_scores[current["y"]][current["x"]]
            open_set = [p for p in open_set
                        if not (p["x"] == current["x"] and p["y"] == current["y"])]
            closed_set.append(current)

            for neighbor in search_scores[current["y"]][current["x"]].neighbors:
                neighbor_cell = search_scores[neighbor["y"]][neighbor["x"]]
                if same_cell(neighbor, destination):
                    neighbor_cell.previous = current
                    temp = neighbor
                    while (search_scores[temp["y"]][temp["x"]].previous["x"] != start["x"]
                           or search_scores[temp["y"]][temp["x"]].previous["y"] != start["y"]):
                        temp = search_scores[temp["y"]][temp["x"]].previous
                    return calc_direction(start, temp)

                if neighbor_cell.state < SNAKE_BODY:
                    if not array_includes_pair(closed_set, neighbor):
                        temp_g = current_cell.g + 1
                        shorter = True
                        if array_includes_pair(open_set, neighbor):
                            if temp_g > neighbor_cell.g:
                                shorter = False
                        else:
                            open_set.append(neighbor)
                        if shorter:
                            neighbor_cell.g = temp_g
                            neighbor_cell.h = get_distance(neighbor, destination)
                            neighbor_cell.f = neighbor_cell.g + neighbor_cell.h
                            neighbor_cell.previous = current
        return None
    except Exception:
        return None


def fill(direction, grid, data, constraints=None):
    if constraints is None:
        constraints = []
    try:
        you = data["you"]
        area = 0
        closed_grid = init_grid(len(grid[0]), len(grid), False)
        open_grid = init_grid(len(grid[0]), len(grid), False)
        open_stack = []

        def in_grid(pos, grd):
            try:
                return grd[pos["y"]][pos["x"]]
            except Exception:
                return None

        def add_to_open(pos):
            try:
                if (not out_of_bounds(pos, grid) and not in_grid(pos, closed_grid)
                        and not in_grid(pos, open_grid)):
                    if in_grid(pos, grid) <= DANGER:
                        for c in constraints:
                            if area == 0 and (in_grid(pos, grid) == KILL_ZONE
                                              or in_grid(pos, grid) == FUTURE_2):
                                break
                            if in_grid(pos, grid) == c:
                                return
                        open_stack.append(pos)
                        open_grid[pos["y"]][pos["x"]] = True
            except Exception:
                pass

        def remove_from_open():
            if not open_stack:
                return False
            pos = open_stack.pop()
            if not pos:
                return False
            open_grid[pos["y"]][pos["x"]] = False
            return pos

        def add_to_closed(pos):
            closed_grid[pos["y"]][pos["x"]] = True

        current = you["body"][0]
        given_move_pos = {"x": current["x"], "y": current["y"]}
        if direction == UP:
            given_move_pos["y"] -= 1
        elif direction == DOWN:
            given_move_pos["y"] += 1
        elif direction == LEFT:
            given_move_pos["x"] -= 1
        elif direction == RIGHT:
            given_move_pos["x"] += 1
        add_to_open(given_move_pos)
        add_to_closed(current)

        enemy_heads = kill_zones = tails = foods = warnings = walls = 0

        while open_stack:
            next_move = remove_from_open()
            if not next_move:
                break
            add_to_closed(next_move)
            v = in_grid(next_move, grid)
            if v == ENEMY_HEAD:
                enemy_heads += 1
            elif v == TAIL:
                tails += 1
            elif v == KILL_ZONE:
                kill_zones += 1
            elif v == FOOD:
                foods += 1
            elif v == WALL_NEAR:
                walls += 1
            elif v == WARNING:
                warnings += 1
            area += 1

            add_to_open({"x": next_move["x"], "y": next_move["y"] - 1})
            add_to_open({"x": next_move["x"], "y": next_move["y"] + 1})
            add_to_open({"x": next_move["x"] - 1, "y": next_move["y"]})
            add_to_open({"x": next_move["x"] + 1, "y": next_move["y"]})

        score = 0
        score += area * BASE_SPACE
        score += tails * BASE_TAIL
        score += foods * BASE_FOOD
        score += enemy_heads * BASE_ENEMY_HEAD
        score += kill_zones * BASE_KILL_ZONE
        score += warnings * BASE_WARNING
        score += walls * (BASE_WALL_NEAR * WALL_NEAR_FILL_MULTIPLIER)

        if area < len(you["body"]) and tails < 1:
            score = math.floor(score / 2)
        return score
    except Exception:
        return 0


def get_enemy_locations(data):
    try:
        you = data["you"]
        return [s["body"][0] for s in data["board"]["snakes"] if s["id"] != you["id"]]
    except Exception:
        return []


def get_enemy_move_locations(pos, grid):
    try:
        return [apply_move_to_pos(m, pos) for m in range(4) if valid_move(m, pos, grid)]
    except Exception:
        return []


def edge_fill_from_enemy_to_you(enemy, grid_copy, grid, data):
    try:
        your_head = location(data)
        for enemy_move in get_enemy_move_locations(enemy, grid):
            closed_grid = init_grid(len(grid[0]), len(grid), False)
            open_grid = init_grid(len(grid[0]), len(grid), False)
            open_stack = []

            def in_grid(pos, grd):
                try:
                    return grd[pos["y"]][pos["x"]]
                except Exception:
                    return False

            def add_to_open(pos):
                try:
                    if (not out_of_bounds(pos, grid) and not in_grid(pos, closed_grid)
                            and not in_grid(pos, open_grid)):
                        if in_grid(pos, grid) <= DANGER and on_perimeter(pos, grid):
                            open_stack.append(pos)
                            open_grid[pos["y"]][pos["x"]] = True
                except Exception:
                    pass

            def remove_from_open():
                if not open_stack:
                    return False
                pos = open_stack.pop()
                if not pos:
                    return False
                open_grid[pos["y"]][pos["x"]] = False
                return pos

            def add_to_closed(pos):
                closed_grid[pos["y"]][pos["x"]] = True

            add_to_open(enemy_move)
            edge_spaces = []
            found_me = False
            fail = False
            next_move = None

            while open_stack and not found_me and not fail:
                next_move = remove_from_open()
                if not next_move:
                    break
                edge_spaces.append(next_move)
                add_to_closed(next_move)
                for neighbor in ({"x": next_move["x"], "y": next_move["y"] - 1},
                                 {"x": next_move["x"], "y": next_move["y"] + 1},
                                 {"x": next_move["x"] - 1, "y": next_move["y"]},
                                 {"x": next_move["x"] + 1, "y": next_move["y"]}):
                    if not out_of_bounds(neighbor, grid):
                        if same_cell(your_head, neighbor):
                            found_me = True
                            break
                        if not on_perimeter(neighbor, grid):
                            if in_grid(neighbor, grid) < SNAKE_BODY:
                                fail = True
                                break
                        add_to_open(neighbor)

            if fail:
                return {"grid": grid_copy, "move": None}
            if found_me:
                for space in edge_spaces:
                    grid_copy[space["y"]][space["x"]] = KILL_ZONE
                return {"grid": grid_copy, "move": next_move}
    except Exception:
        pass
    return {"grid": grid_copy, "move": None}


def preprocess_grid(grid, data):
    try:
        if near_perimeter(location(data), grid):
            grid_copy = copy_grid(grid)
            for enemy in get_enemy_locations(data):
                if on_perimeter(enemy, grid):
                    result = edge_fill_from_enemy_to_you(enemy, grid_copy, grid, data)
                    grid_copy = result["grid"]
            return grid_copy
    except Exception:
        pass
    return grid


def get_kill_zones_in_order_of_distance_from_wall(grid, target):
    try:
        spots = []
        for direction, spot in ((UP, {"x": target["x"], "y": target["y"] - 1}),
                                (DOWN, {"x": target["x"], "y": target["y"] + 1}),
                                (LEFT, {"x": target["x"] - 1, "y": target["y"]}),
                                (RIGHT, {"x": target["x"] + 1, "y": target["y"]})):
            if not out_of_bounds(spot, grid) and valid_move(direction, target, grid):
                spots.append({"pos": spot, "distance": distance_from_wall(spot, grid)})
        spots.sort(key=lambda s: s["distance"], reverse=True)
        kill_zones = [s["pos"] for s in spots]
        return kill_zones if kill_zones else None
    except Exception:
        return None


def get_future2_in_order_of_distance_from_wall(grid, target):
    try:
        spots = []
        for offset in ({"x": 0, "y": -2}, {"x": 1, "y": -1}, {"x": 2, "y": 0},
                       {"x": 1, "y": 1}, {"x": 0, "y": 2}, {"x": -1, "y": 1},
                       {"x": -2, "y": 0}, {"x": -1, "y": -1}):
            spot = {"x": target["x"] + offset["x"], "y": target["y"] + offset["y"]}
            # NOTE: faithful to original bug -> grid[spot.y][spot.y] (not [spot.x])
            if not out_of_bounds(spot, grid) and grid[spot["y"]][spot["y"]] == FUTURE_2:
                spots.append({"pos": spot, "distance": distance_from_wall(spot, grid)})
        spots.sort(key=lambda s: s["distance"], reverse=True)
        future2s = [s["pos"] for s in spots]
        return future2s if future2s else None
    except Exception:
        return None


def close_accessable_kill_zone_far_from_wall(grid, data):
    try:
        you = data["you"]
        grid_copy = copy_grid(grid)
        guard = 0
        while guard < 200:
            guard += 1
            target = closest_target(grid_copy, you["body"][0], SMALL_HEAD)
            if target is None:
                return None
            kill_zones = get_kill_zones_in_order_of_distance_from_wall(grid, target)
            if kill_zones is not None:
                for kill_zone in kill_zones:
                    m = astar(grid, data, kill_zone, KILL_ZONE)
                    if m is not None:
                        return m
            grid_copy[target["y"]][target["x"]] = ENEMY_HEAD
    except Exception:
        pass
    return None


def close_accessable_future2_far_from_wall(grid, data):
    try:
        you = data["you"]
        grid_copy = copy_grid(grid)
        guard = 0
        while guard < 200:
            guard += 1
            target = closest_target(grid_copy, you["body"][0], SMALL_HEAD)
            if target is None:
                target = closest_target(grid_copy, you["body"][0], ENEMY_HEAD)
            if target is None:
                return None
            future2s = get_future2_in_order_of_distance_from_wall(grid, target)
            if future2s is not None:
                for future2 in future2s:
                    m = astar(grid, data, future2, FUTURE_2)
                    if m is not None:
                        return m
            grid_copy[target["y"]][target["x"]] = SNAKE_BODY
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# move.js
# ---------------------------------------------------------------------------
def base_score_for_board_position(x, y, grid):
    try:
        if out_of_bounds({"x": x, "y": y}, grid):
            return FORGET_ABOUT_IT
        v = grid[y][x]
        if v in (SPACE, TAIL, FUTURE_2):
            return BASE_SPACE
        if v == FOOD:
            return BASE_FOOD
        if v == KILL_ZONE:
            return BASE_KILL_ZONE * KILL_ZONE_BASE_MOVE_MULTIPLIER
        if v == WALL_NEAR:
            return BASE_WALL_NEAR * WALL_NEAR_BASE_MOVE_MULTIPLIER
        if v == WARNING:
            return BASE_WARNING
        if v == SMALL_DANGER:
            return BASE_SMALL_DANGER
        if v == DANGER:
            return BASE_DANGER
        return FORGET_ABOUT_IT
    except Exception:
        return FORGET_ABOUT_IT


def base_move_scores(grid, self):
    head = self["body"][0]
    scores = [0, 0, 0, 0]
    scores[UP] += base_score_for_board_position(head["x"], head["y"] - 1, grid)
    scores[DOWN] += base_score_for_board_position(head["x"], head["y"] + 1, grid)
    scores[LEFT] += base_score_for_board_position(head["x"] - 1, head["y"], grid)
    scores[RIGHT] += base_score_for_board_position(head["x"] + 1, head["y"], grid)
    return scores


def highest_score_move(scores):
    best_move = 0
    best_score = -9999
    for i in range(len(scores)):
        if scores[i] > best_score:
            best_score = scores[i]
            best_move = i
    return best_move


def get_fallback_move(grid, data):
    try:
        target = tail_location(data)
        move_dir = astar(grid, data, target, TAIL)
        grid_copy = copy_grid(grid)
        guard = 0
        while move_dir is None and guard < 200:
            guard += 1
            target = closest_food(grid_copy, location(data))
            if target is not None:
                grid_copy[target["y"]][target["x"]] = WARNING
                move_dir = astar(grid, data, target, FOOD)
            else:
                break
        if move_dir is not None:
            return {"move": move_dir, "score": ASTAR_SUCCESS / 5}
    except Exception:
        pass
    return {"move": None, "score": 0}


def coil(grid, data):
    try:
        tail_loc = tail_location(data)
        tail_distances = [0, 0, 0, 0]
        largest_distance = 0
        for m in range(4):
            next_move = apply_move_to_pos(m, location(data))
            if out_of_bounds(next_move, grid):
                continue
            if grid[next_move["y"]][next_move["x"]] >= SNAKE_BODY:
                continue
            current_distance = get_distance(tail_loc, next_move)
            if tail_distances[m] < current_distance:
                tail_distances[m] = current_distance
                if largest_distance < current_distance:
                    largest_distance = current_distance
        coil_scores = [0, 0, 0, 0]
        for m in range(4):
            if tail_distances[m] == largest_distance:
                coil_scores[m] += COIL
        return coil_scores
    except Exception:
        return []


def build_move(grid, data, move_dir, move_score=0):
    you = data["you"]
    scores = base_move_scores(grid, you)
    try:
        if move_dir is None:
            fallback = get_fallback_move(grid, data)
            move_dir = fallback["move"]
            if move_dir is not None:
                scores[move_dir] += fallback["score"]
            else:
                coil_scores = coil(grid, data)
                for m in range(len(coil_scores)):
                    scores[m] += coil_scores[m]
        else:
            scores[move_dir] += move_score
    except Exception:
        pass

    # flood fill scores (now, 1 move ahead, 2 moves ahead)
    try:
        for m in range(4):
            scores[m] += fill(m, grid, data)
            grid_copy = move_tails(1, grid, data)
            scores[m] += fill(m, grid_copy, data, [KILL_ZONE, DANGER, WARNING])
            grid_copy = move_tails(2, grid, data)
            scores[m] += fill(m, grid_copy, data, [KILL_ZONE, DANGER, WARNING, FUTURE_2])
    except Exception:
        pass

    # farther from dangerous snake
    try:
        enemy_distances = [0, 0, 0, 0]
        largest_distance = 0
        largest_distance_move = 0
        unique = False
        for m in range(4):
            cd = distance_to_enemy(m, grid, data, ENEMY_HEAD)
            if enemy_distances[m] < cd:
                enemy_distances[m] = cd
                if largest_distance == cd:
                    unique = False
                elif largest_distance < cd:
                    largest_distance = cd
                    largest_distance_move = m
                    unique = True
        if unique:
            scores[largest_distance_move] += ENEMY_DISTANCE
    except Exception:
        pass

    # closer to killable snake
    try:
        enemy_distances = [9999, 9999, 9999, 9999]
        smallest_distance = 9999
        smallest_distance_move = 0
        unique = False
        for m in range(4):
            cd = distance_to_enemy(m, grid, data, KILL_ZONE)
            if cd == 0:
                continue
            if enemy_distances[m] > cd:
                enemy_distances[m] = cd
                if smallest_distance == cd:
                    unique = False
                elif smallest_distance > cd:
                    smallest_distance = cd
                    smallest_distance_move = m
                    unique = True
        if unique:
            scores[smallest_distance_move] += ENEMY_DISTANCE
    except Exception:
        pass

    # farther from wall
    try:
        center_distances = [0, 0, 0, 0]
        largest_distance = 0
        largest_distance_move = 0
        unique = False
        for m in range(4):
            cd = distance_to_center(m, location(data), grid, data)
            if center_distances[m] < cd:
                center_distances[m] = cd
                if largest_distance == cd:
                    unique = False
                elif largest_distance < cd:
                    largest_distance = cd
                    largest_distance_move = m
                    unique = True
        if unique:
            scores[largest_distance_move] += WALL_DISTANCE
    except Exception:
        pass

    return highest_score_move(scores)


def eat(grid, data):
    try:
        you = data["you"]
        my_head = location(data)
        health = you["health"]
        urgency_score = 110 - health
        if data["turn"] > INITIAL_FEEDING:
            urgency_score = round(urgency_score * FEEDING_URGENCY_MULTIPLIER)

        move_dir = None
        grid_copy = copy_grid(grid)
        try:
            target = closest_food(grid, my_head)
            if target is None:
                return build_move(grid, data, None, 0)
            move_dir = astar(grid, data, target, FOOD)
            guard = 0
            while move_dir is None and target is not None and guard < 200:
                guard += 1
                grid_copy[target["y"]][target["x"]] = DANGER
                target = closest_food(grid_copy, my_head)
                if target is None:
                    break
                move_dir = astar(grid, data, target, FOOD)
        except Exception:
            pass

        if move_dir is not None:
            return build_move(grid, data, move_dir, urgency_score)
        return build_move(grid, data, None, 0)
    except Exception:
        return build_move(grid, data, None, 0)


def hunt(grid, data):
    try:
        score = 0
        move_dir = close_accessable_kill_zone_far_from_wall(grid, data)
        if move_dir is not None:
            score = ASTAR_SUCCESS
        return build_move(grid, data, move_dir, score)
    except Exception:
        return build_move(grid, data, None, 0)


def kill_time(grid, data):
    return build_move(grid, data, None, 0)


# ---------------------------------------------------------------------------
# main.js decision logic
# ---------------------------------------------------------------------------
def decide_internal_move(data):
    grid = build_grid(data)
    grid = preprocess_grid(grid, data)

    health = data["you"]["health"]
    turn = data["turn"]
    move_dir = None

    min_health = SURVIVAL_MIN - math.floor(turn / LONG_GAME_ENDURANCE)
    if health < min_health or turn < INITIAL_FEEDING:
        move_dir = eat(grid, data)
    elif turn < INITIAL_TIME_KILL:
        move_dir = kill_time(grid, data)
    elif not biggest_snake(data):
        move_dir = eat(grid, data)
    elif biggest_snake(data):
        move_dir = hunt(grid, data)

    if move_dir is None:
        move_dir = eat(grid, data)
    if move_dir is None:
        move_dir = UP
    return move_dir


# ---------------------------------------------------------------------------
# Robust safety net: guarantee a legal v1 move.
# ---------------------------------------------------------------------------
def _v1_neighbor(head, direction):
    if direction == "up":
        return head["x"], head["y"] + 1
    if direction == "down":
        return head["x"], head["y"] - 1
    if direction == "left":
        return head["x"] - 1, head["y"]
    return head["x"] + 1, head["y"]


def _safe_v1_moves(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = game_state["you"]["body"][0]

    blocked = set()
    for snake in board["snakes"]:
        body = snake["body"]
        will_grow = snake.get("health", 0) == 100
        n = len(body)
        for i, seg in enumerate(body):
            if i == n - 1 and not will_grow and n > 1:
                continue  # tail vacates next turn
            blocked.add((seg["x"], seg["y"]))

    safe = []
    for d in ("up", "down", "left", "right"):
        nx, ny = _v1_neighbor(head, d)
        if nx < 0 or ny < 0 or nx >= w or ny >= h:
            continue
        if (nx, ny) in blocked:
            continue
        safe.append(d)
    return safe


# ---------------------------------------------------------------------------
# v1 API entry points
# ---------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "tyrelh",
        "color": "#9557E0",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return


def end(game_state):
    return


def move(game_state):
    chosen = None
    try:
        internal = decide_internal_move(game_state)
        chosen = INTERNAL_TO_V1.get(internal, "up")
    except Exception:
        chosen = None

    try:
        safe = _safe_v1_moves(game_state)
        if chosen not in safe:
            if safe:
                chosen = safe[0]
            elif chosen is None:
                chosen = "up"
    except Exception:
        if chosen is None:
            chosen = "up"

    if chosen is None:
        chosen = "up"
    return {"move": chosen}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
