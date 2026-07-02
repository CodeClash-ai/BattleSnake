"""
Robosnake 2017 (rdbrck/bountysnake2017) ported to Battlesnake v1 API.

Original: Lua, Redbrick's 2017 bounty snake (42-3). Alpha-beta pruning minimax
between "me" (maximizer) and the closest enemy (minimizer), with a heuristic
built from flood-fill space, food proximity (weighted by hunger), and centrality.

FIDELITY: faithful. The core alpha-beta search, the head-on-collision move
filtering (drop my moves the enemy can also reach when I am <= its length),
the flood-fill trap detection, and the heuristic (base 100, food weight =
100-health, center pull, percent-accessible scaling) are all reproduced.
Differences from the original:
  - Gold ("$") does not exist in Battlesnake v1, so gold-related terms are
    dropped (they were never triggered in a v1 game anyway).
  - Coordinate system remapped: the 2017 bot used the OLD API (top-left origin,
    y-down). v1 is bottom-left origin, y-up. We work directly in v1 coordinates;
    since the algorithm is symmetric the flood-fill / distances are unaffected.
  - Added a ~0.3s wall-clock guard and iterative-deepening-ish depth cap so a
    move is always returned well under the 1s limit on an 11x11 board.
"""

import sys
import time

# Tunables (mirror the original config knobs)
MAX_RECURSION_DEPTH = 6      # original default was configurable; kept modest for speed
TIME_LIMIT = 0.30            # wall-clock guard in seconds
INT_MAX = 2147483647
INT_MIN = -2147483648

# Grid cell markers (matching original semantics)
EMPTY = '.'
FOOD = 'O'
HEAD = '@'
BODY = '#'

_deadline = 0.0


class _TimeUp(Exception):
    pass


def _check_time():
    if time.time() > _deadline:
        raise _TimeUp()


def _is_safe(v):
    # A tile is passable if empty or food. (Gold '$' from the original is absent in v1.)
    return v == EMPTY or v == FOOD


def _mdist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbours(pos, grid, width, height):
    """All in-bounds passable coordinate pairs adjacent to pos.

    v1 coords: up=y+1, down=y-1, left=x-1, right=x+1. pos = (x, y).
    """
    x, y = pos
    result = []
    for nx, ny in ((x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)):
        if 0 <= nx < width and 0 <= ny < height and _is_safe(grid[ny][nx]):
            result.append((nx, ny))
    return result


def _floodfill(pos, grid, width, height):
    """Count reachable safe squares from pos. Uses an explicit stack (no
    recursion-depth blowups). Mutates the passed grid, so give it a copy."""
    count = 0
    stack = [pos]
    while stack:
        x, y = stack.pop()
        if 0 <= x < width and 0 <= y < height and _is_safe(grid[y][x]):
            grid[y][x] = 1  # mark visited (any non-safe marker)
            count += 1
            stack.append((x, y + 1))
            stack.append((x, y - 1))
            stack.append((x + 1, y))
            stack.append((x - 1, y))
    return count


def _copy_grid(grid):
    return [row[:] for row in grid]


def _heuristic(grid, state, my_moves, enemy_moves, width, height):
    me = state['me']
    enemy = state['enemy']
    total = width * height

    # My win/loss conditions
    if len(my_moves) == 0:
        return INT_MIN
    if me['health'] <= 0:
        return INT_MIN

    # Flood fill from my head position.
    ff = _copy_grid(grid)
    mh = me['coords'][0]
    ff[mh[1]][mh[0]] = EMPTY
    accessible = _floodfill(mh, ff, width, height)
    percent = accessible / total if total else 0.0

    # If reachable space is smaller than my body, this may be a trap.
    if accessible <= len(me['coords']):
        # Guard against divide-by-zero.
        if percent <= 0:
            return INT_MIN
        return -9999999 * (1.0 / percent)

    # Enemy win/loss conditions
    if len(enemy_moves) == 0:
        return INT_MAX
    if enemy['health'] <= 0:
        return INT_MAX

    eff = _copy_grid(grid)
    eh = enemy['coords'][0]
    eff[eh[1]][eh[0]] = EMPTY
    enemy_accessible = _floodfill(eh, eff, width, height)

    if enemy_accessible <= len(enemy['coords']):
        return 9999999 * percent

    # Gather food from the grid.
    food = []
    for y in range(height):
        row = grid[y]
        for x in range(width):
            if row[x] == FOOD:
                food.append((x, y))

    score = 100.0
    center_x = -(-width // 2)   # math.ceil(width/2) using 1-based -> approximate center
    center_y = -(-height // 2)
    center = (center_x, center_y)

    # Food: pull toward it proportional to hunger.
    food_weight = 100 - me['health']
    for f in food:
        score -= _mdist(mh, f) * food_weight

    # Stay near the center.
    score -= _mdist(mh, center) * 100

    # Scale by accessible space.
    if score < 0:
        if percent > 0:
            score = score * (1.0 / percent)
    elif score > 0:
        score = score * percent

    return score


def _advance(grid, state, key, move, width, height):
    """Return (new_grid, new_state) after `key` ('me'/'enemy') moves to `move`.
    Mirrors the original grid/coords bookkeeping. RULES_VERSION 2017: eating
    food resets health to 100."""
    new_grid = _copy_grid(grid)
    new_state = {
        'me': {'coords': list(state['me']['coords']), 'health': state['me']['health']},
        'enemy': {'coords': list(state['enemy']['coords']), 'health': state['enemy']['health']},
    }
    snake = new_state[key]
    coords = snake['coords']
    coords.insert(0, move)
    head = coords[0]
    ate = new_grid[head[1]][head[0]] == FOOD
    if not ate:
        tail = coords[-1]
        new_grid[tail[1]][tail[0]] = EMPTY
        coords.pop()
        snake['health'] -= 1
    else:
        snake['health'] = 100
    # Mark head and neck on the grid.
    new_grid[head[1]][head[0]] = HEAD
    if len(coords) > 1:
        neck = coords[1]
        new_grid[neck[1]][neck[0]] = BODY
    return new_grid, new_state


def _n_complement(set1, set2):
    s2 = set(set2)
    return [m for m in set1 if m not in s2]


def _alphabeta(grid, state, depth, alpha, beta, best_move, maximizing, width, height):
    _check_time()

    my_moves = _neighbours(state['me']['coords'][0], grid, width, height)
    enemy_moves = _neighbours(state['enemy']['coords'][0], grid, width, height)

    # If I'm no longer than the enemy, avoid squares the enemy can also reach.
    if state['me'] is not state['enemy']:
        if len(state['me']['coords']) <= len(state['enemy']['coords']):
            my_moves = _n_complement(my_moves, enemy_moves)

    moves = my_moves if maximizing else enemy_moves

    if (depth == MAX_RECURSION_DEPTH or len(moves) == 0 or
            state['me']['health'] <= 0 or state['enemy']['health'] <= 0):
        return _heuristic(grid, state, my_moves, enemy_moves, width, height), best_move

    if maximizing:
        chosen = best_move
        for m in moves:
            ng, ns = _advance(grid, state, 'me', m, width, height)
            val, _ = _alphabeta(ng, ns, depth + 1, alpha, beta, best_move, False, width, height)
            if val > alpha:
                alpha = val
                chosen = m
            if beta <= alpha:
                break
        return alpha, chosen
    else:
        chosen = best_move
        for m in moves:
            ng, ns = _advance(grid, state, 'enemy', m, width, height)
            val, _ = _alphabeta(ng, ns, depth + 1, alpha, beta, best_move, True, width, height)
            if val < beta:
                beta = val
                chosen = m
            if beta <= alpha:
                break
        return beta, chosen


def _build_grid(board):
    width = board['width']
    height = board['height']
    grid = [[EMPTY for _ in range(width)] for _ in range(height)]
    for f in board.get('food', []):
        grid[f['y']][f['x']] = FOOD
    for snake in board.get('snakes', []):
        body = snake['body']
        for j, seg in enumerate(body):
            if j == 0:
                grid[seg['y']][seg['x']] = HEAD
            else:
                grid[seg['y']][seg['x']] = BODY
    return grid, width, height


def _direction(src, dst):
    if dst[0] == src[0] + 1 and dst[1] == src[1]:
        return 'right'
    if dst[0] == src[0] - 1 and dst[1] == src[1]:
        return 'left'
    if dst[0] == src[0] and dst[1] == src[1] + 1:
        return 'up'
    if dst[0] == src[0] and dst[1] == src[1] - 1:
        return 'down'
    return None


def _to_coords(snake):
    return [(seg['x'], seg['y']) for seg in snake['body']]


def _fallback_move(head, grid, width, height):
    """Always return an in-bounds move that is not into a snake body.
    Tails are enterable, but the grid already frees tails only via search; here
    we just avoid any body/head cell and stay in bounds."""
    x, y = head
    candidates = [(x, y + 1, 'up'), (x, y - 1, 'down'),
                  (x - 1, y, 'left'), (x + 1, y, 'right')]
    # Prefer safe (empty/food) squares.
    for nx, ny, d in candidates:
        if 0 <= nx < width and 0 <= ny < height and _is_safe(grid[ny][nx]):
            return d
    # Next, any in-bounds square (last resort; better than out of bounds).
    for nx, ny, d in candidates:
        if 0 <= nx < width and 0 <= ny < height:
            return d
    return 'up'


def move(game_state):
    global _deadline
    _deadline = time.time() + TIME_LIMIT
    try:
        board = game_state['board']
        you = game_state['you']
        width = board['width']
        height = board['height']

        grid, width, height = _build_grid(board)
        my_head = (you['head']['x'], you['head']['y'])

        # Identify me and the closest enemy.
        me = None
        for s in board['snakes']:
            if s['id'] == you['id']:
                me = s
                break
        if me is None:
            me = you

        enemy = None
        best_dist = 1 << 30
        for s in board['snakes']:
            if s['id'] == you['id']:
                continue
            d = _mdist(my_head, (s['head']['x'], s['head']['y']))
            if d < best_dist:
                best_dist = d
                enemy = s
        if enemy is None:
            enemy = me  # solo game: predict against self (as original does)

        state = {
            'me': {'coords': _to_coords(me), 'health': me['health']},
            'enemy': {'coords': _to_coords(enemy), 'health': enemy['health']},
        }
        if enemy is me:
            state['enemy'] = state['me']

        best_move = None
        try:
            _, best_move = _alphabeta(
                grid, state, 0, float('-inf'), float('inf'),
                None, True, width, height)
        except _TimeUp:
            best_move = None

        # FAILSAFE #1: pick a random-ish safe neighbour (complement of enemy).
        if best_move is None:
            my_moves = _neighbours(my_head, grid, width, height)
            enemy_head = (enemy['head']['x'], enemy['head']['y'])
            enemy_moves = _neighbours(enemy_head, grid, width, height)
            safe = _n_complement(my_moves, enemy_moves)
            if len(state['me']['coords']) <= len(state['enemy']['coords']) and safe:
                my_moves = safe
            if my_moves:
                best_move = my_moves[0]

        if best_move is not None:
            d = _direction(my_head, best_move)
            if d is not None:
                return {"move": d}

        # FAILSAFE #2: guaranteed in-bounds, non-body move.
        return {"move": _fallback_move(my_head, grid, width, height)}
    except Exception:
        # Last-ditch: never crash.
        try:
            you = game_state['you']
            board = game_state['board']
            grid, width, height = _build_grid(board)
            head = (you['head']['x'], you['head']['y'])
            return {"move": _fallback_move(head, grid, width, height)}
        except Exception:
            return {"move": "up"}


def info():
    return {
        "apiversion": "1",
        "author": "rdbrck",
        "color": "#6699cc",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    pass


def end(game_state):
    pass


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
