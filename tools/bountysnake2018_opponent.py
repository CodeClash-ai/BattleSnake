import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
Son of Robosnake (SoR) - rdbrck's 2018 Battlesnake bounty entry.
Port of https://github.com/rdbrck/bountysnake2018 (Lua) to the current
Battlesnake v1 API, as a self-contained pure-stdlib Python bot.

FIDELITY: faithful. This reproduces the original alpha-beta pruning search
with the same board heuristic (flood-fill space control, trap detection,
food weighting, aggression toward the enemy head, edge avoidance, and
percent-accessible scaling). The original ran on a 17x17/200ms bounty; here
search depth and a wall-clock guard keep it fast on any board size.

Original config (config/server.prod.conf):
    MAX_RECURSION_DEPTH = int(os.environ.get("BOUNTY_MAX_DEPTH", "6"))
    HUNGER_HEALTH = 40
    LOW_FOOD = 8

Grid tile semantics (from the Lua):
    '.' empty   'O' food   '@' head   '#' body   '*' tail (enterable)
Safe-to-move squares are '.', 'O', '*'.

Coordinate note: the 2018 bot used the OLD API (top-left origin, y-down) and
1-based indexing. This port uses the v1 API directly (bottom-left origin,
y-up) with a dict grid keyed by (x, y), so no remapping of directions is
needed -- up = y+1, down = y-1, left = x-1, right = x+1.
"""

import sys
import time
import random

# ----- Original configuration -----------------------------------------------
MAX_RECURSION_DEPTH = int(os.environ.get("BOUNTY_MAX_DEPTH", "6"))
HUNGER_HEALTH = 40
LOW_FOOD = 8

# Wall-clock guard: bail out of the search once we've spent this long so we
# always respond well under the API timeout on an 11x11 board.
TIME_LIMIT = float(os.environ.get("BOUNTY_TIME_LIMIT", "0.03"))

INT_MAX = 2147483647
INT_MIN = -2147483648


# ----- Utilities (util.lua) --------------------------------------------------

def mdist(src, dst):
    """Manhattan distance between two {x,y} points."""
    return abs(src['x'] - dst['x']) + abs(src['y'] - dst['y'])


def direction(src, dst):
    """Direction name to move from src to dst (v1: y-up)."""
    if dst['x'] == src['x'] + 1 and dst['y'] == src['y']:
        return 'right'
    if dst['x'] == src['x'] - 1 and dst['y'] == src['y']:
        return 'left'
    if dst['x'] == src['x'] and dst['y'] == src['y'] + 1:
        return 'up'
    if dst['x'] == src['x'] and dst['y'] == src['y'] - 1:
        return 'down'
    return 'up'


def build_world_map(width, height, food, snakes):
    """Build the tile grid as a dict keyed by (x, y).

    Mirrors util.buildWorldMap: heads are '@', interior body '#', tail '*'
    (unless overlapping a head/body of the same or another snake).
    """
    grid = {}
    for y in range(height):
        for x in range(width):
            grid[(x, y)] = '.'

    for f in food:
        grid[(f['x'], f['y'])] = 'O'

    for snake in snakes:
        body = snake['body']
        length = len(body)
        for j, seg in enumerate(body):
            key = (seg['x'], seg['y'])
            if key not in grid:
                continue
            if j == 0:
                grid[key] = '@'
            elif j == length - 1:
                if grid[key] not in ('@', '#'):
                    grid[key] = '*'
            else:
                if grid[key] != '@':
                    grid[key] = '#'
    return grid


# ----- Algorithm (algorithm.lua) --------------------------------------------

def is_safe_square(v, failsafe=False):
    if failsafe:
        return True
    return v == '.' or v == 'O' or v == '*'


def is_safe_square_floodfill(v):
    return v == '.' or v == 'O' or v == '*'


def neighbours(pos, grid, width, height, failsafe=False):
    """Set of adjacent squares that are safe to move into (v1 coords)."""
    result = []
    x, y = pos['x'], pos['y']
    candidates = [
        {'x': x, 'y': y + 1},  # up
        {'x': x, 'y': y - 1},  # down
        {'x': x + 1, 'y': y},  # right
        {'x': x - 1, 'y': y},  # left
    ]
    for c in candidates:
        if 0 <= c['x'] < width and 0 <= c['y'] < height:
            if is_safe_square(grid[(c['x'], c['y'])], failsafe):
                result.append(c)
    return result


def floodfill(pos, grid, num_safe, length, width, height):
    """Iterative flood fill (stack-based) counting reachable squares up to
    a maximum depth of `length`. Mutates `grid` (work on a copy)."""
    stack = [pos]
    while stack:
        if num_safe >= length:
            return num_safe
        p = stack.pop()
        key = (p['x'], p['y'])
        if is_safe_square_floodfill(grid.get(key, '#')):
            grid[key] = 1
            num_safe += 1
            x, y = p['x'], p['y']
            for c in (
                {'x': x, 'y': y + 1},
                {'x': x, 'y': y - 1},
                {'x': x + 1, 'y': y},
                {'x': x - 1, 'y': y},
            ):
                if 0 <= c['x'] < width and 0 <= c['y'] < height:
                    stack.append(c)
    return num_safe


def heuristic(grid, state, my_moves, enemy_moves, width, height):
    """The board/gamestate scoring function (algorithm.lua heuristic)."""
    score = 0
    me = state['me']
    enemy = state['enemy']
    me_body = me['body']
    enemy_body = enemy['body']
    me_head = me_body[0]
    enemy_head = enemy_body[0]

    # Head-on-head collision.
    if me_head['x'] == enemy_head['x'] and me_head['y'] == enemy_head['y']:
        if len(me_body) > len(enemy_body):
            # Original does NOT early-return here: it adds INT_MAX to the
            # score and falls through to the rest of the heuristic.
            score += INT_MAX
        elif len(me_body) < len(enemy_body):
            return INT_MIN
        else:
            # draws better than losing (bounty needs a clear winner)
            return -2147483647

    # My win/loss conditions
    if len(my_moves) == 0:
        return INT_MIN
    if me['health'] <= 0:
        return INT_MIN

    # Collect food from the grid
    food = []
    for (x, y), v in grid.items():
        if v == 'O':
            food.append({'x': x, 'y': y})

    board_size = width * height

    # Flood fill from my head.
    ff_grid = dict(grid)
    ff_grid[(me_head['x'], me_head['y'])] = '.'
    ff_depth = (2 * len(me_body)) + len(food)
    accessible = floodfill(me_head, ff_grid, 0, ff_depth, width, height)
    percent_accessible = accessible / board_size

    # Possible trap for me.
    if accessible <= len(me_body):
        return -9999999 * (1 / percent_accessible)

    # Enemy win/loss conditions
    if len(enemy_moves) == 0:
        score += INT_MAX
    if enemy['health'] <= 0:
        score += INT_MAX

    # Flood fill from enemy head.
    eff_grid = dict(grid)
    eff_grid[(enemy_head['x'], enemy_head['y'])] = '.'
    eff_depth = (2 * len(enemy_body)) + len(food)
    enemy_accessible = floodfill(enemy_head, eff_grid, 0, eff_depth,
                                 width, height)

    if enemy_accessible <= len(enemy_body):
        score += 9999999

    # Food weighting.
    food_weight = 0
    if len(food) <= LOW_FOOD:
        food_weight = 200 - (2 * me['health'])
    else:
        if me['health'] <= HUNGER_HEALTH or len(me_body) < 4:
            food_weight = 100 - me['health']
    if food_weight > 0:
        for i, f in enumerate(food):
            dist = mdist(me_head, f)
            # Original: score = score - (dist * foodWeight) - i, where i is
            # the 1-based loop index used to break ties between equidistant
            # food. Both terms are SUBTRACTED.
            score -= (dist * food_weight) + (i + 1)

    # Aggression: hang out near the enemy's head.
    aggressive_weight = 100
    if len(food) <= LOW_FOOD:
        aggressive_weight = me['health']
    kill_squares = neighbours(enemy_head, grid, width, height)
    enemy_last_direction = None
    if len(enemy_body) >= 2:
        enemy_last_direction = direction(enemy_body[1], enemy_body[0])
    for ks in kill_squares:
        dist = mdist(me_head, ks)
        d = direction(enemy_head, ks)
        if enemy_last_direction is not None and d == enemy_last_direction:
            score -= dist * (2 * aggressive_weight)
        else:
            score -= dist * aggressive_weight

    # Avoid the edge of the game board.
    if (me_head['x'] == 0 or me_head['x'] == width - 1
            or me_head['y'] == 0 or me_head['y'] == height - 1):
        score -= 25000

    # Scale by percent accessible.
    if score < 0:
        score = score * (1 / percent_accessible)
    elif score > 0:
        score = score * percent_accessible

    return score


def _advance(grid, snake, move, width, height):
    """Advance one snake by `move` on a fresh grid+snake, returning
    (new_grid, new_snake). Mirrors the per-move grid/state bookkeeping in
    algorithm.alphabeta (works on copies)."""
    new_grid = dict(grid)
    body = [dict(seg) for seg in snake['body']]
    new_snake = {'health': snake['health'], 'body': body,
                 'id': snake.get('id'), 'name': snake.get('name', '')}

    eating = new_grid.get((move['x'], move['y'])) == 'O'
    if eating:
        new_snake['health'] = 100
    else:
        new_snake['health'] = new_snake['health'] - 1

    length = len(body)
    # remove tail from map ONLY if not stacked on the segment before it
    if length > 1 and (body[length - 1]['x'] == body[length - 2]['x']
                       and body[length - 1]['y'] == body[length - 2]['y']):
        pass
    else:
        tail = body[length - 1]
        new_grid[(tail['x'], tail['y'])] = '.'

    # always remove tail from state
    old_tail = body.pop()

    # move head on grid (old head becomes body)
    if length > 1:
        new_grid[(body[0]['x'], body[0]['y'])] = '#'
    body.insert(0, {'x': move['x'], 'y': move['y']})
    new_grid[(move['x'], move['y'])] = '@'

    # if eating, grow (re-add a tail segment where the old tail was)
    if eating:
        body.append({'x': old_tail['x'], 'y': old_tail['y']})

    # mark tail square
    length = len(body)
    if length > 1 and (body[length - 1]['x'] == body[length - 2]['x']
                       and body[length - 1]['y'] == body[length - 2]['y']):
        new_grid[(body[length - 1]['x'], body[length - 1]['y'])] = '#'
    else:
        new_grid[(body[length - 1]['x'], body[length - 1]['y'])] = '*'

    return new_grid, new_snake


def alphabeta(grid, state, depth, alpha, beta, alpha_move, beta_move,
              maximizing, prev_grid, prev_enemy_moves, width, height,
              deadline):
    """Alpha-beta pruning. Returns (score, best_move)."""
    me = state['me']
    enemy = state['enemy']
    my_moves = neighbours(me['body'][0], grid, width, height)
    if maximizing:
        enemy_moves = neighbours(enemy['body'][0], grid, width, height)
    else:
        enemy_moves = prev_enemy_moves

    moves = my_moves if maximizing else enemy_moves

    me_head = me['body'][0]
    enemy_head = enemy['body'][0]
    endgame = (
        depth == MAX_RECURSION_DEPTH
        or len(moves) == 0
        or me['health'] <= 0
        or enemy['health'] <= 0
        or (me_head['x'] == enemy_head['x'] and me_head['y'] == enemy_head['y'])
        or time.time() > deadline
    )
    if endgame:
        return heuristic(grid, state, my_moves, enemy_moves, width, height), \
            (alpha_move if maximizing else beta_move)

    if maximizing:
        for m in moves:
            new_grid, new_me = _advance(grid, me, m, width, height)
            new_state = {'me': new_me, 'enemy': enemy}
            new_alpha, _ = alphabeta(
                new_grid, new_state, depth + 1, alpha, beta,
                alpha_move, beta_move, False, grid, enemy_moves,
                width, height, deadline)
            if new_alpha > alpha:
                alpha = new_alpha
                alpha_move = m
            if beta <= alpha:
                break
        return alpha, alpha_move
    else:
        for m in moves:
            new_grid, new_enemy = _advance(prev_grid, enemy, m, width, height)
            new_state = {'me': me, 'enemy': new_enemy}
            new_beta, _ = alphabeta(
                new_grid, new_state, depth + 1, alpha, beta,
                alpha_move, beta_move, True, None, None,
                width, height, deadline)
            if new_beta < beta:
                beta = new_beta
                beta_move = m
            if beta <= alpha:
                break
        return beta, beta_move


def n_complement(set1, set2):
    """Values of set1 that don't appear in set2 (coordinate pairs)."""
    out = []
    for a in set1:
        found = False
        for b in set2:
            if a['x'] == b['x'] and a['y'] == b['y']:
                found = True
                break
        if not found:
            out.append(a)
    return out


# ----- Battlesnake v1 API ----------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "rdbrck",
        "color": "#5DD284",
        "head": "bendr",
        "tail": "fat-rattle",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _choose_move(game_state):
    board = game_state['board']
    width = board['width']
    height = board['height']
    food = board.get('food', [])
    snakes = board.get('snakes', [])
    you = game_state['you']

    grid = build_world_map(width, height, food, snakes)

    me = {
        'id': you['id'],
        'name': you.get('name', ''),
        'health': you['health'],
        'body': [dict(s) for s in you['body']],
    }

    # Pick the closest enemy (as the original does).
    enemy = None
    best = 99999
    for s in snakes:
        if s['id'] == me['id']:
            continue
        d = mdist(me['body'][0], s['body'][0])
        if d < best:
            best = d
            enemy = {
                'id': s['id'],
                'name': s.get('name', ''),
                'health': s['health'],
                'body': [dict(b) for b in s['body']],
            }
    if enemy is None:
        # Alone in the arena: predict our own behavior.
        enemy = {
            'id': me['id'],
            'name': me['name'],
            'health': me['health'],
            'body': [dict(b) for b in me['body']],
        }

    state = {'me': me, 'enemy': enemy}
    deadline = time.time() + TIME_LIMIT

    best_score, best_move = alphabeta(
        grid, state, 0, float('-inf'), float('inf'),
        None, None, True, None, None, width, height, deadline)

    # FAILSAFE #1
    if best_move is None:
        my_moves = neighbours(me['body'][0], grid, width, height)
        enemy_moves = neighbours(enemy['body'][0], grid, width, height)
        safe_moves = n_complement(my_moves, enemy_moves)
        if len(me['body']) <= len(enemy['body']) and len(safe_moves) > 0:
            my_moves = safe_moves
        if len(my_moves) > 0:
            best_move = random.choice(my_moves)
        else:
            # Prefer snake deaths over wall deaths.
            my_moves = neighbours(me['body'][0], grid, width, height,
                                  failsafe=True)
            if my_moves:
                best_move = random.choice(my_moves)

    # FAILSAFE #2: guaranteed valid response.
    if best_move is None:
        head = me['body'][0]
        best_move = {'x': head['x'] - 1, 'y': head['y']}

    return direction(me['body'][0], best_move)


def move(game_state):
    try:
        return {"move": _choose_move(game_state)}
    except Exception:
        # Absolute last resort: find any in-bounds, non-body square.
        try:
            board = game_state['board']
            width, height = board['width'], board['height']
            you = game_state['you']
            head = you['body'][0]
            occupied = set()
            for s in board.get('snakes', []):
                body = s['body']
                for seg in body[:-1]:  # tails are enterable
                    occupied.add((seg['x'], seg['y']))
            options = [
                ('up', head['x'], head['y'] + 1),
                ('down', head['x'], head['y'] - 1),
                ('left', head['x'] - 1, head['y']),
                ('right', head['x'] + 1, head['y']),
            ]
            for name, nx, ny in options:
                if 0 <= nx < width and 0 <= ny < height \
                        and (nx, ny) not in occupied:
                    return {"move": name}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
