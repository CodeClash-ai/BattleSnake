"""CodeClash port of tyrelh's battlesnake2018 (https://github.com/tyrelh/battlesnake2018).

Original: Python 2018, bottle-based, OLD Battlesnake API (top-left origin, y-down).
This is a faithful reimplementation for the current v1 API (bottom-left origin, y-up).

Strategy (unchanged from original):
  - If health below a board/length-derived minimum, or if not the biggest snake -> seek
    closest food via A* (falling back to own tail if no food).
  - If biggest snake -> hunt: A* toward closest KILL_ZONE (a square adjacent to a smaller
    enemy's head), falling back to own tail.
  - build_map marks food, snake bodies, enterable tails as space, enemy heads, and
    DANGER/KILL zones around enemy heads.
  - best_move does a flood-fill look_ahead to pick the move with the most reachable area,
    preferring KILL_ZONE > SPACE > DANGER, and preferring moves that enclose own tail.
  - First INITIAL_FEEDING turns always aim at closest food.

Coordinate handling: the original algorithm assumes a top-left origin where its "UP"
means y-1. To keep the algorithm verbatim we flip incoming v1 coordinates to that
top-left space (y_old = height - 1 - y_new). Because the flip is applied on input, the
direction strings the original emits ('up'/'down'/'left'/'right') are already correct in
v1 terms and are returned as-is.
"""

# ---- original constants ----
SPACE = 0
KILL_ZONE = 1
FOOD = 2
DANGER = 3
SNAKE_BODY = 4
ENEMY_HEAD = 5
directions = ['up', 'left', 'down', 'right']
UP = 0
LEFT = 1
DOWN = 2
RIGHT = 3

INITIAL_FEEDING = 3

# module-level board globals (mirrors original use of globals)
board_width = 0
board_height = 0
my_id = ''


# ---------------------------------------------------------------------------
# v1 -> old-API adapter
# ---------------------------------------------------------------------------
def _to_old(game_state):
    """Translate a v1 game_state into the old-API dict shape the original code expects,
    flipping the y axis (v1 bottom-left -> old top-left)."""
    board = game_state['board']
    w = board['width']
    h = board['height']

    def pt(p):
        return {'x': p['x'], 'y': h - 1 - p['y']}

    def conv_snake(s):
        body = [pt(seg) for seg in s['body']]
        return {
            'id': s['id'],
            'name': s.get('name', ''),
            'health': s.get('health', 100),
            'length': s.get('length', len(body)),
            'body': {'data': body},
        }

    you = game_state['you']
    old = {
        'turn': game_state.get('turn', 0),
        'width': w,
        'height': h,
        'food': {'data': [pt(f) for f in board.get('food', [])]},
        'snakes': {'data': [conv_snake(s) for s in board.get('snakes', [])]},
        'you': conv_snake(you),
    }
    return old


# ---------------------------------------------------------------------------
# original logic (adapted only to remove bottle / debug prints)
# ---------------------------------------------------------------------------
def _decide(data):
    """Top-level move decision, mirroring the original /move handler."""
    global board_height, board_width, my_id
    board_width = data['width']
    board_height = data['height']
    my_id = data['you']['id']
    health = data['you']['health']

    survival_min = set_health_min(data)
    if health < survival_min:
        direction = hungry(data)
    elif not biggest(data):
        direction = hungry(data)
    elif biggest(data):
        direction = hunt(data)
    else:
        direction = kill_time(data)
    return directions[direction]


def hungry(data):
    grid = build_map(data)
    target = closest_food(grid, data)
    if not target:
        target = get_tail(data)
    return astar(data, grid, target, 'food')


def kill_time(data):
    grid = build_map(data)
    tail = get_tail(data)
    return astar(data, grid, tail, 'my_tail')


def hunt(data):
    grid = build_map(data)
    target = get_enemy_head(grid, data)
    if not target:
        target = get_tail(data)
    return astar(data, grid, target, 'enemy_head')


def build_map(data):
    global my_id, board_height, board_width
    my_length = data['you']['length']
    grid = [[SPACE for _col in range(data['height'])] for _row in range(data['width'])]
    for food in data['food']['data']:
        grid[food['x']][food['y']] = FOOD
    for snake in data['snakes']['data']:
        for segment in snake['body']['data']:
            grid[segment['x']][segment['y']] = SNAKE_BODY
        # tail is enterable if the snake is not currently growing
        if snake['body']['data'][-1] != snake['body']['data'][-2]:
            tempX = snake['body']['data'][-1]['x']
            tempY = snake['body']['data'][-1]['y']
            grid[tempX][tempY] = SPACE
        if snake['id'] == my_id:
            continue
        head = get_coords(snake['body']['data'][0])
        grid[head[0]][head[1]] = ENEMY_HEAD
        head_zone = DANGER
        if snake['length'] < my_length:
            head_zone = KILL_ZONE
        if head[1] + 1 < board_height:
            if grid[head[0]][head[1] + 1] < head_zone:
                grid[head[0]][head[1] + 1] = head_zone
        if head[1] - 1 >= 0:
            if grid[head[0]][head[1] - 1] < head_zone:
                grid[head[0]][head[1] - 1] = head_zone
        if head[0] - 1 >= 0:
            if grid[head[0] - 1][head[1]] < head_zone:
                grid[head[0] - 1][head[1]] = head_zone
        if head[0] + 1 < board_width:
            if grid[head[0] + 1][head[1]] < head_zone:
                grid[head[0] + 1][head[1]] = head_zone
    return grid


def astar(data, grid, destination, mode):
    search_scores = build_astar_grid(data, grid)
    open_set = []
    closed_set = []
    start = current_location(data)
    if data['turn'] < INITIAL_FEEDING:
        cf = closest_food(grid, data)
        if cf:
            destination = cf
    if not destination:
        destination = get_tail(data)
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
            while (search_scores[temp[0]][temp[1]].previous[0] != start[0]
                   or search_scores[temp[0]][temp[1]].previous[1] != start[1]):
                temp = search_scores[temp[0]][temp[1]].previous
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
                while (search_scores[temp[0]][temp[1]].previous[0] != start[0]
                       or search_scores[temp[0]][temp[1]].previous[1] != start[1]):
                    temp = search_scores[temp[0]][temp[1]].previous
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
    # open set empty: no path
    move = 2
    if mode == 'food' or mode == 'enemy_head':
        tail = get_tail(data)
        move = astar(data, grid, tail, 'my_tail')
    return best_move(move, data, grid)


def calculate_direction(a, b, grid, data):
    x = a[0] - b[0]
    y = a[1] - b[1]
    direction = 0
    if x < 0:
        direction = 3
    elif x > 0:
        direction = 1
    elif y < 0:
        direction = 2
    count = 0
    while not valid_move(direction, grid, data):
        if count == 3:
            return direction
        count += 1
        direction += 1
        if direction == 4:
            direction = 0
    return direction


def best_move(reccommended_move, data, grid):
    global board_height, board_width
    reg_moves = []
    danger_moves = []
    kill_moves = []
    current = current_location(data)
    best = []
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
                if grid[current[0]][current[1] - 1] == DANGER:
                    reg_moves.remove(move)
                    danger_moves.append(move)
                elif grid[current[0]][current[1] - 1] == KILL_ZONE:
                    reg_moves.remove(move)
                    kill_moves.append(move)
            elif move == DOWN:
                if grid[current[0]][current[1] + 1] == DANGER:
                    reg_moves.remove(move)
                    danger_moves.append(move)
                elif grid[current[0]][current[1] + 1] == KILL_ZONE:
                    reg_moves.remove(move)
                    kill_moves.append(move)
            elif move == LEFT:
                if grid[current[0] - 1][current[1]] == DANGER:
                    reg_moves.remove(move)
                    danger_moves.append(move)
                elif grid[current[0] - 1][current[1]] == KILL_ZONE:
                    reg_moves.remove(move)
                    kill_moves.append(move)
            elif move == RIGHT:
                if grid[current[0] + 1][current[1]] == DANGER:
                    reg_moves.remove(move)
                    danger_moves.append(move)
                elif grid[current[0] + 1][current[1]] == KILL_ZONE:
                    reg_moves.remove(move)
                    kill_moves.append(move)
    else:
        return reccommended_move  # suicide (no viable at all)

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


def look_ahead(move, grid, data):
    area = 0
    current = current_location(data)
    given_move_coords = current
    if move == UP:
        given_move_coords = [current[0], current[1] - 1]
    elif move == DOWN:
        given_move_coords = [current[0], current[1] + 1]
    elif move == LEFT:
        given_move_coords = [current[0] - 1, current[1]]
    elif move == RIGHT:
        given_move_coords = [current[0] + 1, current[1]]
    move_queue = []
    checked_moves = []
    move_queue.append(given_move_coords)
    checked_moves.append(list(current))
    while move_queue:
        for next_move in list(move_queue):
            area += 1
            move_queue.remove(next_move)
            checked_moves.append(next_move)
            neighbor_up = [next_move[0], next_move[1] - 1]
            if (neighbor_up != list(current) and neighbor_up not in checked_moves
                    and neighbor_up not in move_queue):
                if neighbor_up[1] >= 0:
                    if grid[neighbor_up[0]][neighbor_up[1]] <= DANGER:
                        move_queue.append(neighbor_up)
            neighbor_down = [next_move[0], next_move[1] + 1]
            if (neighbor_down != list(current) and neighbor_down not in checked_moves
                    and neighbor_down not in move_queue):
                if neighbor_down[1] < board_height:
                    if grid[neighbor_down[0]][neighbor_down[1]] <= DANGER:
                        move_queue.append(neighbor_down)
            neighbor_left = [next_move[0] - 1, next_move[1]]
            if (neighbor_left != list(current) and neighbor_left not in checked_moves
                    and neighbor_left not in move_queue):
                if neighbor_left[0] >= 0:
                    if grid[neighbor_left[0]][neighbor_left[1]] <= DANGER:
                        move_queue.append(neighbor_left)
            neighbor_right = [next_move[0] + 1, next_move[1]]
            if (neighbor_right != list(current) and neighbor_right not in checked_moves
                    and neighbor_right not in move_queue):
                if neighbor_right[0] < board_width:
                    if grid[neighbor_right[0]][neighbor_right[1]] <= DANGER:
                        move_queue.append(neighbor_right)
    return area


def move_contains_tail(move, grid, data):
    tail = get_coords(data['you']['body']['data'][-1])
    current = current_location(data)
    contains_tail = False
    given_move_coords = current
    if move == UP:
        given_move_coords = [current[0], current[1] - 1]
    elif move == DOWN:
        given_move_coords = [current[0], current[1] + 1]
    elif move == LEFT:
        given_move_coords = [current[0] - 1, current[1]]
    elif move == RIGHT:
        given_move_coords = [current[0] + 1, current[1]]
    move_queue = []
    checked_moves = []
    move_queue.append(given_move_coords)
    checked_moves.append(list(current))
    while move_queue:
        for next_move in list(move_queue):
            if tail[0] == next_move[0] and tail[1] == next_move[1]:
                contains_tail = True
            move_queue.remove(next_move)
            checked_moves.append(next_move)
            neighbor_up = [next_move[0], next_move[1] - 1]
            if (neighbor_up != list(current) and neighbor_up not in checked_moves
                    and neighbor_up not in move_queue):
                if neighbor_up[1] >= 0:
                    if grid[neighbor_up[0]][neighbor_up[1]] <= DANGER:
                        move_queue.append(neighbor_up)
            neighbor_down = [next_move[0], next_move[1] + 1]
            if (neighbor_down != list(current) and neighbor_down not in checked_moves
                    and neighbor_down not in move_queue):
                if neighbor_down[1] < board_height:
                    if grid[neighbor_down[0]][neighbor_down[1]] <= DANGER:
                        move_queue.append(neighbor_down)
            neighbor_left = [next_move[0] - 1, next_move[1]]
            if (neighbor_left != list(current) and neighbor_left not in checked_moves
                    and neighbor_left not in move_queue):
                if neighbor_left[0] >= 0:
                    if grid[neighbor_left[0]][neighbor_left[1]] <= DANGER:
                        move_queue.append(neighbor_left)
            neighbor_right = [next_move[0] + 1, next_move[1]]
            if (neighbor_right != list(current) and neighbor_right not in checked_moves
                    and neighbor_right not in move_queue):
                if neighbor_right[0] < board_width:
                    if grid[neighbor_right[0]][neighbor_right[1]] <= DANGER:
                        move_queue.append(neighbor_right)
    return contains_tail


def valid_move(d, grid, data):
    global board_height, board_width
    current = current_location(data)
    if d == 0:
        if current[1] - 1 < 0:
            return False
        return grid[current[0]][current[1] - 1] <= DANGER
    if d == 1:
        if current[0] - 1 < 0:
            return False
        return grid[current[0] - 1][current[1]] <= DANGER
    if d == 2:
        if current[1] + 1 > board_height - 1:
            return False
        return grid[current[0]][current[1] + 1] <= DANGER
    if d == 3:
        if current[0] + 1 > board_width - 1:
            return False
        return grid[current[0] + 1][current[1]] <= DANGER
    return True


def get_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_coords(o):
    return (o['x'], o['y'])


def current_location(data):
    return (data['you']['body']['data'][0]['x'], data['you']['body']['data'][0]['y'])


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


def get_enemy_head(grid, data):
    my_location = current_location(data)
    close_kill_zone = None
    close_kill_distance = 9999
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == KILL_ZONE:
                kill_zone = [i, j]
                distance = get_distance(my_location, kill_zone)
                if distance < close_kill_distance:
                    close_kill_zone = kill_zone
                    close_kill_distance = distance
    return close_kill_zone


def get_tail(data):
    body = data['you']['body']['data']
    tail = current_location(data)
    for segment in body:
        tail = get_coords(segment)
    return tail


def build_astar_grid(data, grid):
    w = data['width']
    h = data['height']
    astar_grid = [[Cell(row, col) for col in range(h)] for row in range(w)]
    for i in range(w):
        for j in range(h):
            astar_grid[i][j].state = grid[i][j]
    return astar_grid


class Cell:
    def __init__(self, x, y):
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


def biggest(data):
    mid = data['you']['id']
    my_length = data['you']['length']
    longest_length = 0
    for snake in data['snakes']['data']:
        if mid != snake['id']:
            if snake['length'] > longest_length:
                longest_length = snake['length']
    if longest_length >= my_length:
        return False
    return True


def set_health_min(data):
    health_board = max(board_height, board_width) * 2
    health_length = data['you']['length']
    if health_length > health_board:
        return health_length
    return health_board


# ---------------------------------------------------------------------------
# robust safety fallback
# ---------------------------------------------------------------------------
def _safe_fallback(game_state):
    """Return any in-bounds move that does not hit a snake body (tails enterable)."""
    board = game_state['board']
    w = board['width']
    h = board['height']
    you = game_state['you']
    head = you['body'][0]
    hx, hy = head['x'], head['y']

    # occupied cells: all snake bodies except each snake's tail (tail moves away),
    # unless the snake just ate (tail == the segment before it).
    blocked = set()
    for s in board.get('snakes', []):
        body = s['body']
        for i, seg in enumerate(body):
            if i == len(body) - 1:
                # tail: enterable unless growing (tail == second-to-last)
                if len(body) >= 2 and body[-1] == body[-2]:
                    blocked.add((seg['x'], seg['y']))
                # else leave enterable
            else:
                blocked.add((seg['x'], seg['y']))

    candidates = [
        ('up', hx, hy + 1),
        ('down', hx, hy - 1),
        ('left', hx - 1, hy),
        ('right', hx + 1, hy),
    ]
    for name, nx, ny in candidates:
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
            return name
    # totally trapped: return an in-bounds move if any, else 'up'
    for name, nx, ny in candidates:
        if 0 <= nx < w and 0 <= ny < h:
            return name
    return 'up'


# ---------------------------------------------------------------------------
# CodeClash v1 API entry points
# ---------------------------------------------------------------------------
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
        old = _to_old(game_state)
        chosen = _decide(old)
        if chosen not in ("up", "down", "left", "right"):
            chosen = _safe_fallback(game_state)
        else:
            # validate the chosen move against real board to guarantee legality
            board = game_state['board']
            w = board['width']
            h = board['height']
            head = game_state['you']['body'][0]
            hx, hy = head['x'], head['y']
            delta = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
            dx, dy = delta[chosen]
            nx, ny = hx + dx, hy + dy
            blocked = set()
            for s in board.get('snakes', []):
                body = s['body']
                for i, seg in enumerate(body):
                    if i == len(body) - 1:
                        if len(body) >= 2 and body[-1] == body[-2]:
                            blocked.add((seg['x'], seg['y']))
                    else:
                        blocked.add((seg['x'], seg['y']))
            if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) in blocked:
                chosen = _safe_fallback(game_state)
        return {"move": chosen}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
