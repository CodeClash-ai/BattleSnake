"""CodeClash port of graeme-hill/snakebot ("Team Graeme & Chris").

Winner of Battlesnake Victoria 2018 Expert Division.

FIDELITY: faithful (structural approximation of the threaded C++ Sim within
one fast pure-stdlib file).

The original (C++) bot's flagship algorithm is `Sim` (sim.cpp): it forms
algorithm PAIRS = (myAlgorithm x enemyAlgorithm) where
  myAlgorithms  = { dog (with 12 two-move prefixes), cautious, inYourFace }
  enemyAlgos    = { hungry, inMyFace, left, right, up, down }
rolls each pair forward as a lightweight game simulation (newStateAfterMoves),
records obituaries + foods eaten, scores every resulting Future (scoreFuture),
then via bestMove() groups Futures by key=(myAlgorithm.name, prefix), takes the
WORST score within each key (maximin over enemy behaviours), and returns the
direction of the best-of-worst -- UNLESS every worst score < 1500, in which
case it "takes its chances" and returns the best-of-best. `preferred` (a +500
bonus in scoring) is dog.move(state) == chaseTail.

  Dog       = chaseTail -> notImmediatelySuicidal          (NO food seeking)
  Cautious  = bestFood  -> chaseTail -> notImmediatelySuicidal
  Hungry    = closestFood -> notImmediatelySuicidal

This port reproduces that faithfully within one fast file. For each safe first
move it runs the maximin over a set of enemy policies (hungry + fixed
directions), rolling my snake forward with the Cautious policy stack and each
enemy with its policy, scores every Future with the same scoreFuture heuristic
(same constants: IDEAL_HEALTH_AT_FOOD_TIME=100, food multipliers 200/100,
survival*100, murder (100-turn)*10000, preferred +500, corner-death cap 1000,
best-move threshold 1500), and picks via the same best-of-worst / best-of-best
logic. couldEndUpCornerAdjacentToBiggerSnake is ported cell-for-cell with the
y-axis flipped for the v1 API. Search is depth- and wall-clock-bounded.

COORDINATES: original is OLD-API (top-left origin, y-DOWN); this port targets
Battlesnake v1 (bottom-left origin, y-UP): up=y+1, down=y-1, left=x-1,
right=x+1. head=body[0]. Because the whole board is just mirrored across the
y-axis, every distance/flood-fill/path routine is invariant; only the hard-
coded diagonal geometry of couldEndUpCornerAdjacent needed its y offsets
negated (done below), and direction NAMES are emitted in v1 convention.
"""

import time

# ---- constants (from simulator.cpp) ----
IDEAL_HEALTH_AT_FOOD_TIME = 100
SEARCH_MAX_TURNS = 14          # how deep each simulated future rolls
TIME_BUDGET = 0.30             # wall-clock cap in seconds

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
DIR_LIST = ["up", "down", "left", "right"]


# ---------------------------------------------------------------------------
# Board model
# ---------------------------------------------------------------------------
class Board:
    """Lightweight, cheaply-copyable game state."""

    __slots__ = ("w", "h", "food", "snakes", "me_id")

    def __init__(self, w, h, food, snakes, me_id):
        self.w = w
        self.h = h
        self.food = food          # set of (x,y)
        # snakes: dict id -> dict(health, body=list[(x,y)])
        self.snakes = snakes
        self.me_id = me_id

    def copy(self):
        new_snakes = {}
        for sid, s in self.snakes.items():
            new_snakes[sid] = {
                "health": s["health"],
                "body": list(s["body"]),
            }
        return Board(self.w, self.h, set(self.food), new_snakes, self.me_id)

    def me(self):
        return self.snakes.get(self.me_id)

    def enemies(self):
        return [s for sid, s in self.snakes.items() if sid != self.me_id]


def in_bounds(p, board):
    return 0 <= p[0] < board.w and 0 <= p[1] < board.h


def head_of(snake):
    return snake["body"][0]


def tail_of(snake):
    return snake["body"][-1]


def length_of(snake):
    return len(snake["body"])


def add(p, d):
    return (p[0] + d[0], p[1] + d[1])


# ---------------------------------------------------------------------------
# Occupancy / vacate model (mirrors Map::turnsUntilVacant)
# ---------------------------------------------------------------------------
def build_vacate(board):
    """Map cell -> turns until vacant. Body part i vacates in (len-i-1) turns;
    tail => 0 (enterable now). Matches updateVacateTurnsForSnake."""
    vac = {}
    for s in board.snakes.values():
        body = s["body"]
        n = len(body)
        for i, p in enumerate(body):
            turns = n - i - 1
            if turns > vac.get(p, -1):
                vac[p] = turns
    return vac


def turns_until_vacant(vac, board, p):
    if not in_bounds(p, board):
        return 0
    return vac.get(p, 0)


def is_180_for(board, snake, p):
    if snake is None or len(snake["body"]) <= 1:
        return False
    return snake["body"][1] == p


def is_cell_ok_for(board, vac, snake, p):
    return (in_bounds(p, board)
            and turns_until_vacant(vac, board, p) == 0
            and not is_180_for(board, snake, p))


# ---------------------------------------------------------------------------
# Flood fill (countAccessibleCells) respecting vacate turns.
# Matches original: counts a cell when turn >= turnsUntilVacant.
# ---------------------------------------------------------------------------
def count_accessible(board, vac, start):
    from collections import deque
    q = deque()
    q.append((start, 0))
    visited = set()
    count = 0
    while q:
        p, turn = q.popleft()
        if p in visited:
            continue
        if not in_bounds(p, board):
            continue
        visited.add(p)
        if turn < turns_until_vacant(vac, board, p):
            continue
        count += 1
        # push order mirrors original (l, r, down(+y? no) ...) -- order is
        # irrelevant for a count.
        for d in DIRS.values():
            q.append((add(p, d), turn + 1))
    return count


# ---------------------------------------------------------------------------
# BFS shortest path respecting vacate grid (stands in for A* shortestPath).
# `snake` is whose head we start from (for the 180 rule). Returns
# (size, first_direction) or (0, None).
# ---------------------------------------------------------------------------
def shortest_path(board, vac, snake, start, goal):
    from collections import deque
    if start == goal:
        return (0, None)
    q = deque()
    q.append(start)
    came_from = {start: None}
    turn_of = {start: 0}
    found = False
    while q:
        cur = q.popleft()
        if cur == goal:
            found = True
            break
        t = turn_of[cur] + 1
        for d in DIRS.values():
            nxt = add(cur, d)
            if nxt in came_from:
                continue
            if not in_bounds(nxt, board):
                continue
            # 180 rule only applies leaving the true head.
            if cur == start and is_180_for(board, snake, nxt):
                continue
            # allow reaching the goal even if it's technically a tail cell
            if nxt != goal and t < turns_until_vacant(vac, board, nxt):
                continue
            came_from[nxt] = cur
            turn_of[nxt] = t
            q.append(nxt)
    if not found:
        return (0, None)
    path = []
    node = goal
    while came_from[node] is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    size = len(path)
    first = path[0]
    dx = first[0] - start[0]
    dy = first[1] - start[1]
    for name, d in DIRS.items():
        if d == (dx, dy):
            return (size, name)
    return (0, None)


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------------------
# Policies (ported from movement.cpp / dog.cpp / cautious.cpp / hungry.cpp)
# ---------------------------------------------------------------------------
def not_immediately_suicidal_moves_for(board, vac, snake):
    """DirectionSet order in original: left, right, up, down."""
    h = head_of(snake)
    moves = []
    for name in ["left", "right", "up", "down"]:
        if is_cell_ok_for(board, vac, snake, add(h, DIRS[name])):
            moves.append(name)
    return moves


def not_immediately_suicidal_for(board, vac, snake):
    moves = not_immediately_suicidal_moves_for(board, vac, snake)
    return moves[0] if moves else None


def chase_tail_for(board, vac, snake):
    return shortest_path(board, vac, snake, head_of(snake), tail_of(snake))[1]


def closest_food_for(board, vac, snake):
    """closestFood: nearest reachable food, ignoring enemy contention."""
    head = head_of(snake)
    best_size = None
    best_dir = None
    for food in board.food:
        size, d = shortest_path(board, vac, snake, head, food)
        if d is None:
            continue
        if best_size is not None and size >= best_size:
            continue
        best_size = size
        best_dir = d
    return best_dir


def best_food_for(board, vac, snake):
    """movement.cpp::bestFood: closest reachable food that an equal/bigger
    enemy won't reach first."""
    my_head = head_of(snake)
    my_len = length_of(snake)
    enemies = [s for sid, s in board.snakes.items()
               if s is not snake]
    foods = sorted(board.food, key=lambda f: manhattan(my_head, f))
    best_size = None
    best_dir = None
    for food in foods:
        if best_size is not None and manhattan(my_head, food) >= best_size:
            break
        size, d = shortest_path(board, vac, snake, my_head, food)
        if d is None:
            continue
        if best_size is not None and size >= best_size:
            continue
        enemy_will_win = False
        sorted_enemies = sorted(enemies,
                                key=lambda e: manhattan(head_of(e), food))
        for e in sorted_enemies:
            if manhattan(food, head_of(e)) > size:
                break
            esize, ed = shortest_path(board, vac, e, head_of(e), food)
            if ed is None:
                continue
            if esize == size:
                enemy_will_win = my_len < length_of(e)
            else:
                enemy_will_win = esize < size
            if enemy_will_win:
                break
        if not enemy_will_win:
            best_size = size
            best_dir = d
    return best_dir


def dog_move(board, vac, snake):
    """Dog: chaseTail -> notImmediatelySuicidal (no food)."""
    d = chase_tail_for(board, vac, snake)
    if d is not None:
        return d
    return not_immediately_suicidal_for(board, vac, snake)


def cautious_move(board, vac, snake):
    """Cautious: bestFood -> chaseTail -> notImmediatelySuicidal."""
    d = best_food_for(board, vac, snake)
    if d is not None:
        return d
    d = chase_tail_for(board, vac, snake)
    if d is not None:
        return d
    return not_immediately_suicidal_for(board, vac, snake)


def hungry_move(board, vac, snake):
    """Hungry: closestFood -> notImmediatelySuicidal."""
    d = closest_food_for(board, vac, snake)
    if d is not None:
        return d
    return not_immediately_suicidal_for(board, vac, snake)


def one_direction_move(board, vac, snake, fixed):
    """OneDirection: go `fixed` if legal, else fall back to Cautious."""
    if is_cell_ok_for(board, vac, snake, add(head_of(snake), DIRS[fixed])):
        return fixed
    return cautious_move(board, vac, snake)


# ---------------------------------------------------------------------------
# Enemy policy set (mirrors Sim's enemyAlgorithms). Each entry produces a move
# for a given enemy id; we take the maximin (worst for me) across the whole set.
# ---------------------------------------------------------------------------
def enemy_move(policy, board, vac, enemy_id):
    ep = Board(board.w, board.h, board.food, board.snakes, enemy_id)
    e = ep.me()
    if e is None:
        return None
    if policy == "hungry":
        return hungry_move(ep, vac, e)
    if policy in ("left", "right", "up", "down"):
        return one_direction_move(ep, vac, e, policy)
    return hungry_move(ep, vac, e)


ENEMY_POLICIES = ["hungry", "left", "right", "up", "down"]


# ---------------------------------------------------------------------------
# Simulation step (applyMoves): move heads, eat or shrink, resolve collisions.
# Mirrors moveHeadsForward / eatFoodOrDie / markCrashersDead / removeDeadGuys.
# ---------------------------------------------------------------------------
def apply_moves(board, moves):
    """moves: dict snake_id -> direction name. Returns (new Board, dead set)."""
    nb = board.copy()

    # 1. Move heads forward.
    for sid, s in nb.snakes.items():
        d = moves.get(sid)
        if d is None:
            new_head = (-999, -999)   # no legal move -> walks into a wall
        else:
            new_head = add(head_of(s), DIRS[d])
        s["body"].insert(0, new_head)

    # 2. Eat food or shrink. Health decrements; eating resets to 100. Original
    #    grows on the following turn (tail duplicated) but for scoring we treat
    #    an eater as not popping its tail this turn.
    grew = set()
    for sid, s in nb.snakes.items():
        head = head_of(s)
        s["health"] -= 1
        if head in nb.food:
            s["health"] = 100
            grew.add(sid)
        else:
            s["body"].pop()
    for sid in grew:
        nb.food.discard(head_of(nb.snakes[sid]))

    dead = set()

    # 3. Head-to-head (markCrashersDead: equal -> both die; shorter dies).
    heads = {}
    for sid, s in nb.snakes.items():
        h = head_of(s)
        heads.setdefault(h, []).append(sid)
    for h, ids in heads.items():
        if len(ids) < 2:
            continue
        longest = max(length_of(nb.snakes[i]) for i in ids)
        winners = [i for i in ids
                   if length_of(nb.snakes[i]) == longest]
        # everyone who isn't strictly-longest dies; if tie for longest all die
        if len(winners) > 1:
            for i in ids:
                dead.add(i)
        else:
            for i in ids:
                if i != winners[0]:
                    dead.add(i)

    # 4. Out of bounds / starvation.
    for sid, s in nb.snakes.items():
        h = head_of(s)
        if not in_bounds(h, nb) or s["health"] <= 0:
            dead.add(sid)

    # 5. Body collisions: head enters any snake's parts[1:] (tail cells).
    body_cells = {}
    for sid, s in nb.snakes.items():
        body = s["body"]
        for i in range(1, len(body)):
            body_cells[body[i]] = True
    for sid, s in nb.snakes.items():
        if sid in dead:
            continue
        if head_of(s) in body_cells:
            dead.add(sid)

    for sid in dead:
        del nb.snakes[sid]

    return nb, dead


# ---------------------------------------------------------------------------
# Scoring (simulator.cpp::scoreFuture / getFoodScore)
# ---------------------------------------------------------------------------
def get_food_score(food_turn, health):
    health_at_food_time = health - food_turn
    diff = health_at_food_time - IDEAL_HEALTH_AT_FOOD_TIME
    multiplier = 200 if diff >= 0 else 100
    inverse_diff = IDEAL_HEALTH_AT_FOOD_TIME - abs(diff)
    return inverse_diff * multiplier


# ---------------------------------------------------------------------------
# couldEndUpCornerAdjacentToBiggerSnake -- ported cell-for-cell from
# snakelib.cpp with y offsets NEGATED for the v1 (y-up) API. In the original
# (y-down): Up moves to smaller y. In v1 "up" moves to larger y, so each
# original branch keeps its x offsets and negates every y offset; direction
# names are unchanged (only the axis flipped).
# ---------------------------------------------------------------------------
def _space_is_open(board, vac, p):
    return in_bounds(p, board) and turns_until_vacant(vac, board, p) == 0


def _any_big_snake_at(board, my_len, a, b):
    for e in board.enemies():
        if length_of(e) >= my_len:          # isTooBigForMeToEat: myLen <= theirLen
            h = head_of(e)
            if h == a or h == b:
                return True
    return False


def _corner_check(board, vac, my_len, danger_pts, dest_pts):
    open0 = _space_is_open(board, vac, dest_pts[0])
    open1 = _space_is_open(board, vac, dest_pts[1])
    if open0 and _any_big_snake_at(board, my_len, danger_pts[0], danger_pts[1]):
        return True
    if open1 and _any_big_snake_at(board, my_len, danger_pts[2], danger_pts[3]):
        return True
    return False


def could_end_up_corner_adjacent(board, vac, move_name):
    me = board.me()
    if me is None:
        return False
    x, y = head_of(me)
    my_len = length_of(me)

    if move_name == "up":     # original Up, y offsets negated (-> +y)
        p2 = (x - 2, y + 2)
        p3 = (x - 1, y + 3)
        p4 = (x + 1, y + 3)
        p5 = (x + 2, y + 2)
        pt = (x - 1, y + 2)
        pu = (x + 1, y + 2)
        return _corner_check(board, vac, my_len, [p2, p3, p4, p5], [pt, pu])
    elif move_name == "right":
        p5 = (x + 2, y + 2)
        p6 = (x + 3, y + 1)
        p7 = (x + 3, y - 1)
        p8 = (x + 2, y - 2)
        pv = (x + 2, y + 1)
        pw = (x + 2, y - 1)
        return _corner_check(board, vac, my_len, [p5, p6, p7, p8], [pv, pw])
    elif move_name == "down":
        p8 = (x + 2, y - 2)
        p9 = (x + 1, y - 3)
        pa = (x - 1, y - 3)
        pb = (x - 2, y - 2)
        px = (x + 1, y - 2)
        py = (x - 1, y - 2)
        return _corner_check(board, vac, my_len, [p8, p9, pa, pb], [px, py])
    else:                     # left
        pb = (x - 2, y - 2)
        pc = (x - 3, y - 1)
        p1 = (x - 3, y + 1)
        p2 = (x - 2, y + 2)
        pz = (x - 2, y - 2)
        ps = (x - 1, y - 2)
        return _corner_check(board, vac, my_len, [pb, pc, p1, p2], [pz, ps])


def score_future(future, root_board):
    """future keys: move, obituaries(id->turn), foods_eaten(id->[turns]),
    accessible (int), root_vac, preferred."""
    me = root_board.me()
    my_id = root_board.me_id
    my_health = me["health"]
    my_len = length_of(me)

    survival_score = 1_000_000_000
    murder_score = 0
    food_score = 0
    dies = False

    preferred = future["preferred"]
    is_preferred = preferred is not None and preferred == future["move"]
    bonus = 500 if is_preferred else 0

    next_food = 1000
    food_turns = future["foods_eaten"].get(my_id)
    if food_turns:
        next_food = food_turns[0]
        food_score = get_food_score(food_turns[0], my_health)

    if next_food > my_health:
        survival_score = min(survival_score, my_health * 100)
        dies = True

    for sid, turn in future["obituaries"].items():
        if sid == my_id:
            survival_score = min(survival_score, turn * 100)
            dies = True
        else:
            murder_score += (100 - min(100, turn)) * 10000

    if not dies:
        accessible = future["accessible"]
        if accessible < my_len:
            survival_score = min(survival_score, accessible * 100)
            dies = True

    if could_end_up_corner_adjacent(root_board, future["root_vac"],
                                    future["move"]):
        survival_score = min(survival_score, 1000)
        dies = True

    if dies:
        return survival_score + bonus
    return survival_score + food_score + murder_score + bonus


# ---------------------------------------------------------------------------
# Roll one future forward for a given (first move, enemy policy) branch.
# ---------------------------------------------------------------------------
def simulate_future(root_board, first_move, enemy_policy, deadline):
    my_id = root_board.me_id
    obituaries = {}
    foods_eaten = {}

    board = root_board
    turn = 0
    while turn < SEARCH_MAX_TURNS:
        if time.monotonic() > deadline:
            break
        turn += 1
        vac = build_vacate(board)

        moves = {}
        me = board.me()
        if turn == 1:
            moves[my_id] = first_move
        elif me is not None:
            md = cautious_move(board, vac, me)
            moves[my_id] = md if md is not None else "up"

        for sid, s in board.snakes.items():
            if sid == my_id:
                continue
            ed = enemy_move(enemy_policy, board, vac, sid)
            moves[sid] = ed if ed is not None else "up"

        old_food = set(board.food)
        board, dead = apply_moves(board, moves)

        for sid in dead:
            obituaries.setdefault(sid, turn)
        for sid, s in board.snakes.items():
            if head_of(s) in old_food:
                foods_eaten.setdefault(sid, []).append(turn)

        if my_id not in board.snakes:
            break

    return {
        "move": first_move,
        "obituaries": obituaries,
        "foods_eaten": foods_eaten,
    }


# ---------------------------------------------------------------------------
# Top-level decision (Sim::move + bestMove maximin).
# ---------------------------------------------------------------------------
def choose_move(board):
    deadline = time.monotonic() + TIME_BUDGET
    root_vac = build_vacate(board)
    me = board.me()

    candidates = not_immediately_suicidal_moves_for(board, root_vac, me)
    if not candidates:
        return fallback_move(board, root_vac)

    # preferred = dog.move(state) = chaseTail (NOT bestFood).
    preferred = dog_move(board, root_vac, me)

    accessible = {}
    for mv in candidates:
        nh = add(head_of(me), DIRS[mv])
        accessible[mv] = count_accessible(board, root_vac, nh)

    # Maximin: worst score per first move across all enemy policies.
    worst_scores = {}
    best_scores = {}

    for mv in candidates:
        for pol in ENEMY_POLICIES:
            if time.monotonic() > deadline:
                break
            fut = simulate_future(board, mv, pol, deadline)
            fut["accessible"] = accessible[mv]
            fut["root_vac"] = root_vac
            fut["preferred"] = preferred
            sc = score_future(fut, board)
            if mv not in worst_scores or sc < worst_scores[mv]:
                worst_scores[mv] = sc
            if mv not in best_scores or sc > best_scores[mv]:
                best_scores[mv] = sc
        if time.monotonic() > deadline:
            break

    if not worst_scores:
        return preferred or candidates[0]

    best_of_worst_mv = max(worst_scores, key=lambda m: worst_scores[m])
    best_of_best_mv = max(best_scores, key=lambda m: best_scores[m])

    if worst_scores[best_of_worst_mv] < 1500:
        return best_of_best_mv
    return best_of_worst_mv


def fallback_move(board, vac):
    me = board.me()
    h = head_of(me)
    for name in ["left", "right", "up", "down"]:
        p = add(h, DIRS[name])
        if (in_bounds(p, board)
                and turns_until_vacant(vac, board, p) == 0
                and not is_180_for(board, me, p)):
            return name
    for name in ["left", "right", "up", "down"]:
        p = add(h, DIRS[name])
        if in_bounds(p, board) and turns_until_vacant(vac, board, p) == 0:
            return name
    for name in ["left", "right", "up", "down"]:
        p = add(h, DIRS[name])
        if in_bounds(p, board):
            return name
    return "up"


# ---------------------------------------------------------------------------
# v1 API glue
# ---------------------------------------------------------------------------
def _board_from_state(game_state):
    b = game_state["board"]
    food = set((f["x"], f["y"]) for f in b.get("food", []))
    snakes = {}
    for s in b["snakes"]:
        body = [(p["x"], p["y"]) for p in s["body"]]
        snakes[s["id"]] = {"health": s.get("health", 100), "body": body}
    me_id = game_state["you"]["id"]
    if me_id not in snakes:
        s = game_state["you"]
        body = [(p["x"], p["y"]) for p in s["body"]]
        snakes[me_id] = {"health": s.get("health", 100), "body": body}
    return Board(b["width"], b["height"], food, snakes, me_id)


def info():
    # Original Sim::meta() color == "#698866". 2018 API exposed head/tail
    # "types" (Sim used "shades"/"pixel") that have no v1 equivalent, so
    # head/tail default here.
    return {
        "apiversion": "1",
        "author": "graeme-hill",
        "color": "#698866",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        board = _board_from_state(game_state)
        mv = choose_move(board)
        if mv not in DIRS:
            mv = "up"
        return {"move": mv}
    except Exception:
        try:
            board = _board_from_state(game_state)
            vac = build_vacate(board)
            return {"move": fallback_move(board, vac)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
