"""
Port of nessegrev-julia (Nettogrof) to Python for the Battlesnake v1 API.

Faithful reimplementation of the ORIGINAL Julia bot's strategy:
  - Tree search over combined moves of all snakes (minimax-flavoured).
  - Leaf evaluation = "ground control" flood-fill (author's snack-a-tron scoring).
  - Head-to-head resolution: longer snake wins, equal length both die.
  - Score ratio = mine / (sum_others + 1); best move = the direction whose
    WORST child ratio is highest (see chooseBestMove in the original).

Notes on coordinate systems:
  The Julia code works in a v0 "top-left origin" space with square = x*1000+y
  and flips up/down at the very end for the v1 API. We work directly in the
  standard v1 space ((0,0) bottom-left, up = y+1) so no flip is needed; the
  strategy (flood control + ratio minimax) is orientation-independent.

Performance: iterative-deepening-style expansion with a ~0.3s wall-clock guard
and a hard depth cap, per the port requirements.
"""

import time

TIME_LIMIT = 0.30      # wall-clock guard (seconds)
MAX_DEPTH = 6          # hard cap on search plies
FLOOD_START = 35       # matches the Julia flood seed value


def info():
    return {
        "apiversion": "1",
        "author": "Nettogrof",
        "color": "#66ccff",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---------------------------------------------------------------------------
# Snake / board model
# ---------------------------------------------------------------------------

class Snake:
    __slots__ = ("body", "health", "eat", "alive")

    def __init__(self, body, health, eat, alive):
        # body is a list of (x, y) tuples, body[0] is the head
        self.body = body
        self.health = health
        self.eat = eat
        self.alive = alive

    def clone(self):
        return Snake(self.body, self.health, self.eat, self.alive)

    def head(self):
        return self.body[0]


def _occupies(snake, sq):
    """True if this snake occupies `sq` next turn (tail vacates unless eating)."""
    body = snake.body
    if sq not in body:
        return False
    if snake.eat:
        return True
    # not eating: tail moves off, so the last body cell is enterable
    idx = body.index(sq)
    return idx < len(body) - 1


def _free_space(sq, snakes):
    for s in snakes:
        if _occupies(s, sq):
            return False
    return True


def _new_snake(snake, new_head, eat):
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
# Move generation (mirrors Search.jl `multi`)
# ---------------------------------------------------------------------------

def _snake_moves(snake, width, height, all_snakes, food_set):
    """All legal next-states for one snake (in-bounds + not into a body)."""
    out = []
    if not snake.alive:
        return out
    hx, hy = snake.head()
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = hx + dx, hy + dy
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        nh = (nx, ny)
        if _free_space(nh, all_snakes):
            eat = nh in food_set
            out.append(_new_snake(snake, nh, eat))
    return out


def _merge(list_of_combos, snake_options):
    """Cartesian merge of combined-move lists (mirrors Search.jl `merge`)."""
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
    """Resolve head-to-head collisions (mirrors Search.jl `clean`)."""
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
# Leaf evaluation: ground control flood fill (mirrors Node.jl adjustGroundControl)
# ---------------------------------------------------------------------------

def _flood(seed, blocked, width, height, sign):
    """
    BFS flood assigning decreasing magnitude values from FLOOD_START, matching
    the recursive flood in the Julia code (distance-limited, blocked by bodies).
    Returns a dict {(x,y): value}.  sign is +1 for us, -1 for opponents.
    """
    field = {}
    start_val = FLOOD_START
    frontier = [(seed[0], seed[1], start_val)]
    field[seed] = sign * start_val
    while frontier:
        x, y, val = frontier.pop()
        if val <= 1:
            continue
        nval = val - 1
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            cell = (nx, ny)
            if cell in blocked:
                continue
            cur = field.get(cell)
            # only overwrite if strictly closer (higher magnitude), like the
            # `< value` guard in the Julia flood functions
            if cur is None or abs(cur) < nval:
                field[cell] = sign * nval
                frontier.append((nx, ny, nval))
    return field


def _evaluate(snakes, width, height):
    """
    Score vector. score[0] = us. Ground-control based, plus survival bonuses.
    Mirrors setScore/adjustGroundControl (snack-a-tron branch).
    """
    n = len(snakes)
    score = [0.0] * n

    # all body cells block flood
    blocked = set()
    for s in snakes:
        for cell in s.body:
            blocked.add(cell)

    me = snakes[0]
    if me.alive:
        my_field = _flood(me.head(), blocked - {me.head()}, width, height, +1)
    else:
        my_field = {}

    opp_field = {}
    for i in range(1, n):
        s = snakes[i]
        if not s.alive:
            continue
        f = _flood(s.head(), blocked - {s.head()}, width, height, -1)
        for cell, v in f.items():
            cur = opp_field.get(cell)
            if cur is None or v < cur:
                opp_field[cell] = v

    cp = 0
    cn = 0
    cells = set(my_field) | set(opp_field)
    for cell in cells:
        final = my_field.get(cell, 0) + opp_field.get(cell, 0)
        if final > 0:
            cp += 1
        elif final < 0:
            cn += 1

    denom = float(height + width)
    score[0] += 2.0 * (cp / denom)
    for i in range(1, n):
        score[i] += 2.0 * (cn / denom)

    # survival bonuses (setScore)
    if n > 1:
        alive = sum(1 for s in snakes if s.alive)
        # (a node with < 2 alive is terminal; handled by not recursing further)
    elif n == 1:
        score[0] += 1000.0

    if not me.alive:
        score[0] = 0.0

    return score


def _score_ratio(score):
    others = sum(score) - score[0]
    return score[0] / (others + 1.0)


# ---------------------------------------------------------------------------
# Search (mirrors run/generateChild + updateScore minimax)
# ---------------------------------------------------------------------------

def _search(snakes, width, height, food_set, depth, deadline):
    """
    Returns a score vector for the given position.
    Recursively expands combined moves; minimax-style aggregation via
    grouping children by our head (updateScore semantics).
    """
    me = snakes[0]
    if not me.alive:
        return [0.0] * len(snakes)

    if depth <= 0 or time.time() > deadline:
        return _evaluate(snakes, width, height)

    # generate my moves
    my_moves = _snake_moves(me, width, height, snakes, food_set)
    if not my_moves:
        s = [0.0] * len(snakes)
        return s  # trapped -> we die, score 0 for us

    # generate combined moves for all snakes
    combos = _merge([], my_moves)
    for i in range(1, len(snakes)):
        opts = _snake_moves(snakes[i], width, height, snakes, food_set)
        combos = _merge(combos, opts)
    _clean(combos)

    if not combos:
        return _evaluate(snakes, width, height)

    # group children by our head; for each group, opponents pick the response
    # that MINIMISES our score (min over group[0]), we take MAX over groups.
    groups = {}  # our_head -> list of child score vectors
    for combo in combos:
        child_snakes = combo
        if child_snakes[0].alive:
            cs = _search(child_snakes, width, height, food_set, depth - 1, deadline)
        else:
            cs = [0.0] * len(snakes)
        head = child_snakes[0].head()
        groups.setdefault(head, []).append(cs)
        if time.time() > deadline:
            break

    # aggregate: within a group opponents minimise our score[0] and maximise
    # theirs; across groups we choose the best ratio.
    best_ratio = None
    best_vec = None
    for head, vecs in groups.items():
        agg = list(vecs[0])
        agg[0] = min(v[0] for v in vecs)
        for i in range(1, len(agg)):
            agg[i] = max(v[i] for v in vecs)
        r = _score_ratio(agg)
        if best_ratio is None or r > best_ratio:
            best_ratio = r
            best_vec = agg

    return best_vec if best_vec is not None else _evaluate(snakes, width, height)


# ---------------------------------------------------------------------------
# Move entry point
# ---------------------------------------------------------------------------

def _build_snakes(game_state):
    board = game_state["board"]
    you_id = game_state["you"]["id"]

    def mk(s):
        body = [(p["x"], p["y"]) for p in s["body"]]
        health = s.get("health", 100)
        return Snake(body, health, health == 100, True)

    snakes = [mk(game_state["you"])]
    for s in board["snakes"]:
        if s["id"] != you_id:
            snakes.append(mk(s))
    return snakes


def _safe_fallback(game_state):
    """Any in-bounds move not into a snake body (tails enterable)."""
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
        food_set = {(f["x"], f["y"]) for f in board.get("food", [])}
        snakes = _build_snakes(game_state)

        me = snakes[0]
        hx, hy = me.head()

        # top-level legal moves
        my_moves = _snake_moves(me, w, h, snakes, food_set)
        if not my_moves:
            return {"move": _safe_fallback(game_state)}

        # For each direction, gather child ratios; per chooseBestMove we take
        # the WORST (min) ratio per direction, then the best of those.
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

                # build combined children rooted at this first move
                combos = _merge([], [opt])
                for i in range(1, len(snakes)):
                    opts = _snake_moves(snakes[i], w, h, snakes, food_set)
                    combos = _merge(combos, opts)
                _clean(combos)

                if not combos:
                    local[d].append(_score_ratio(_evaluate([opt] + snakes[1:], w, h)))
                else:
                    for combo in combos:
                        if combo[0].alive:
                            cs = _search(combo, w, h, food_set, depth - 1, deadline)
                        else:
                            cs = [0.0] * len(snakes)
                        local[d].append(_score_ratio(cs))
                        if time.time() > deadline:
                            aborted = True
                            break
                if aborted:
                    break
            if not aborted:
                dir_scores = local  # committed a full depth
            else:
                # partial: still use if we have nothing yet
                if not any(dir_scores.values()):
                    dir_scores = local
                break

        # choose direction with best worst-case ratio
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
