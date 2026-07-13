"""
Port of joshhartmann11/battleJake2019 (Battlesnake 2019, Python/bottle) to the
CodeClash arena format against the current Battlesnake v1 API.

The original bot was written for the 2019 Battlesnake API which used a TOP-LEFT
origin with y increasing downward, and where the move string "up" meant y-1.
The v1 API uses a BOTTOM-LEFT origin with y increasing upward and "up" == y+1.

To reproduce the original strategy faithfully and unchanged, we flip the y
coordinate of every input coordinate into the original's y-down frame:
    y_old = height - 1 - y_new
Then we run the original move-selection logic verbatim. Because a flip of y is
its own inverse for the direction semantics, the returned move string ("up",
"down", "left", "right") is already correct for the v1 API:
    old "up" => y_old decreases => y_new increases => v1 "up"   (matches)
    old "down" => y_old increases => y_new decreases => v1 "down" (matches)
left/right are unaffected.

Pure stdlib. All move logic wrapped in try/except with a safe legal fallback.
"""

import random
import traceback
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ---- Original tuning constants (verbatim) ------------------------------------
HUNGRY = 60
FOOD_MIN = 1
STARVING = 30
FOOD_MAX = 10
SIZE_THRESHOLD = 0

# The original tracked whether it ate food last turn via a module global. That
# is unreliable in a stateless arena, so we recompute it each move from health.
ate_food_last_turn = False


# ---- Original helper functions (ported verbatim, y-down frame) ---------------
def have_choice(move, moves):
    if move is not None:
        return False
    if len(moves) <= 1:
        return False
    return True


def get_space(space, move):
    if move == 'left':
        return (space[0] - 1, space[1])
    elif move == 'right':
        return (space[0] + 1, space[1])
    elif move == 'up':
        return (space[0], space[1] - 1)
    else:
        return (space[0], space[1] + 1)


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


def eat_tail(head, snakes):
    moves = []
    for s in snakes:
        xdist = head[0] - s['tail'][0]
        ydist = head[1] - s['tail'][1]
        if abs(xdist) == 1 and ydist == 0:
            if xdist > 0:
                moves.append('left')
            else:
                moves.append('right')
        if abs(ydist) == 1 and xdist == 0:
            if ydist > 0:
                moves.append('up')
            else:
                moves.append('down')
    return moves


def go_straight(moves, head, body):
    if len(body) > 1:
        pm = get_previous_move(head, body[1])
        if pm in moves:
            return pm


def flee_heads(moves, snakes, head, dist=999):
    headManhattan = [abs(s['head'][0] - head[0]) + abs(s['head'][1] - head[1]) for s in snakes]
    closestSnakes = sorted([(x, i) for (i, x) in enumerate(headManhattan)])

    tmpMoves = list(moves)

    for s in closestSnakes:
        snake = snakes[s[1]]
        xdist = head[0] - snake['body'][0][0]
        ydist = head[1] - snake['body'][0][1]

        if len(moves) == 1:
            return moves

        if abs(xdist) < abs(ydist) and xdist < dist:
            if ('left' in moves) and (xdist > 0):
                moves.remove('left')
            if ('right' in moves) and (xdist < 0):
                moves.remove('right')
        elif ydist < dist:
            if ('down' in moves) and (ydist < 0):
                moves.remove('down')
            if ('up' in moves) and (ydist > 0):
                moves.remove('up')
        else:
            return moves

    if moves == []:
        moves = tmpMoves
    return moves


def flee_others(moves, delMoves, snakesTogether, head, dist):
    prevMoves = list(moves)
    validMoves = list(moves)
    for s in snakesTogether:
        if s not in delMoves:
            for m in moves:
                fh = get_space(head, m)
                xdist = s[0] - fh[0]
                ydist = s[1] - fh[1]
                if (abs(xdist) == dist and ydist == 0) or (abs(ydist) == dist and xdist == 0):
                    if m in validMoves:
                        validMoves.remove(m)
            moves = validMoves

    if moves == []:
        return prevMoves
    return moves


def ate_food(head, food, move):
    if get_space(head, move) in food:
        return True
    else:
        return False


def flee_wall(moves, walls, head):
    if head[0] >= walls[0] - 1:
        if 'left' in moves:
            return ['left']
    elif head[0] <= 0:
        if 'right' in moves:
            return ['right']

    if head[1] <= 0:
        if 'down' in moves:
            return ['down']
    elif head[1] >= walls[1] - 1:
        if 'up' in moves:
            return ['up']

    validMoves = list(moves)

    if head[0] >= walls[0] - 2:
        if 'right' in moves:
            validMoves.remove('right')
    elif head[0] <= 1:
        if 'left' in moves:
            validMoves.remove('left')

    if len(moves) > 1:
        if head[1] <= 1:
            if 'up' in moves:
                validMoves.remove('up')
        elif head[1] >= walls[1] - 2:
            if 'down' in moves:
                validMoves.remove('down')

    if validMoves == []:
        return moves
    return validMoves


def strangle_others(moves, head, mySize, body, snakes, walls):
    if head[0] == 0 or head[0] == walls[0] - 2 or \
       head[1] == 0 or head[1] == walls[1] - 2:

        mydir = (head[0] - body[1][0], head[1] - body[1][1])
        for s in snakes:
            snakedir = (s['head'][0] - s['body'][1][0], s['head'][1] - s['body'][1][1])
            if snakedir == mydir:
                if s['head'][0] == 0 or \
                   s['head'][0] == walls[0] - 1 or \
                   s['head'][1] == 0 or \
                   s['head'][1] == walls[0] - 1:
                    if mydir[0] > 0 and 'right' in moves and \
                       head[0] - s['head'][0] < mySize and head[0] - s['head'][0] > 0:
                        return 'right'
                    elif mydir[0] < 0 and 'left' in moves and \
                         head[0] - s['head'][0] > -mySize and head[0] - s['head'][0] < 0:
                        return 'left'
                    elif mydir[1] > 1 and 'down' in moves and \
                         head[1] - s['head'][1] > mySize and head[1] - s['head'][1] > 0:
                        return 'down'
                    elif mydir[1] < 1 and 'up' in moves and \
                         head[1] - s['head'][1] > -mySize and head[1] - s['head'][1] < 0:
                        return 'up'
    return None


def eat_others(moves, head, mySize, snakes):
    validMoves = []
    for s in snakes:
        if s['size'] < mySize - 1:
            xdist = s['head'][0] - head[0]
            ydist = s['head'][1] - head[1]

            if (abs(xdist) == 1) and (abs(ydist) == 1):
                if xdist > 0 and 'right' in moves:
                    validMoves.append('right')
                elif xdist < 0 and 'left' in moves:
                    validMoves.append('left')
                if ydist > 0 and 'down' in moves:
                    validMoves.append('down')
                elif ydist < 0 and 'up' in moves:
                    validMoves.append('up')

            elif (abs(xdist) == 2 and ydist == 0) or (abs(ydist) == 2 and xdist == 0):
                if xdist == 2 and 'right' in moves:
                    validMoves.append('right')
                elif xdist == -2 and 'left' in moves:
                    validMoves.append('left')
                elif ydist == 2 and 'down' in moves:
                    validMoves.append('down')
                elif 'up' in moves:
                    validMoves.append('up')

    if validMoves == []:
        return moves
    return list(set(validMoves))


def get_food(moves, head, food, dist):
    validMoves = []
    for f in food:
        xdist = f[0] - head[0]
        ydist = f[1] - head[1]

        if (abs(xdist) + abs(ydist)) <= dist:
            if xdist > 0 and 'right' in moves:
                validMoves.append('right')
            elif xdist < 0 and 'left' in moves:
                validMoves.append('left')
            elif ydist > 0 and 'down' in moves:
                validMoves.append('down')
            elif ydist < 0 and 'up' in moves:
                validMoves.append('up')

    if validMoves == []:
        return moves
    return list(set(validMoves))


def dont_hit_wall(moves, head, walls):
    if head[0] == walls[0] - 1 and 'right' in moves:
        moves.remove('right')
    elif head[0] == 0 and 'left' in moves:
        moves.remove('left')

    if head[1] == 0 and 'up' in moves:
        moves.remove('up')
    elif head[1] == walls[1] - 1 and 'down' in moves:
        moves.remove('down')

    return moves


def dont_hit_snakes(moves, head, snakesTogether, ignore):
    if get_space(head, 'left') in snakesTogether and 'left' in moves:
        moves.remove('left')
    if get_space(head, 'right') in snakesTogether and 'right' in moves:
        moves.remove('right')
    if get_space(head, 'up') in snakesTogether and 'up' in moves:
        moves.remove('up')
    if get_space(head, 'down') in snakesTogether and 'down' in moves:
        moves.remove('down')
    return moves


def dont_get_eaten(moves, you, snakes, sameSize=True):
    for s in snakes:
        if s['id'] == you.get('id'):
            continue
        if ((s['size'] >= you['size']) and sameSize) or \
           ((s['size'] > you['size']) and not sameSize):
            xdist = s['head'][0] - you['head'][0]
            ydist = s['head'][1] - you['head'][1]

            if abs(xdist) == 1 and abs(ydist) == 1:
                if xdist > 0 and 'right' in moves:
                    moves.remove('right')
                elif xdist < 0 and 'left' in moves:
                    moves.remove('left')
                if ydist > 0 and 'down' in moves:
                    moves.remove('down')
                elif ydist < 0 and 'up' in moves:
                    moves.remove('up')

            elif (abs(xdist) == 2 and ydist == 0) or (abs(ydist) == 2 and xdist == 0):
                if xdist == 2 and 'right' in moves:
                    moves.remove('right')
                elif xdist == -2 and 'left' in moves:
                    moves.remove('left')
                elif ydist == 2 and 'down' in moves:
                    moves.remove('down')
                elif ydist == -2 and 'up' in moves:
                    moves.remove('up')

    return moves


# ---- v1 -> original-frame conversion ----------------------------------------
def _to_old_frame(game_state):
    """Convert a v1 game_state into the 2019-style `data` dict the original
    logic expects, flipping y so the board is in the top-left/y-down frame."""
    board = game_state['board']
    W = board['width']
    H = board['height']

    def fy(y):
        return H - 1 - y

    def pt(c):
        return (c['x'], fy(c['y']))

    you = game_state['you']
    you_body = [pt(b) for b in you['body']]

    data_you = {
        'id': you['id'],
        'body': you_body,
        'head': you_body[0],
        'size': len(you_body),
        'health': you.get('health', 100),
    }

    snakes = []
    snakesTogether = []
    for s in board['snakes']:
        body = [pt(b) for b in s['body']]
        for b in body:
            snakesTogether.append(b)
        snakes.append({
            'id': s['id'],
            'size': len(body),
            'body': body,
            'head': body[0],
            'tail': body[-1],
        })

    food = [pt(f) for f in board['food']]
    walls = (W, H)
    return data_you, snakes, snakesTogether, food, walls


def _pick_original_move(game_state):
    """Runs the original battleJake2019 move-selection logic in the y-down frame.
    Returns a move string ('up'/'down'/'left'/'right') that is already valid in
    v1 semantics (see module docstring)."""
    global ate_food_last_turn

    you, snakes, snakesTogether, food, walls = _to_old_frame(game_state)
    health = game_state['you'].get('health', 100)
    you['health'] = health

    # Reconstruct "ate food last turn": in v1, health resets to 100 the turn
    # after eating (approx: at 100 health mid-game we likely just ate).
    turn = game_state.get('turn', 0)
    ate_food_last_turn = (health >= 100 and turn > 0)

    move = None
    moves = ['left', 'right', 'up', 'down']

    if ate_food_last_turn:
        moves = dont_hit_wall(moves, you['head'], walls)
        moves = dont_hit_snakes(moves, you['head'], snakesTogether, [])
        moves = dont_get_eaten(moves, you, snakes)
    else:
        moves = dont_hit_wall(moves, you['head'], walls)
        moves = dont_hit_snakes(moves, you['head'], snakesTogether, [you['body'][-1]])
        moves = dont_get_eaten(moves, you, snakes)

    # Don't choose anything that'll kill you next time
    if len(moves) > 1:
        tmpMoves = list(moves)
        for m in moves:
            nextHead = get_space(you['head'], m)
            nextMoves = ['left', 'right', 'up', 'down']
            nextMoves = dont_hit_wall(nextMoves, nextHead, walls)
            nextMoves = dont_hit_snakes(nextMoves, nextHead, snakesTogether + [you['head']], [])
            if nextMoves == []:
                tmpMoves.remove(m)
        if tmpMoves != []:
            moves = tmpMoves

    # Take food as first preference if I'm small
    if you['size'] < 6:
        you["health"] = you["health"] / 2

    # Take food as preference as I get more hungry
    if have_choice(move, moves) and (you["health"] < HUNGRY):
        maxFood = round((1 - ((you["health"] - STARVING) / (HUNGRY - STARVING))) * (FOOD_MAX - FOOD_MIN))
        for i in reversed(range(1, maxFood)):
            if have_choice(move, moves):
                moves = get_food(moves, you['head'], food, i)

    if have_choice(moves, moves):
        move = strangle_others(moves, you['head'], you['size'], you['body'], snakes, walls)

    if have_choice(move, moves):
        moves = flee_wall(moves, walls, you['head'])

    if have_choice(move, moves):
        moves = flee_others(moves, [you['body'][0], you['body'][-1]], snakesTogether, you['head'], 1)

    if have_choice(move, moves):
        moves = eat_others(moves, you['head'], you['size'], snakes)

    if have_choice(move, moves):
        moves = flee_heads(moves, snakes, you['head'], dist=3)

    if have_choice(move, moves):
        move = go_straight(moves, you['head'], you['body'])

    if have_choice(move, moves):
        moves = flee_heads(moves, snakes, you['head'])

    if have_choice(move, moves):
        move = random.choice(moves)

    if move is None:
        if len(moves) == 1:
            move = moves[0]
        else:
            # Last-ditch: try eat_tail branch, else any non-lethal move.
            tailMoves = eat_tail(you['head'], snakes)
            tailMoves = dont_get_eaten(tailMoves, you, snakes, sameSize=False)
            if tailMoves:
                move = tailMoves[0]
            if move is None:
                m2 = ['left', 'right', 'up', 'down']
                m2 = dont_hit_wall(m2, you['head'], walls)
                m2 = dont_hit_snakes(m2, you['head'], snakesTogether, [])
                m2 = dont_get_eaten(m2, you, snakes, sameSize=False)
                if m2 == []:
                    move = 'up'
                else:
                    move = random.choice(m2)

    return move


# ---- Safe fallback (v1 frame) -----------------------------------------------
def _safe_move(game_state):
    """Guaranteed legal move: in bounds and not onto any snake body segment
    (tails are enterable). Used if the main logic fails or returns nothing."""
    board = game_state['board']
    W, H = board['width'], board['height']
    you = game_state['you']
    head = you['body'][0]

    occupied = set()
    for s in board['snakes']:
        body = s['body']
        for i, b in enumerate(body):
            # A tail is enterable unless the snake likely just ate (approx by health).
            if i == len(body) - 1 and s.get('health', 100) < 100:
                continue
            occupied.add((b['x'], b['y']))

    dirs = {
        'up': (head['x'], head['y'] + 1),
        'down': (head['x'], head['y'] - 1),
        'left': (head['x'] - 1, head['y']),
        'right': (head['x'] + 1, head['y']),
    }
    for name, (nx, ny) in dirs.items():
        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in occupied:
            return name
    # Nothing safe: at least stay in bounds if possible.
    for name, (nx, ny) in dirs.items():
        if 0 <= nx < W and 0 <= ny < H:
            return name
    return 'up'


# ---- v1 API entry points -----------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "joshhartmann11",
        "color": "#EADA50",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return


def end(game_state):
    return


def move(game_state):
    chosen = None
    try:
        chosen = _pick_original_move(game_state)
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        chosen = None

    # Validate the chosen move is actually legal in the v1 frame; if not, or if
    # the logic returned nothing, fall back to a guaranteed-safe move.
    try:
        board = game_state['board']
        W, H = board['width'], board['height']
        head = game_state['you']['body'][0]
        occupied = set()
        for s in board['snakes']:
            for b in s['body']:
                occupied.add((b['x'], b['y']))
        deltas = {'up': (0, 1), 'down': (0, -1), 'left': (-1, 0), 'right': (1, 0)}
        if chosen in deltas:
            dx, dy = deltas[chosen]
            nx, ny = head['x'] + dx, head['y'] + dy
            if not (0 <= nx < W and 0 <= ny < H) or (nx, ny) in occupied:
                chosen = _safe_move(game_state)
        else:
            chosen = _safe_move(game_state)
    except Exception:
        chosen = 'up'

    return {"move": chosen}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
