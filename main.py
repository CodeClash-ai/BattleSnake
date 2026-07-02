"""
Port of FeistySnake-2019 (https://github.com/derekjbell/FeistySnake-2019,
originally authored by Tristan Giles / "tbgiles" and team) to the
CodeClash Battlesnake v1 API.

Original bot: Python + Flask, OLD Battlesnake API (top-left origin, y-down).
It builds an integer grid (1=open, 0=wall, -1=danger), picks one of three
states (attack / grow / defend) and moves via A* pathfinding + floodfill
space-checks, with tail-chasing and danger-square backups.

This file reproduces that logic. The only semantic remap is the coordinate
system: the v1 API uses a BOTTOM-LEFT origin with y-up, whereas the original
indexed grid[y][x] with y-down. We keep the grid semantics identical to the
original (grid[y][x], y increasing "down" in original terms) by using the raw
v1 y values directly as row indices, and only flip the up/down interpretation
of the final move letter to match v1's y-up convention.
"""

import math
import heapq
from collections import deque

infinity = float('inf')


# --------------------------------------------------------------------------
# A* pathfinding (faithful to astar.py)
# --------------------------------------------------------------------------
class AStar():
    def __init__(self, start, grid, width, height):
        self.start = start
        self.grid = grid
        self.height = height
        self.width = width

    class search_node():
        def __init__(self, position, fscore=infinity, gscore=infinity, parent=None):
            self.fscore = fscore
            self.gscore = gscore
            self.position = position
            self.parent = parent

        def __lt__(self, comparator):
            return self.fscore < comparator.fscore

    class search_node_maker(dict):
        def __missing__(self, node):
            newNode = AStar.search_node(node)
            self.__setitem__(node, newNode)
            return newNode

    def get_heuristic(self, end):
        (x1, y1) = self.start
        (x2, y2) = end
        return math.hypot(x2 - x1, y2 - y1)

    def get_node_neighbours(self, node):
        (x, y) = node
        return [(dx, dy) for (dx, dy) in
                [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                if 0 <= dx < self.width and 0 <= dy < self.height
                and self.grid[dy][dx] == 1]

    def get_path(self, endPoint):
        current = endPoint
        path = []
        while current.position != self.start:
            path.append(current.position)
            current = current.parent
        path.append(self.start)
        return list(reversed(path))

    def compute_path(self, end):
        openList = []
        current_search_node = AStar.search_node(self.start,
                                                fscore=self.get_heuristic(end),
                                                gscore=0)
        node_maker = AStar.search_node_maker()
        heapq.heappush(openList, current_search_node)
        closedList = []
        while openList:
            current_search_node = heapq.heappop(openList)
            if current_search_node.position == end:
                return self.get_path(current_search_node)
            else:
                closedList.append(current_search_node)
                neighbours = [node_maker[tocheck] for tocheck in
                              self.get_node_neighbours(current_search_node.position)]
                for neighbour in neighbours:
                    newGscore = current_search_node.gscore + 1
                    if neighbour in openList and newGscore < neighbour.gscore:
                        openList.remove(neighbour)
                    if newGscore < neighbour.gscore and neighbour in closedList:
                        closedList.remove(neighbour)
                    if neighbour not in openList and neighbour not in closedList:
                        neighbour.gscore = newGscore
                        neighbour.fscore = neighbour.gscore + self.get_heuristic(neighbour.position)
                        neighbour.parent = current_search_node
                        heapq.heappush(openList, neighbour)
                    heapq.heapify(openList)
        return None


# --------------------------------------------------------------------------
# FloodFill (faithful to floodfill.py)
# --------------------------------------------------------------------------
class FloodFill():
    def __init__(self, map):
        self.map = map[0]
        self.width = len(self.map[0])
        self.height = len(self.map)
        self.used = {}

    def calculate_one(self, square):
        self.used = {}
        self.false_map()
        return self.fill(square, self.map)

    def false_map(self):
        for y in range(0, self.height):
            for x in range(0, self.width):
                self.used[(x, y)] = False

    def fill(self, start, map):
        count = 0
        q = deque()
        curr = start
        # Guard: start must be a valid, open square.
        if not (0 <= start[0] < self.width and 0 <= start[1] < self.height):
            return 0
        q.append(curr)
        self.used[curr] = True
        count += 1
        while q:
            curr = q.popleft()
            for neighbour in self.get_neighbours(curr):
                if not self.used[neighbour]:
                    self.used[neighbour] = True
                    q.append(neighbour)
                    count += 1
        return count

    def get_neighbours(self, curr):
        up = (curr[0], curr[1] - 1)
        down = (curr[0], curr[1] + 1)
        left = (curr[0] - 1, curr[1])
        right = (curr[0] + 1, curr[1])
        return self.inbounds([up, down, left, right])

    def inbounds(self, neighbours):
        inb = []
        for neighbour in neighbours:
            x = neighbour[0]
            y = neighbour[1]
            if 0 <= x < self.width and 0 <= y < self.height and not self.used[neighbour]:
                if self.map[y][x] == 1:
                    inb.append(neighbour)
        return inb


# --------------------------------------------------------------------------
# Helper (faithful to helper.py)
# --------------------------------------------------------------------------
class Helper():
    def get_closest_food_dist(self, food_list, data):
        head_x = data["you"]["body"][0]["x"]
        head_y = data["you"]["body"][0]["y"]
        current_minimum = math.inf
        for pellet in food_list:
            d = self.get_crows_dist((head_x, head_y), pellet)
            if d < current_minimum:
                current_minimum = d
        return current_minimum

    def get_crows_dist(self, start, end):
        (x1, y1) = start
        (x2, y2) = end
        return abs(math.hypot(x2 - x1, y2 - y1))

    def get_move_letter(self, start, end):
        # NOTE: In the ORIGINAL bot the grid was y-down (top-left origin), so
        # delta_y > 0 meant "down" and delta_y < 0 meant "up". Under the v1 API
        # the board is y-up (bottom-left origin), so we FLIP those two here:
        # increasing grid-row/y => "up" in v1, decreasing => "down".
        current_x, current_y = start[0], start[1]
        next_x, next_y = end[0], end[1]
        delta_x = next_x - current_x
        delta_y = next_y - current_y
        if delta_x > 0:
            return 'right'
        elif delta_y > 0:
            return 'up'      # flipped (was 'down' in original y-down grid)
        elif delta_x < 0:
            return 'left'
        elif delta_y < 0:
            return 'down'    # flipped (was 'up' in original y-down grid)
        return 'up'

    def get_neighbors(self, node, lines, height, width):
        (x, y) = node
        potential_moves = [(nx, ny) for nx, ny in
                           [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                           if 0 <= nx < width and 0 <= ny < height and lines[ny][nx] == 1]
        if len(potential_moves) > 0:
            return self.sort_options_fill(potential_moves, lines)
        else:
            return None

    def get_backup_move(self, node, lines, height, width):
        (x, y) = node
        safe_moves = [(nx, ny) for nx, ny in
                      [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                      if 0 <= nx < width and 0 <= ny < height and lines[ny][nx] == 1]
        danger_moves = [(nx, ny) for nx, ny in
                        [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                        if 0 <= nx < width and 0 <= ny < height and lines[ny][nx] == -1]
        if len(safe_moves) > 0:
            return self.sort_options_fill(safe_moves, lines)
        elif len(danger_moves) > 0:
            return self.sort_options_fill(danger_moves, lines)
        else:
            return None

    def sort_options_fill(self, options, map):
        filler = FloodFill([map, []])
        list_with_area = []
        for entry in options:
            list_with_area.append([entry, filler.calculate_one(entry)])
        list_with_area.sort(key=lambda x: x[1])
        return_list = [x for [x, y] in list_with_area]
        return_list.reverse()
        return return_list

    def get_max_snake_length(self, data):
        my_snake_id = data["you"]["id"]
        current_max = 0
        for snake in data["board"]["snakes"]:
            if snake["id"] != my_snake_id:
                if len(snake["body"]) > current_max:
                    current_max = len(snake["body"])
        return current_max

    def is_good_move(self, location, map, my_snake_length):
        filler = FloodFill([map, []])
        available_space = filler.calculate_one(tuple(location))
        return available_space > my_snake_length


# --------------------------------------------------------------------------
# Setup (faithful to setup.py)
# --------------------------------------------------------------------------
class Setup():
    def __init__(self):
        self.helper = Helper()

    def grid_setup(self, data):
        food = data["board"]["food"]
        width = data["board"]["width"]
        height = data["board"]["height"]
        snakes = data["board"]["snakes"]
        my_snake_id = data["you"]["id"]
        my_snake_head = (data["you"]["body"][0]["x"], data["you"]["body"][0]["y"])

        # 1=open, 0=wall, -1=danger. Indexed grid[y][x].
        move_grid = [[1 for _ in range(width)] for _ in range(height)]

        # Food: sort by crow distance to head, keep the 5 closest as (x, y).
        unsorted_food_list = []
        for pellet in food:
            tp = (pellet["x"], pellet["y"])
            unsorted_food_list.append([tp, self.helper.get_crows_dist(tp, my_snake_head)])
        unsorted_food_list.sort(key=lambda x: x[1])
        food_grid = [x for [x, y] in unsorted_food_list][0:5]

        for snake in snakes:
            body = snake["body"]
            snake_id = snake["id"]

            # Danger zone around enemy heads.
            if snake_id != my_snake_id:
                head = body[0]
                head_x, head_y = head["x"], head["y"]
                top = head_y - 1
                bottom = head_y + 1
                left = head_x - 1
                right = head_x + 1
                if top >= 0 and move_grid[top][head_x] != 0:
                    move_grid[top][head_x] = -1
                if bottom < height and move_grid[bottom][head_x] != 0:
                    move_grid[bottom][head_x] = -1
                if left >= 0 and move_grid[head_y][left] != 0:
                    move_grid[head_y][left] = -1
                if right < width and move_grid[head_y][right] != 0:
                    move_grid[head_y][right] = -1

            # Every body cell is a wall.
            for point in body:
                move_grid[point["y"]][point["x"]] = 0

            # Tail becomes reachable-if-necessary (-1) unless the snake just ate.
            if snake["health"] < 100:
                move_grid[body[-1]["y"]][body[-1]["x"]] = -1

        return [move_grid, food_grid]


# --------------------------------------------------------------------------
# State: Attack (faithful to state_attack.py)
# --------------------------------------------------------------------------
class State_Attack():
    def __init__(self):
        self.helper = None

    def get_move(self, grid_data, data):
        self.height = data["board"]["height"]
        self.width = data["board"]["width"]
        self.head_x = data["you"]["body"][0]["x"]
        self.head_y = data["you"]["body"][0]["y"]
        self.my_snake_health = data["you"]["health"]
        self.my_snake_length = len(data["you"]["body"])
        self.pathfinder = AStar((self.head_x, self.head_y), grid_data[0], self.width, self.height)
        self.grid_data = grid_data
        self.data = data

        snakes = data["board"]["snakes"]
        target_snake_id = self.find_closest_snake_head(snakes)

        if self.my_snake_health < 40:
            return self.default_behaviour()
        if target_snake_id:
            return self.attack_snake_head(snakes, target_snake_id)
        else:
            return self.default_behaviour()

    def find_closest_snake_head(self, snakes):
        current_minimum = float('inf')
        current_id = None
        for snake in snakes:
            if snake["id"] == self.data["you"]["id"]:
                continue
            ex, ey = snake["body"][0]["x"], snake["body"][0]["y"]
            dist = self.helper.get_crows_dist((self.head_x, self.head_y), (ex, ey))
            if dist < current_minimum:
                current_minimum = dist
                current_id = snake["id"]
        return current_id

    def attack_snake_head(self, snakes, target_id):
        for snake in snakes:
            if snake["id"] == target_id:
                target_snake = snake["body"]
                target_position = self.get_danger_squares(target_snake)
                if target_position:
                    tx, ty = target_position[0], target_position[1]
                    old_val = self.grid_data[0][ty][tx]
                    self.grid_data[0][ty][tx] = 1
                    target_move = self.move_to_food([target_position])
                    self.grid_data[0][ty][tx] = old_val
                    return target_move
                else:
                    return self.default_behaviour()

    def get_danger_squares(self, target_snake):
        available_moves = []
        head_x, head_y = target_snake[0]["x"], target_snake[0]["y"]
        top = head_y - 1
        bottom = head_y + 1
        left = head_x - 1
        right = head_x + 1
        if top >= 0 and self.grid_data[0][top][head_x] != 0:
            available_moves.append((head_x, top))
        if bottom < self.height and self.grid_data[0][bottom][head_x] != 0:
            available_moves.append((head_x, bottom))
        if left >= 0 and self.grid_data[0][head_y][left] != 0:
            available_moves.append((left, head_y))
        if right < self.width and self.grid_data[0][head_y][right] != 0:
            available_moves.append((right, head_y))
        if available_moves:
            return available_moves[0]
        return None

    def move_to_food(self, food_list):
        current_minimum = float('inf')
        current_path = None
        for food in food_list:
            path = self.pathfinder.compute_path(tuple(food))
            if path:
                path = list(path)
                if len(path) < current_minimum:
                    current_minimum = len(path)
                    current_path = path
        if current_path and len(current_path) > 1 and \
                self.helper.is_good_move(list(current_path)[1], self.grid_data[0], self.my_snake_length):
            return self.helper.get_move_letter((self.head_x, self.head_y), list(current_path)[1])
        else:
            backup_moves = self.helper.get_backup_move((self.head_x, self.head_y),
                                                       self.grid_data[0], self.height, self.width)
            if backup_moves:
                return self.helper.get_move_letter((self.head_x, self.head_y), backup_moves[0])
            else:
                return 'up'

    def default_behaviour(self):
        move = self.move_to_food(self.grid_data[1])
        if move:
            return move
        else:
            backup_moves = self.helper.get_backup_move((self.head_x, self.head_y),
                                                       self.grid_data[0], self.height, self.width)
            if backup_moves:
                return self.helper.get_move_letter((self.head_x, self.head_y), backup_moves[0])
            else:
                return 'up'


# --------------------------------------------------------------------------
# State: Defend (faithful to state_defend.py)
# --------------------------------------------------------------------------
class State_Defend():
    def __init__(self):
        self.helper = None

    def get_move(self, grid_data, data):
        self.height = data["board"]["height"]
        self.width = data["board"]["width"]
        self.head_x = data["you"]["body"][0]["x"]
        self.head_y = data["you"]["body"][0]["y"]
        self.my_snake_health = data["you"]["health"]
        self.my_snake_length = len(data["you"]["body"])
        self.pathfinder = AStar((self.head_x, self.head_y), grid_data[0], self.width, self.height)
        self.grid_data = grid_data
        self.data = data

        move = self.move_to_food()

        if (self.my_snake_length > 3 and self.my_snake_health > 65) or move is None:
            move = self.chase_tail(self.my_snake_health == 100)

        if move:
            return move
        else:
            backup_moves = self.helper.get_backup_move((self.head_x, self.head_y),
                                                       self.grid_data[0], self.height, self.width)
            if backup_moves:
                return self.helper.get_move_letter((self.head_x, self.head_y), backup_moves[0])
            else:
                return 'up'

    def move_to_food(self):
        current_minimum = float('inf')
        current_path = None
        for food in self.grid_data[1]:
            path = self.pathfinder.compute_path(tuple(food))
            if path:
                path = list(path)
                if len(path) < current_minimum:
                    current_minimum = len(path)
                    current_path = path
        if current_path and len(current_path) > 1 and \
                self.helper.is_good_move(current_path[1], self.grid_data[0], self.my_snake_length):
            return self.helper.get_move_letter((self.head_x, self.head_y), list(current_path)[1])
        return None

    def chase_tail(self, snake_growing):
        my_tail = (self.data["you"]["body"][-1]["x"], self.data["you"]["body"][-1]["y"])
        self.grid_data[0][my_tail[1]][my_tail[0]] = 1
        path = self.pathfinder.compute_path(my_tail)
        self.grid_data[0][my_tail[1]][my_tail[0]] = -1
        if path and len(path) > 1:
            danger_tail_move = (path[1] == my_tail and self.tail_is_in_danger())
            if not danger_tail_move:
                if not snake_growing:
                    return self.helper.get_move_letter((self.head_x, self.head_y), list(path)[1])
                else:
                    neighbours = self.helper.get_neighbors(my_tail, self.grid_data[0], self.height, self.width)
                    if neighbours:
                        for neighbour in neighbours:
                            npath = self.pathfinder.compute_path(neighbour)
                            if npath and len(npath) > 1:
                                return self.helper.get_move_letter((self.head_x, self.head_y), list(npath)[1])
        return None

    def tail_is_in_danger(self):
        my_tail = (self.data["you"]["body"][-1]["x"], self.data["you"]["body"][-1]["y"])
        for snake in self.data["board"]["snakes"]:
            (x, y) = (snake["body"][0]["x"], snake["body"][0]["y"])
            moves = [(nx, ny) for nx, ny in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                     if 0 <= nx < self.width and 0 <= ny < self.height]
            if my_tail in moves:
                return True
        return False


# --------------------------------------------------------------------------
# State: Grow (faithful to state_grow.py)
# --------------------------------------------------------------------------
class State_Grow():
    def __init__(self):
        self.helper = None

    def get_move(self, grid_data, data):
        self.height = data["board"]["height"]
        self.width = data["board"]["width"]
        self.head_x = data["you"]["body"][0]["x"]
        self.head_y = data["you"]["body"][0]["y"]
        self.my_snake_health = data["you"]["health"]
        self.my_snake_length = len(data["you"]["body"])
        self.pathfinder = AStar((self.head_x, self.head_y), grid_data[0], self.width, self.height)
        self.grid_data = grid_data
        self.data = data

        move = self.move_to_food()

        if move:
            return move
        else:
            move = self.chase_tail(self.my_snake_health == 100)
            if move:
                return move
            else:
                backup_moves = self.helper.get_backup_move((self.head_x, self.head_y),
                                                           self.grid_data[0], self.height, self.width)
                if backup_moves:
                    return self.helper.get_move_letter((self.head_x, self.head_y), backup_moves[0])
                else:
                    return 'up'

    def move_to_food(self):
        current_minimum = float('inf')
        current_path = None
        for food in self.grid_data[1]:
            path = self.pathfinder.compute_path(tuple(food))
            if path:
                path = list(path)
                if len(path) < current_minimum:
                    current_minimum = len(path)
                    current_path = path
        if current_path and len(current_path) > 1 and \
                self.helper.is_good_move(current_path[1], self.grid_data[0], self.my_snake_length):
            return self.helper.get_move_letter((self.head_x, self.head_y), list(current_path)[1])
        return None

    def chase_tail(self, isGonnaGrow):
        my_tail = (self.data["you"]["body"][-1]["x"], self.data["you"]["body"][-1]["y"])
        self.grid_data[0][my_tail[1]][my_tail[0]] = 1
        path = self.pathfinder.compute_path(my_tail)
        self.grid_data[0][my_tail[1]][my_tail[0]] = 0
        if path and len(path) > 1:
            danger_tail_move = (path[1] == my_tail and self.tail_is_in_danger())
            if not danger_tail_move:
                if not isGonnaGrow:
                    return self.helper.get_move_letter((self.head_x, self.head_y), list(path)[1])
                else:
                    neighbours = self.helper.get_neighbors(my_tail, self.grid_data[0], self.height, self.width)
                    if neighbours:
                        for neighbour in neighbours:
                            npath = self.pathfinder.compute_path(neighbour)
                            if npath and len(npath) > 1:
                                return self.helper.get_move_letter((self.head_x, self.head_y), list(npath)[1])
        return None

    def tail_is_in_danger(self):
        my_tail = (self.data["you"]["body"][-1]["x"], self.data["you"]["body"][-1]["y"])
        for snake in self.data["board"]["snakes"]:
            (x, y) = (snake["body"][0]["x"], snake["body"][0]["y"])
            moves = [(nx, ny) for nx, ny in [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
                     if 0 <= nx < self.width and 0 <= ny < self.height]
            if my_tail in moves:
                return True
        return False


# --------------------------------------------------------------------------
# Absolute-legal-move fallback (v1 y-up). Never step into a body cell or wall.
# --------------------------------------------------------------------------
def _fallback_move(game_state):
    try:
        board = game_state["board"]
        width = board["width"]
        height = board["height"]
        you = game_state["you"]
        head = you["body"][0]
        hx, hy = head["x"], head["y"]

        blocked = set()
        for snake in board.get("snakes", []):
            body = snake["body"]
            # Body cells are blocked; the tail cell will move so it's enterable
            # (unless the snake just ate -> tail stays, but we keep it simple/safe
            # by excluding only the very last cell).
            for cell in body[:-1]:
                blocked.add((cell["x"], cell["y"]))
        # Include our own full body minus tail as blocked too (already covered).

        candidates = [
            ("up", hx, hy + 1),
            ("down", hx, hy - 1),
            ("left", hx - 1, hy),
            ("right", hx + 1, hy),
        ]
        for name, nx, ny in candidates:
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
                return name
        # Nothing safe: just stay in-bounds if possible.
        for name, nx, ny in candidates:
            if 0 <= nx < width and 0 <= ny < height:
                return name
    except Exception:
        pass
    return "up"


def _validate_or_fallback(move_letter, game_state):
    """Ensure the chosen move is legal (in-bounds, not into a body/wall cell).
    If not, replace with a safe fallback."""
    try:
        board = game_state["board"]
        width = board["width"]
        height = board["height"]
        head = game_state["you"]["body"][0]
        hx, hy = head["x"], head["y"]
        deltas = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        if move_letter not in deltas:
            return _fallback_move(game_state)
        dx, dy = deltas[move_letter]
        nx, ny = hx + dx, hy + dy
        if not (0 <= nx < width and 0 <= ny < height):
            return _fallback_move(game_state)
        blocked = set()
        for snake in board.get("snakes", []):
            for cell in snake["body"][:-1]:
                blocked.add((cell["x"], cell["y"]))
        if (nx, ny) in blocked:
            return _fallback_move(game_state)
        return move_letter
    except Exception:
        return _fallback_move(game_state)


# --------------------------------------------------------------------------
# v1 API entry points
# --------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "tbgiles",
        "color": "#FF69B4",
        "head": "shades",
        "tail": "freckled",
    }


def start(game_state):
    return


def end(game_state):
    return


def move(game_state):
    try:
        setup_process = Setup()
        helper = Helper()
        grid_data = setup_process.grid_setup(game_state)

        defend = State_Defend()
        attack = State_Attack()
        grow = State_Grow()
        defend.helper = helper
        attack.helper = helper
        grow.helper = helper

        max_snake = helper.get_max_snake_length(game_state)
        closest_food_distance = helper.get_closest_food_dist(grid_data[1], game_state)
        board_width = game_state["board"]["width"]

        if len(game_state["you"]["body"]) > max_snake + 1:
            state = attack
        elif closest_food_distance < board_width / 1.5:
            state = grow
        else:
            state = defend

        next_move = state.get_move(grid_data, game_state)
        next_move = _validate_or_fallback(next_move, game_state)
        return {"move": next_move}
    except Exception:
        return {"move": _fallback_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
