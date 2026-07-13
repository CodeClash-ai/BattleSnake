import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
Port of "Vulture Snake" by Spenca (BattleSnake2017).
Original: https://github.com/Spenca/BattleSnake2017 (Python, bottle, old 2017 API).

Original strategy (faithfully reproduced):
  - State 0 "seek food": greedy move toward the closest food (match x first,
    then y).
  - State 1 "circle food": once adjacent (Manhattan dist == 1) to closest food
    with health above a threshold (dist_to_food + 5), enter a defensive
    "square" circling pattern around the food and keep orbiting it.
  - After picking a move, checkCollision() rejects moves into walls or any
    snake body cell; if bad, desperation() picks any collision-free direction
    (falling back to 'left').

The original ran on the 2017 API: top-left origin with y increasing DOWNWARD
(in checkCollision, 'up' => y-1, 'down' => y+1), snake body under
snake['coords'], head at coords[0], id in data['you'], health in
'health_points'. We convert the incoming v1 state into that old top-left frame,
run the ORIGINAL algorithm verbatim, then remap the produced direction back to
v1 (bottom-left, y-up): because we flip the y axis, 'up' and 'down' swap while
'left'/'right' are unchanged.
"""

import random

# ---- persistent state (mirrors original module globals) ----
state = 0
sqCorners = None

# Grid marker constants (unused for decisions but kept for fidelity)
snakeBody = -1
foodPos = -2


# =====================================================================
# ORIGINAL algorithm, operating on the 2017 top-left/y-down data shape.
# (transcribed from app/utils.py, Python 3 syntax)
# =====================================================================

def getSnakeLen(coords):
    return len(coords)


def distance(p, q):
    dx = abs(p[0] - q[0])
    dy = abs(p[1] - q[1])
    return dx + dy


def closestFood(foodList, position):
    closestF = None
    closestDist = 9999
    for food in foodList:
        dist = distance(food, position)
        if dist < closestDist:
            closestF = food
            closestDist = dist
    return closestF


def getDirection(snake):
    fst = snake['coords'][0]
    snd = snake['coords'][1]
    dx = fst[0] - snd[0]
    dy = fst[1] - snd[1]
    if dx == 1:
        return 'right'
    elif dx == -1:
        return 'left'
    elif dy == 1:
        return 'down'
    else:
        return 'up'


def getSeekMove(snake, data):
    move = None
    snakeHead = snake['coords'][0]
    foodList = data['food']
    closeFood = closestFood(foodList, snakeHead)
    if closeFood is None:
        return None
    if snakeHead[0] > closeFood[0]:
        move = 'left'
    elif snakeHead[0] < closeFood[0]:
        move = 'right'
    elif snakeHead[1] > closeFood[1]:
        move = 'up'
    elif snakeHead[1] < closeFood[1]:
        move = 'down'
    return move


def getSqSideLen(n):
    length = 1 + ((n + 4) // 4)
    if length < 3:
        length = 3
    return length


def getSqCorners(snake, closeFood):
    squareDim = getSqSideLen(getSnakeLen(snake['coords']))
    sX = snake['coords'][0][0]
    sY = snake['coords'][0][1]
    snakeHead = snake['coords'][0]
    dx = closeFood[0] - snakeHead[0]
    dy = closeFood[1] - snakeHead[1]
    if dx == 1:
        return [[sX, sY - squareDim + 2], [sX + squareDim - 1, sY - squareDim + 2],
                [sX + squareDim - 1, sY + 1], [sX, sY + 1]], 'up'
    elif dx == -1:
        return [[sX - squareDim + 1, sY - 1], [sX, sY - 1],
                [sX, sY + squareDim - 2], [sX - squareDim + 1, sY + squareDim - 2]], 'down'
    elif dy == 1:
        return [[sX - 1, sY], [sX + squareDim - 2, sY],
                [sX + squareDim - 2, sY + squareDim - 1], [sX - 1, sY + squareDim - 1]], 'right'
    elif dy == -1:
        return [[sX - squareDim + 2, sY - squareDim + 1], [sX + 1, sY - squareDim + 1],
                [sX + 1, sY], [sX - squareDim + 2, sY]], 'left'
    # Fallback for dx/dy not exactly +/-1 (original had no else)
    return None, getSeekMove(snake, {'food': [closeFood]})


def turnRight(direction):
    if direction == 'right':
        return 'down'
    elif direction == 'left':
        return 'up'
    elif direction == 'up':
        return 'right'
    elif direction == 'down':
        return 'left'


def getDefMove(snake, corners):
    snakeHead = snake['coords'][0]
    direction = getDirection(snake)
    if corners is not None and snakeHead in corners:
        return turnRight(direction)
    else:
        return direction


def remove_common_elements(a, b):
    for e in a[:]:
        if e in b:
            a.remove(e)


def checkCollision(snake, data, move):
    currentPos = snake['coords'][0]
    if move == 'up':
        choice = [currentPos[0], currentPos[1] - 1]
    elif move == 'down':
        choice = [currentPos[0], currentPos[1] + 1]
    elif move == 'right':
        choice = [currentPos[0] + 1, currentPos[1]]
    else:  # left (and None default)
        choice = [currentPos[0] - 1, currentPos[1]]

    occupiedPositions = []
    for s in data['snakes']:
        for c in s['coords']:
            occupiedPositions.append(c)

    for s in range(data['width']):
        occupiedPositions.append([s, -1])
        occupiedPositions.append([s, data['height']])
    for s in range(data['height']):
        occupiedPositions.append([-1, s])
        occupiedPositions.append([data['width'], s])

    return choice in occupiedPositions


def desperation(snake, data, move):
    opts = ['up', 'down', 'right', 'left']
    if move in opts:
        opts.remove(move)
    bad = []
    for item in opts:
        if checkCollision(snake, data, item):
            bad.append(item)
    remove_common_elements(opts, bad)
    if len(opts) > 0:
        return random.choice(opts)
    return 'left'


def newState(foodCount, snake, data):
    global state
    global sqCorners
    foods = data['food']
    snakeHead = snake['coords'][0]
    closeFood = closestFood(foods, snakeHead)
    snakeLen = getSnakeLen(snake['coords'])

    if closeFood is None:
        # No food: just avoid dying.
        move = getDirection(snake) if snakeLen >= 2 else 'left'
        if checkCollision(snake, data, move):
            move = desperation(snake, data, move)
        return move

    dist = distance(snakeHead, closeFood)
    health = snake["health_points"]
    threshold = dist + 5

    if state == 0 and dist == 1 and health > threshold:
        sqCorners, move = getSqCorners(snake, closeFood)
        state = 1
    elif state == 1 and health > threshold:
        move = getDefMove(snake, sqCorners)
        state = 1
    else:
        move = getSeekMove(snake, data)
        state = 0

    if checkCollision(snake, data, move):
        move = desperation(snake, data, move)
        state = 0

    return move


# =====================================================================
# v1 API adapter
# =====================================================================

def _to_old_data(game_state):
    """Convert v1 game_state into the 2017 top-left/y-down data dict."""
    board = game_state["board"]
    width = board["width"]
    height = board["height"]

    def flip(p):
        # v1 (bottom-left, y-up) -> old (top-left, y-down)
        return [p["x"], (height - 1) - p["y"]]

    snakes = []
    for s in game_state["board"]["snakes"]:
        snakes.append({
            "id": s["id"],
            "health_points": s.get("health", 100),
            "coords": [flip(c) for c in s["body"]],
        })

    old = {
        "width": width,
        "height": height,
        "you": game_state["you"]["id"],
        "food": [flip(f) for f in board.get("food", [])],
        "snakes": snakes,
    }
    our = None
    for s in snakes:
        if s["id"] == old["you"]:
            our = s
    if our is None:
        # Build from 'you' directly if not present in snakes list
        y = game_state["you"]
        our = {
            "id": y["id"],
            "health_points": y.get("health", 100),
            "coords": [flip(c) for c in y["body"]],
        }
        old["snakes"].append(our)
    return old, our


# Remap old-frame direction to v1. The original 2017 API defines 'up' as
# y-1 on a top-left/y-down board; v1 defines 'up' as y+1 on a bottom-left
# board. Because we feed the algorithm y-flipped coordinates (old frame), a
# move the algorithm calls 'up' (toward smaller old-y) is physically the same
# as v1 'up' (toward larger v1-y). So the remap is the identity.
_REMAP = {"up": "up", "down": "down", "left": "left", "right": "right"}


def _fallback_move(game_state):
    """Guaranteed-legal move: in bounds and not into a snake body (tails ok)."""
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]

    # Occupied cells (exclude tails, which move away). Include a tail only if
    # that snake just ate (body has a duplicated tail => stays).
    blocked = set()
    for s in board["snakes"]:
        body = s["body"]
        for i, c in enumerate(body):
            if i == len(body) - 1 and len(body) >= 2 and body[-1] != body[-2]:
                continue  # tail will vacate
            blocked.add((c["x"], c["y"]))

    dirs = {
        "up": (head["x"], head["y"] + 1),
        "down": (head["x"], head["y"] - 1),
        "left": (head["x"] - 1, head["y"]),
        "right": (head["x"] + 1, head["y"]),
    }
    for mv, (nx, ny) in dirs.items():
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
            return mv
    # No safe move: at least stay in bounds.
    for mv, (nx, ny) in dirs.items():
        if 0 <= nx < w and 0 <= ny < h:
            return mv
    return "up"


def info():
    return {
        "apiversion": "1",
        "author": "Spenca",
        "color": "#000000",
        "head": "smile",
        "tail": "pixel",
    }


def start(game_state):
    global state, sqCorners
    state = 0
    sqCorners = None


def end(game_state):
    pass


def move(game_state):
    try:
        old, our = _to_old_data(game_state)
        mv = newState(len(old["food"]), our, old)
        v1mv = _REMAP.get(mv)
        if v1mv is None:
            v1mv = _fallback_move(game_state)

        # Safety: verify the chosen move is legal in v1; if not, fall back.
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head = game_state["you"]["body"][0]
        delta = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        dx, dy = delta[v1mv]
        nx, ny = head["x"] + dx, head["y"] + dy
        own = {(c["x"], c["y"]) for c in game_state["you"]["body"][:-1]}
        if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) in own:
            v1mv = _fallback_move(game_state)
        return {"move": v1mv}
    except Exception:
        try:
            return {"move": _fallback_move(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
