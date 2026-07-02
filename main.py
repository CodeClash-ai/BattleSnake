"""
Port of nessegrev-julia (Nettogrof) to Python for the Battlesnake v1 API.

Faithful reimplementation of the ORIGINAL Julia bot ("snack-a-tron" branch):
  - Tree search over combined moves of all snakes (Search.jl `multi`/`merge`/`clean`).
  - Leaf evaluation = ground-control flood-fill (Node.jl adjustGroundControl):
      * fixed 19x19 board grid, my head floods +35 (decreasing), opponents -35,
        boards summed; score[i] += 2 * (count / (19+19)).
  - Minimax aggregation (Node.jl updateScore): group children by our head,
      within a group opponents minimise my score / maximise theirs, then across
      groups pick the best score-ratio; plus mobility bonus 0.1*possibleMove.
  - scoreRatio = score[1] / (sum(score) + 1 - score[1]).
  - chooseBestMove: worst (min) ratio per direction, then best of those.
  - Head-to-head (clean): longer wins, equal length both die.

ORIGINAL quirks reproduced faithfully:
  - `multi` calls createNewSnake with eat=true ALWAYS, so during search every
    snake grows (tail never vacates, health resets to 100). This is the real
    original behaviour, not real food logic.
  - Ground-control grid + denominator are hardcoded 19x19, not the real board.

Coordinate note: the Julia code uses a v0 top-left origin (square = x*1000+y) and
flips up/down for the v1 API. Ground control is orientation-symmetric, so we work
directly in v1 space ((0,0) bottom-left) with no flip.

Performance: iterative expansion with a ~0.3s wall-clock guard and depth cap.
"""

import time

TIME_LIMIT = 0.30      # wall-clock guard (seconds)
MAX_DEPTH = 6          # search plies
FLOOD_START = 35       # Julia flood seed value
GRID = 19              # Julia adjustGroundControl hardcoded h=w=19
MOBILITY = 0.1         # Julia updateScore: score[1] += 0.1 * possibleMove


def info():
    return {
        "apiversion": "1",
        "author": "Nettogrof",
        "color": "#FFAAAA",
        "head": "shac-gamer",
        "tail": "shac-coffee",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---------------------------------------------------------------------------
# Snake model (SnakeInfo.jl)
# ---------------------------------------------------------------------------

class Snake:
    __slots__ = ("body", "health", "eat", "alive")

    def __init__(self, body, health, eat, alive):
        self.body = body            # list of (x, y), body[0] is head
        self.health = health
        self.eat = eat
        self.alive = alive

    def clone(self):
        return Snake(self.body, self.health, self.eat, self.alive)

    def head(self):
        return self.body[0]


def _is_snake(snake, sq):
    """isSnake: does this snake occupy sq next turn (tail enterable iff not eating)."""
    body = snake.body
    if snake.eat:
        return sq in body
    # not eating: the tail cell (last index) is enterable
    try:
        idx = body.index(sq)
    except ValueError:
        return False
    return idx < len(body) - 1


def _free_space(sq, snakes):
    for s in snakes:
        if _is_snake(s, sq):
            return False
    return True


def _create_new_snake(snake, new_head, eat):
    """createNewSnake (hazard always false in original `multi`)."""
    body = list(snake.body)
    health = snake.health
    alive = snake.alive
    if eat:
        health = 100
    else:
        health -= 1
    body.insert(0, new_head)
    if not eat:
        body.pop()
    if health <= 0:
        alive = False
    return Snake(body, health, eat, alive)


# ---------------------------------------------------------------------------
# Move generation (Search.jl multi / merge / clean)
# ---------------------------------------------------------------------------

def _multi(snake, width, height, all_snakes):
    """Legal next-states for one snake. NOTE: original always passes eat=True."""
    out = []
    if not snake.alive:
        return out
    hx, hy = snake.head()
    # order matches Julia: west(-x), east(+x), south(-y), north(+y)
    for nx, ny in ((hx - 1, hy), (hx + 1, hy), (hx, hy - 1), (hx, hy + 1)):
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        nh = (nx, ny)
        if _free_space(nh, all_snakes):
            out.append(_create_new_snake(snake, nh, True))  # eat=True, faithful
    return out


def _merge(list_of_combos, snake_options):
    if not snake_options:
        return list_of_combos
    if not list_of_combos:
        return [[opt] for opt in snake_options]
    ret = []
    for opt in snake_options:
        for combo in list_of_combos:
            new_combo = [s.clone() for s in combo]
            new_combo.append(opt.clone())
            ret.append(new_combo)
    return ret


def _clean(combos):
    """Head-to-head resolution: longer wins, equal both die."""
    for combo in combos:
        n = len(combo)
        for i in range(n - 1):
            for j in range(i + 1, n):
                if combo[i].body[0] == combo[j].body[0]:
                    li = len(combo[i].body)
                    lj = len(combo[j].body)
                    if li > lj:
                        combo[j].alive = False
                    elif li == lj:
                        combo[i].alive = False
                        combo[j].alive = False
                    else:
                        combo[i].alive = False


# ---------------------------------------------------------------------------
# Ground-control flood fill (Node.jl adjustGroundControl / floodpos / floodneg)
# ---------------------------------------------------------------------------

def _flood(board, x, y, value, sign):
    """
    Recursive flood matching floodpos/floodneg on a fixed GRID x GRID board.
    board maps (x,y)->int. Bodies pre-marked -99. sign=+1 positive, -1 negative.
    Positive: write iff cell >= 0 and cell < value (value decreases from 35).
    Negative: write iff cell > value (value increases from -35 toward -1).
    Bounds: positive uses GRID-2, negative uses GRID-1 (as in the Julia code).
    """
    stack = [(x, y, value)]
    if sign > 0:
        lim = GRID - 2
        while stack:
            cx, cy, v = stack.pop()
            cur = board.get((cx, cy), 0)
            if not (cur >= 0 and cur < v):
                continue
            board[(cx, cy)] = v
            if v > 1:
                nv = v - 1
                if cy < lim:
                    stack.append((cx, cy + 1, nv))
                if cx < lim:
                    stack.append((cx + 1, cy, nv))
                if cy > 0:
                    stack.append((cx, cy - 1, nv))
                if cx > 0:
                    stack.append((cx - 1, cy, nv))
    else:
        lim = GRID - 1
        while stack:
            cx, cy, v = stack.pop()
            cur = board.get((cx, cy), 0)
            if not (cur > v):
                continue
            board[(cx, cy)] = v
            if v < -1:
                nv = v + 1
                if cy < lim:
                    stack.append((cx, cy + 1, nv))
                if cx < lim:
                    stack.append((cx + 1, cy, nv))
                if cy > 0:
                    stack.append((cx, cy - 1, nv))
                if cx > 0:
                    stack.append((cx - 1, cy, nv))


def _adjust_ground_control(snakes, score):
    # positive board and negative board, bodies = -99
    pos = {}
    neg = {}
    for s in snakes:
        for (bx, by) in s.body:
            pos[(bx, by)] = -99
            neg[(bx, by)] = -99

    me = snakes[0]
    mh = me.head()
    pos[mh] = 0
    _flood(pos, mh[0], mh[1], FLOOD_START, +1)

    for i in range(1, len(snakes)):
        oh = snakes[i].head()
        neg[oh] = 0
        _flood(neg, oh[0], oh[1], -FLOOD_START, -1)

    cp = 0
    cn = 0
    cells = set(pos) | set(neg)
    for cell in cells:
        final = pos.get(cell, 0) + neg.get(cell, 0)
        if final > 0:
            cp += 1
        elif final < 0 and final != -99:
            cn += 1

    denom = float(GRID + GRID)   # hardcoded 38, per original
    score[0] += 2.0 * (cp / denom)
    for i in range(1, len(snakes)):
        score[i] += 2.0 * (cn / denom)


def _set_score(snakes):
    """setScore (snack-a-tron branch)."""
    n = len(snakes)
    score = [0.0] * n
    _adjust_ground_control(snakes, score)
    if n == 1:
        score[0] += 1000.0
    # nbAlive < 2 -> terminal (handled by not recursing); no extra score change
    return score


def _score_ratio(score):
    return score[0] / (sum(score) + 1.0 - score[0])


# ---------------------------------------------------------------------------
# Search (Search.jl generateChild + Node.jl updateScore)
# ---------------------------------------------------------------------------

def _aggregate(children, n_snakes):
    """
    updateScore aggregation over a node's children.
      possibleMove == 1  -> single group: min my score, max others.
      possibleMove  > 1  -> group by our head; within group min mine / max theirs;
                            across groups pick best ratio (mine / sum others).
    children: list of (our_head, score_vec, alive_flag) ... but original groups
    on child.snakes[1].body[1] and uses child score directly.
    Returns aggregated score vector for the parent.
    """
    if not children:
        return [0.0] * n_snakes

    # group by our head
    groups = {}
    order = []
    for head, vec in children:
        if head not in groups:
            groups[head] = list(vec)
            order.append(head)
        else:
            g = groups[head]
            g[0] = min(g[0], vec[0])
            for i in range(1, len(g)):
                g[i] = max(g[i], vec[i])

    if len(groups) == 1:
        # possibleMove == 1 style: single min/max group already computed
        return groups[order[0]]

    best_ratio = None
    best_vec = None
    for head in order:
        g = groups[head]
        other = sum(g[1:])
        ratio = g[0] / other if other != 0 else (g[0] / 1e-9 if g[0] else 0.0)
        if best_ratio is None or ratio > best_ratio:
            best_ratio = ratio
            best_vec = g
    return best_vec if best_vec is not None else [0.0] * n_snakes


def _search(snakes, width, height, depth, deadline):
    n = len(snakes)
    me = snakes[0]
    if not me.alive:
        return [0.0] * n

    if depth <= 0 or time.time() > deadline:
        s = _set_score(snakes)
        if s[0] != 0:
            s[0] += MOBILITY * _count_moves(me, width, height, snakes)
        return s

    my_moves = _multi(me, width, height, snakes)
    possible = len(my_moves)
    if possible == 0:
        return [0.0] * n  # trapped -> die, score 0

    combos = _merge([], my_moves)
    for i in range(1, n):
        combos = _merge(combos, _multi(snakes[i], width, height, snakes))
    _clean(combos)

    still_alive = False
    children = []
    for combo in combos:
        head = combo[0].head()
        if combo[0].alive:
            cs = _search(combo, width, height, depth - 1, deadline)
            still_alive = True
        else:
            cs = [0.0] * n
        children.append((head, cs))
        if time.time() > deadline:
            break

    if not still_alive:
        return [0.0] * n

    agg = _aggregate(children, n)
    if agg[0] != 0:
        agg[0] += MOBILITY * possible
    return agg


def _count_moves(snake, width, height, snakes):
    return len(_multi(snake, width, height, snakes))


# ---------------------------------------------------------------------------
# Move entry point (MainSnake.jl move / chooseBestMove)
# ---------------------------------------------------------------------------

def _build_snakes(game_state):
    board = game_state["board"]
    you_id = game_state["you"]["id"]

    def mk(s):
        body = [(p["x"], p["y"]) for p in s["body"]]
        health = s.get("health", 100)
        return Snake(body, health, health == 100, True)   # initSnake: eat = health==100

    snakes = [mk(game_state["you"])]
    for s in board["snakes"]:
        if s["id"] != you_id:
            snakes.append(mk(s))
    return snakes


def _safe_fallback(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    snakes = _build_snakes(game_state)
    hx, hy = snakes[0].head()
    for name, (dx, dy) in (("up", (0, 1)), ("down", (0, -1)),
                           ("left", (-1, 0)), ("right", (1, 0))):
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < w and 0 <= ny < h and _free_space((nx, ny), snakes):
            return name
    return "up"


def move(game_state):
    try:
        deadline = time.time() + TIME_LIMIT
        board = game_state["board"]
        w, h = board["width"], board["height"]
        snakes = _build_snakes(game_state)
        me = snakes[0]
        hx, hy = me.head()

        my_moves = _multi(me, w, h, snakes)
        if not my_moves:
            return {"move": _safe_fallback(game_state)}

        # Per chooseBestMove: gather child ratios per direction, take the WORST
        # (min) ratio per direction, then choose the direction with the best of
        # those worst-case ratios. Iterative deepening under the time guard.
        dir_scores = {"up": [], "down": [], "left": [], "right": []}

        for depth in range(2, MAX_DEPTH + 1):
            if time.time() > deadline:
                break
            local = {"up": [], "down": [], "left": [], "right": []}
            aborted = False
            for opt in my_moves:
                nx, ny = opt.head()
                if nx < hx:
                    d = "left"
                elif nx > hx:
                    d = "right"
                elif ny > hy:
                    d = "up"
                else:
                    d = "down"

                combos = _merge([], [opt])
                for i in range(1, len(snakes)):
                    combos = _merge(combos, _multi(snakes[i], w, h, snakes))
                _clean(combos)

                if not combos:
                    s = _set_score([opt] + [x.clone() for x in snakes[1:]])
                    local[d].append(_score_ratio(s))
                else:
                    children = []
                    for combo in combos:
                        head = combo[0].head()
                        if combo[0].alive:
                            cs = _search(combo, w, h, depth - 1, deadline)
                        else:
                            cs = [0.0] * len(snakes)
                        children.append((head, cs))
                        if time.time() > deadline:
                            aborted = True
                            break
                    # ratio for this first-move child group
                    for _, cs in children:
                        local[d].append(_score_ratio(cs))
                if aborted:
                    break
            if not aborted:
                dir_scores = local
            else:
                if not any(dir_scores.values()):
                    dir_scores = local
                break

        best_dir = None
        best_val = None
        for d in ("up", "down", "left", "right"):
            vals = dir_scores[d]
            if not vals:
                continue
            worst = min(vals)
            if best_val is None or worst > best_val:
                best_val = worst
                best_dir = d

        if best_dir is None:
            return {"move": _safe_fallback(game_state)}
        return {"move": best_dir}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
