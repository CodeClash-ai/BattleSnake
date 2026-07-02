import random

# Port of joshhartmann11/battlejake ("an if-else snake") to the Battlesnake v1 API.
#
# The original bot targeted the OLD Battlesnake API, which used a TOP-LEFT origin
# with y increasing DOWNWARD. In that world:
#   - "up"    moved toward y-1
#   - "down"  moved toward y+1
#   - head[1] == 0            was the TOP wall (blocks "up")
#   - head[1] == height-1     was the BOTTOM wall (blocks "down")
#
# The v1 API uses a BOTTOM-LEFT origin with y increasing UPWARD. To reproduce the
# original logic faithfully we flip the y-axis of the incoming v1 state into the
# old y-down representation, run the original algorithm verbatim, then flip the
# resulting move back ("up" <-> "down"). Left/right are unchanged.


def info():
    return {
        "apiversion": "1",
        "author": "joshhartmann11",
        "color": "#99FFFF",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return {}


def end(game_state):
    return {}


# ----------------------------------------------------------------------------
# Original battlejake logic (unchanged), operating in the OLD y-down coordinate
# space. Coordinates here are old-API tuples (x, y) with y increasing downward.
# ----------------------------------------------------------------------------

def get_future_head(head, move):
    if move == 'left':
        return (head[0] - 1, head[1])
    elif move == 'right':
        return (head[0] + 1, head[1])
    elif move == 'up':
        return (head[0], head[1] - 1)
    else:
        return (head[0], head[1] + 1)


def get_previous_move(head, second):
    if head[0] == second[0]:
        if head[1] > second[1]:
            return 'down'
        else:
            return 'up'
    else:
        if head[0] > second[0]:
            return 'right'
        else:
            return 'left'


def flee_wall(moves, walls, head):
    if head[0] >= walls[0] - 2:
        if 'left' in moves:
            return 'left'
        if 'up' in moves:
            return 'up'
        if 'down' in moves:
            return 'down'
    elif head[0] <= 1:
        if 'right' in moves:
            return 'right'
        if 'down' in moves:
            return 'down'
        if 'up' in moves:
            return 'up'

    if head[1] <= 1:
        if 'down' in moves:
            return 'down'
        if 'right' in moves:
            return 'right'
        if 'left' in moves:
            return 'left'
    elif head[1] >= walls[1] - 2:
        if 'up' in moves:
            return 'up'
        if 'left' in moves:
            return 'left'
        if 'right' in moves:
            return 'right'


def kill_others(head, mySize, heads, size, moves):
    for i, h in enumerate(heads):
        if size[i] < mySize:
            xdist = h[0] - head[0]
            ydist = h[1] - head[1]

            if abs(xdist) == 1 and abs(ydist) == 1:
                if xdist > 0 and 'right' in moves:
                    return 'right'
                elif xdist < 0 and 'left' in moves:
                    return 'left'
                if ydist > 0 and 'down' in moves:
                    return 'down'
                elif ydist < 0 and 'up' in moves:
                    return 'up'
            elif (abs(xdist) == 2 and ydist == 0) ^ (abs(ydist) == 2 and xdist == 0):
                if xdist == 2 and 'right' in moves:
                    return 'right'
                elif xdist == -2 and 'left' in moves:
                    return 'left'
                elif ydist == 2 and 'down' in moves:
                    return 'down'
                elif 'up' in moves:
                    return 'up'


def starving(moves, head, food):
    move = get_food(moves, head, food)
    if not (move is None):
        return move

    for f in food:
        xdist = f[0] - head[0]
        ydist = f[1] - head[1]
        if (abs(xdist) == 2 and ydist == 0) ^ (abs(ydist) == 2 and xdist == 0):
            if xdist == 2 and 'right' in moves:
                return 'right'
            elif xdist == -2 and 'left' in moves:
                return 'left'
            elif ydist == 2 and 'down' in moves:
                return 'down'
            elif ydist == -2 and 'up' in moves:
                return 'up'


def get_food(moves, head, food):
    for f in food:
        xdist = f[0] - head[0]
        ydist = f[1] - head[1]
        if (abs(xdist) == 1 and ydist == 0) ^ (abs(ydist) == 1 and xdist == 0):
            if xdist == 1 and 'right' in moves:
                return 'right'
            elif xdist == -1 and 'left' in moves:
                return 'left'
            elif ydist == 1 and 'down' in moves:
                return 'down'
            elif ydist == -1 and 'up' in moves:
                return 'up'


def get_restrictions(head, mySize, walls, snakes, heads, size, op=True):
    directions = {'up': 1, 'down': 1, 'left': 1, 'right': 1}

    # Don't hit a wall
    if head[0] == walls[0] - 1:
        directions['right'] = 0
    elif head[0] == 0:
        directions['left'] = 0

    if head[1] == 0:
        directions['up'] = 0
    elif head[1] == walls[1] - 1:
        directions['down'] = 0

    # Don't hit other snakes
    for s in snakes:
        xdist = abs(s[0] - head[0])
        ydist = abs(s[1] - head[1])
        if xdist + ydist == 1:
            if xdist == 1:
                if s[0] > head[0]:
                    directions['right'] = 0
                else:
                    directions['left'] = 0
            else:
                if s[1] > head[1]:
                    directions['down'] = 0
                else:
                    directions['up'] = 0

    directions2 = {key: value for key, value in directions.items()}

    # Be scared of the heads of others if they're scary
    for i, h in enumerate(heads):
        if not (size[i] < mySize):
            xdist = h[0] - head[0]
            ydist = h[1] - head[1]

            if abs(xdist) == 1 and abs(ydist) == 1:
                if xdist > 0:
                    directions['right'] = 0
                elif xdist < 0:
                    directions['left'] = 0
                if ydist > 0:
                    directions['down'] = 0
                elif ydist < 0:
                    directions['up'] = 0
            elif (abs(xdist) == 2 and ydist == 0) ^ (abs(ydist) == 2 and xdist == 0):
                if xdist == 2:
                    directions['right'] = 0
                elif xdist == -2:
                    directions['left'] = 0
                elif ydist == 2:
                    directions['down'] = 0
                else:
                    directions['up'] = 0

    # If there's no other choice but to possibly collide with a head
    if 1 not in directions.values() and op:
        directions = directions2

    if not op:
        directions = directions2

    moves = [k for k in directions.keys() if directions[k] == 1]
    return moves


def _decide(you, health, mySize, body, head, walls, snakes, heads, size, food):
    """The original /move body, factored out. All coords in old y-down space."""
    numFood = len(food)
    pm = get_previous_move(head, (body[1][0], body[1][1]))

    moves = get_restrictions(head, mySize, walls, snakes, heads, size)
    try:
        move = None
        while move is None:
            if health < (45 - numFood):
                move = starving(moves, head, food)

            if move is None:
                move = flee_wall(moves, walls, head)

            if move is None:
                move = kill_others(head, mySize, heads, size, moves)

            if move is None:
                if health < (70 - numFood):
                    move = get_food(moves, head, food)

            if move is None:
                if pm in moves or moves == []:
                    move = pm

            if move is None:
                move = random.choice(moves)

            nextHead = get_future_head(head, move)
            if get_restrictions(nextHead, mySize, walls, snakes, heads, size, op=False) == []:
                if moves != []:
                    moves.remove(move)
                    if move != []:
                        move = None
    except Exception:
        move = random.choice(moves)

    return move


# ----------------------------------------------------------------------------
# v1 API adapter
# ----------------------------------------------------------------------------

def _flip_y(y, height):
    return (height - 1) - y


# We flip the INPUT y-coordinates into the old y-down space via
# y_old = (H-1) - y_v1. Under that transform, an old-space "up" (y_old
# decreasing) corresponds to y_v1 increasing, i.e. v1 "up". So once the
# coordinates are flipped, the move names map through directly (identity).
_OLD_TO_V1 = {'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right'}
# v1 delta for legality checks (bottom-left origin)
_V1_DELTA = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}


def _safe_fallback(head_v1, width, height, blocked):
    """Pick any legal v1 move: in-bounds and not into a blocked cell."""
    for m, (dx, dy) in _V1_DELTA.items():
        nx, ny = head_v1[0] + dx, head_v1[1] + dy
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
            return m
    # nothing safe; at least stay in bounds
    for m, (dx, dy) in _V1_DELTA.items():
        nx, ny = head_v1[0] + dx, head_v1[1] + dy
        if 0 <= nx < width and 0 <= ny < height:
            return m
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        width = board["width"]
        height = board["height"]
        you = game_state["you"]
        head_v1 = (you["body"][0]["x"], you["body"][0]["y"])

        # Build a set of blocked cells (all snake bodies except tails, which move)
        # for use only in the robustness fallback.
        blocked = set()
        for s in board["snakes"]:
            b = s["body"]
            for seg in b[:-1]:
                blocked.add((seg["x"], seg["y"]))

        # --- Convert v1 state into the OLD y-down representation ---
        H = height

        my_body = [(seg["x"], _flip_y(seg["y"], H)) for seg in you["body"]]
        mySize = you.get("length", len(my_body))
        health = you.get("health", 100)
        head = my_body[0]
        walls = (width, height)

        snakes_cells = []
        heads = []
        size = []
        for s in board["snakes"]:
            b = [(seg["x"], _flip_y(seg["y"], H)) for seg in s["body"]]
            size.append(s.get("length", len(b)))
            heads.append(b[0])
            for c in b:
                snakes_cells.append(c)

        food = [(f["x"], _flip_y(f["y"], H)) for f in board.get("food", [])]

        # Guard against snakes of length 1 (no body[1] for previous move)
        if len(my_body) < 2:
            return {"move": _safe_fallback(head_v1, width, height, blocked)}

        old_move = _decide(you, health, mySize, my_body, head, walls,
                           snakes_cells, heads, size, food)

        if old_move not in _OLD_TO_V1:
            return {"move": _safe_fallback(head_v1, width, height, blocked)}

        v1_move = _OLD_TO_V1[old_move]

        # Robustness: ensure the chosen move is actually legal in v1 terms.
        dx, dy = _V1_DELTA[v1_move]
        nx, ny = head_v1[0] + dx, head_v1[1] + dy
        if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in blocked:
            return {"move": _safe_fallback(head_v1, width, height, blocked)}

        return {"move": v1_move}
    except Exception:
        try:
            board = game_state["board"]
            width = board["width"]
            height = board["height"]
            you = game_state["you"]
            head_v1 = (you["body"][0]["x"], you["body"][0]["y"])
            blocked = set()
            for s in board["snakes"]:
                for seg in s["body"][:-1]:
                    blocked.add((seg["x"], seg["y"]))
            return {"move": _safe_fallback(head_v1, width, height, blocked)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
