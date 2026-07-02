"""CodeClash port of graeme-hill/snakebot ("Team Graeme & Chris").

Winner of Battlesnake Victoria 2018 Expert Division.

FIDELITY: approximate.

The original (C++) bot's flagship algorithm is `Sim`: it enumerates a set of
paired policies (my policy vs. enemy policy) plus first-move prefixes, rolls
each pair forward as a lightweight game simulation, then scores every resulting
"future" and picks the move that maximizes the worst-case outcome (a maximin),
falling back to best-case if every worst-case is dire (bestMove: threshold
1500). Scoring (scoreFuture) rewards survival, flood-fill accessible space >=
my length, well-timed food (IDEAL_HEALTH_AT_FOOD_TIME=100), murders, and
avoiding corner-adjacency to bigger/equal snakes.

This port reproduces that core faithfully in spirit within one fast pure-stdlib
file: for each safe first move it simulates several turns forward where my
snake follows the original's dog/cautious policy stack (bestFood -> chaseTail
-> notImmediatelySuicidal) and each enemy follows a greedy hungry policy, then
scores the future with the same scoreFuture heuristic and picks via the same
maximin/threshold logic. Search is depth- and wall-clock-bounded to stay well
under 1s on 11x11.

Coordinates use the CURRENT Battlesnake v1 API convention: (0,0) bottom-left,
up=y+1, down=y-1, left=x-1, right=x+1. head=body[0].
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
        # snakes: dict id -> dict(health, body=list[(x,y)], eaten_this_turn)
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
    """Map cell -> turns until vacant. A body part at index i vacates in
    (len - i - 1) turns; tail => 0 (enterable now). Matches
    updateVacateTurnsForSnake."""
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


def is_180(board, p):
    me = board.me()
    if me is None or length_of(me) <= 1:
        return False
    return me["body"][1] == p


def is_cell_ok(board, vac, p):
    return (in_bounds(p, board)
            and turns_until_vacant(vac, board, p) == 0
            and not is_180(board, p))


def is_close_to_equal_or_bigger_head(board, p, my_len):
    """isCloseToEqualOrBiggerSnakeHead: p adjacent to a head of a snake at
    least as long as me."""
    for e in board.enemies():
        if length_of(e) >= my_len:
            eh = head_of(e)
            if abs(eh[0] - p[0]) + abs(eh[1] - p[1]) == 1:
                return True
    return False


# ---------------------------------------------------------------------------
# Flood fill (countAccessibleCells) respecting vacate turns
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
        for d in DIRS.values():
            q.append((add(p, d), turn + 1))
    return count


# ---------------------------------------------------------------------------
# BFS shortest path respecting vacate grid (stands in for A* shortestPath).
# Returns (size, first_direction) or (0, None).
# ---------------------------------------------------------------------------
def shortest_path(board, vac, start, goal):
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
            # allow reaching the goal even if it's technically a tail cell
            if nxt != goal and t < turns_until_vacant(vac, board, nxt):
                continue
            came_from[nxt] = cur
            turn_of[nxt] = t
            q.append(nxt)
    if not found:
        return (0, None)
    # reconstruct
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
# Policies (ported from movement.cpp / dog.cpp / cautious.cpp)
# ---------------------------------------------------------------------------
def not_immediately_suicidal_moves(board, vac):
    me = board.me()
    h = head_of(me)
    moves = []
    for name in ["left", "right", "up", "down"]:
        if is_cell_ok(board, vac, add(h, DIRS[name])):
            moves.append(name)
    return moves


def not_immediately_suicidal(board, vac):
    moves = not_immediately_suicidal_moves(board, vac)
    return moves[0] if moves else None


def chase_tail(board, vac):
    me = board.me()
    size, d = shortest_path(board, vac, head_of(me), tail_of(me))
    return d


def best_food(board, vac):
    """Ported from movement.cpp::bestFood: go to closest reachable food that
    an equal/bigger enemy won't reach first."""
    me = board.me()
    my_head = head_of(me)
    my_len = length_of(me)
    foods = sorted(board.food, key=lambda f: manhattan(my_head, f))
    best_size = None
    best_dir = None
    for food in foods:
        if best_size is not None and manhattan(my_head, food) >= best_size:
            break
        size, d = shortest_path(board, vac, my_head, food)
        if d is None:
            continue
        if best_size is not None and size >= best_size:
            continue
        enemy_will_win = False
        sorted_enemies = sorted(board.enemies(),
                                key=lambda e: manhattan(head_of(e), food))
        for e in sorted_enemies:
            if manhattan(food, head_of(e)) > size:
                break
            esize, ed = shortest_path(board, vac, head_of(e), food)
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


def my_policy_move(board, vac):
    """Dog/Cautious stack: bestFood -> chaseTail -> notImmediatelySuicidal."""
    d = best_food(board, vac)
    if d is not None:
        return d
    d = chase_tail(board, vac)
    if d is not None:
        return d
    return not_immediately_suicidal(board, vac)


def enemy_policy_move(board, vac, enemy_id):
    """Greedy hungry-ish enemy: head toward nearest food, else survive."""
    # Build an enemy-perspective board (same board, different "me").
    ep = Board(board.w, board.h, board.food, board.snakes, enemy_id)
    e = ep.me()
    if e is None:
        return None
    eh = head_of(e)
    if ep.food:
        target = min(ep.food, key=lambda f: manhattan(eh, f))
        size, d = shortest_path(ep, vac, eh, target)
        if d is not None:
            return d
    # else chase own tail / survive
    size, d = shortest_path(ep, vac, eh, tail_of(e))
    if d is not None:
        return d
    return not_immediately_suicidal(ep, vac)


# ---------------------------------------------------------------------------
# Simulation step (applyMoves): move heads, eat or shrink, resolve collisions
# ---------------------------------------------------------------------------
def apply_moves(board, moves):
    """moves: dict snake_id -> direction name. Returns new Board and set of
    ids that died this turn."""
    nb = board.copy()
    grew = set()
    # 1. Move heads forward.
    for sid, s in nb.snakes.items():
        d = moves.get(sid)
        if d is None:
            # no legal move given: keep still-ish -> treat as death by wall
            new_head = (-999, -999)
        else:
            new_head = add(head_of(s), DIRS[d])
        s["body"].insert(0, new_head)

    # 2. Eat food or die (health), remove tail if didn't eat.
    for sid, s in nb.snakes.items():
        head = head_of(s)
        s["health"] -= 1
        if head in nb.food:
            s["health"] = 100
            grew.add(sid)
        else:
            s["body"].pop()  # remove tail
    # remove eaten food
    for sid in grew:
        h = head_of(nb.snakes[sid])
        nb.food.discard(h)

    dead = set()
    # 3. Out of bounds or starvation.
    for sid, s in nb.snakes.items():
        h = head_of(s)
        if not in_bounds(h, nb) or s["health"] <= 0:
            dead.add(sid)

    # 4. Body / head-to-head collisions.
    for sid, s in nb.snakes.items():
        if sid in dead:
            continue
        h = head_of(s)
        for osid, o in nb.snakes.items():
            if osid in dead and osid != sid:
                pass
            # body collision (skip own head at index 0)
            body = o["body"]
            start = 1 if osid == sid else 1  # never collide with any head here
            for i in range(1, len(body)):
                if body[i] == h:
                    dead.add(sid)
                    break
            if sid in dead:
                break
        # head-to-head
        if sid not in dead:
            for osid, o in nb.snakes.items():
                if osid == sid:
                    continue
                if head_of(o) == h:
                    if length_of(o) >= length_of(s):
                        dead.add(sid)
                        break

    for sid in dead:
        del nb.snakes[sid]

    return nb, dead


# ---------------------------------------------------------------------------
# Scoring (ported from simulator.cpp::scoreFuture / getFoodScore)
# ---------------------------------------------------------------------------
def get_food_score(food_turn, health):
    health_at_food_time = health - food_turn
    diff = health_at_food_time - IDEAL_HEALTH_AT_FOOD_TIME
    multiplier = 200 if diff >= 0 else 100
    inverse_diff = IDEAL_HEALTH_AT_FOOD_TIME - abs(diff)
    return inverse_diff * multiplier


def could_end_up_corner_adjacent(board, vac, move_name):
    """Ported from couldEndUpCornerAdjacentToBiggerSnake (adapted to v1
    coords). If we move `move_name`, is there an open cell diagonally adjacent
    that a bigger/equal enemy head could also reach, risking a corner trade?"""
    me = board.me()
    if me is None:
        return False
    hx, hy = head_of(me)
    my_len = length_of(me)
    # destination after the move
    dx, dy = DIRS[move_name]
    nx, ny = hx + dx, hy + dy

    # The two cells flanking the destination (perpendicular to move dir).
    if dx != 0:  # horizontal move -> flanks are vertical
        dest_flanks = [(nx, ny + 1), (nx, ny - 1)]
    else:        # vertical move -> flanks are horizontal
        dest_flanks = [(nx + 1, ny), (nx - 1, ny)]

    for fx, fy in dest_flanks:
        if not in_bounds((fx, fy), board):
            continue
        if turns_until_vacant(vac, board, (fx, fy)) != 0:
            continue
        # if a bigger/equal enemy head is adjacent to this flank cell, danger
        for e in board.enemies():
            if length_of(e) < my_len:
                continue
            eh = head_of(e)
            if abs(eh[0] - fx) + abs(eh[1] - fy) == 1:
                return True
    return False


def score_future(future, root_board, preferred_dir):
    """future: dict with keys move, obituaries(id->turn), foods_eaten(id->[turns]),
    end_board (last board), accessible (int for the first move)."""
    me = root_board.me()
    my_id = root_board.me_id
    my_health = me["health"]
    my_len = length_of(me)

    survival_score = 1_000_000_000
    murder_score = 0
    food_score = 0
    dies = False

    is_preferred = preferred_dir is not None and preferred_dir == future["move"]
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

    if could_end_up_corner_adjacent(root_board, future["root_vac"], future["move"]):
        survival_score = min(survival_score, 1000)
        dies = True

    if dies:
        return survival_score + bonus
    return survival_score + food_score + murder_score + bonus


# ---------------------------------------------------------------------------
# Roll one future forward for a given first move.
# ---------------------------------------------------------------------------
def simulate_future(root_board, first_move, deadline):
    my_id = root_board.me_id
    obituaries = {}
    foods_eaten = {}

    board = root_board
    turn = 0
    move_for_turn = first_move
    while turn < SEARCH_MAX_TURNS:
        if time.monotonic() > deadline:
            break
        turn += 1
        vac = build_vacate(board)

        moves = {}
        # my move
        if turn == 1:
            moves[my_id] = move_for_turn
        else:
            md = my_policy_move(board, vac)
            if md is None:
                md = "up"
            moves[my_id] = md
        # enemy moves
        for e in board.enemies():
            eid = None
            for sid, s in board.snakes.items():
                if s is e:
                    eid = sid
                    break
            ed = enemy_policy_move(board, vac, eid)
            if ed is None:
                ed = "up"
            moves[eid] = ed

        # record food-before state
        old_food = set(board.food)
        old_ids = set(board.snakes.keys())

        board, dead = apply_moves(board, moves)

        # obituaries
        for sid in dead:
            if sid not in obituaries:
                obituaries[sid] = turn
        # foods eaten: a snake sits on a former food cell now
        for sid, s in board.snakes.items():
            if head_of(s) in old_food:
                foods_eaten.setdefault(sid, []).append(turn)

        if my_id not in board.snakes:
            break

    return {
        "move": first_move,
        "obituaries": obituaries,
        "foods_eaten": foods_eaten,
        "end_board": board,
    }


# ---------------------------------------------------------------------------
# Top-level decision (Sim::move + bestMove maximin)
# ---------------------------------------------------------------------------
def choose_move(board):
    deadline = time.monotonic() + TIME_BUDGET
    root_vac = build_vacate(board)
    me = board.me()
    my_len = length_of(me)

    # candidate first moves = not immediately suicidal
    candidates = not_immediately_suicidal_moves(board, root_vac)
    if not candidates:
        # nothing safe: any in-bounds move (avoid known bodies best-effort)
        return fallback_move(board, root_vac)

    # preferred move = the dog/cautious policy pick (Sim uses dog.move as pref)
    preferred = my_policy_move(board, root_vac)

    # For maximin robustness we sample multiple enemy behaviors by scoring the
    # single rolled future per candidate (enemies play greedily). This mirrors
    # scoreFuture over the set of futures per (algorithm, firstMove) key.
    worst_scores = {}   # move -> min score
    best_scores = {}    # move -> max score

    # accessible space for the immediate move (used by scoreFuture when alive)
    accessible = {}
    for mv in candidates:
        nh = add(head_of(me), DIRS[mv])
        accessible[mv] = count_accessible(board, root_vac, nh)

    for mv in candidates:
        if time.monotonic() > deadline:
            break
        fut = simulate_future(board, mv, deadline)
        fut["accessible"] = accessible[mv]
        fut["root_vac"] = root_vac
        sc = score_future(fut, board, preferred)
        worst_scores[mv] = min(worst_scores.get(mv, sc), sc)
        best_scores[mv] = max(best_scores.get(mv, sc), sc)

    if not worst_scores:
        return preferred or candidates[0]

    # bestOfTheWorst / bestOfTheBest with threshold 1500 (from bestMove).
    best_of_worst_mv = max(worst_scores, key=lambda m: worst_scores[m])
    best_of_best_mv = max(best_scores, key=lambda m: best_scores[m])

    if worst_scores[best_of_worst_mv] < 1500:
        return best_of_best_mv
    return best_of_worst_mv


def fallback_move(board, vac):
    me = board.me()
    h = head_of(me)
    # prefer cells that are in bounds and not a snake body (tails ok)
    for name in DIR_LIST:
        p = add(h, DIRS[name])
        if in_bounds(p, board) and turns_until_vacant(vac, board, p) == 0 and not is_180(board, p):
            return name
    for name in DIR_LIST:
        p = add(h, DIRS[name])
        if in_bounds(p, board) and turns_until_vacant(vac, board, p) == 0:
            return name
    for name in DIR_LIST:
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
    return {
        "apiversion": "1",
        "author": "graeme-hill",
        "color": "#880000",
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
        # never crash: return any in-bounds, non-body move
        try:
            board = _board_from_state(game_state)
            vac = build_vacate(board)
            return {"move": fallback_move(board, vac)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
