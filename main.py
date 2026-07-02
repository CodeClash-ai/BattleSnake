"""
snek-two -- port of aleksiy325's C++ Battlesnake (Battlesnake Victoria 2018
Intermediate/Advanced Division winner) to the CodeClash / Battlesnake v1 API.

Original: https://github.com/aleksiy325/snek-two  (C++, author "asdf123" / aleksiy325)

Strategy (faithful reimplementation of src/strategies/minimax_snake.cpp +
src/common/game_state.cpp):

  * Minimax with alpha-beta pruning. The maximizing player is us; the
    minimizing player is a single opponent chosen by BFS from our head
    (getOpponent). Search depth = 4 with a wall-clock cutoff (~150ms in the
    original; kept configurable here and time-guarded).
  * State evaluation (scoreState):
        - dead                -> -inf
        - only one alive      -> +inf
        - voronoi free squares * free_weight (0 owned -> -inf)
        - + 100000 / numAlive
        - food term: rope = health - food_length, using the voronoi-owned
          nearest-food depth when we control food, else BFS distance to the
          nearest reachable food; health < food_length -> -inf; otherwise
          add food_weight * atan(rope / food_exp)
        - + free_squares * free_weight   (added twice, matching the C++)
        - + (1 / size) * length_weight
  * Head-on collision penalty: if a candidate head is adjacent to a living
    opponent head of size >= ours, apply a huge negative adjustment.
  * Tail-follow penalty when stepping onto a snake's tail that may have just
    eaten (doubled tail cell).
  * isSafe(p, distance): a cell is safe if in-bounds/not a wall and any snake
    body occupying it will have vacated within `distance` turns (turns the
    tail segment remains occupied). This makes tails enterable, matching the
    original getTurnsOccupied logic.

Weights are the competition-tuned constants from the C++ MinimaxSnake:
    food_weight = 68.60914, food_exp = 8.51774,
    length_weight = 0.82267, free_weight = 7.60983

FIDELITY: faithful (core minimax + voronoi + arctan-food heuristic reproduced;
adapted to y-up v1 coordinates and current v1 API shapes).
"""

import math
import time
from collections import deque

# ---- tuned weights (from MinimaxSnake) ----------------------------------
FOOD_WEIGHT = 68.60914
FOOD_EXP = 8.51774
LENGTH_WEIGHT = 0.82267
FREE_WEIGHT = 7.60983

MAX_DEPTH = 4
MAX_TIME_MS = 150
MAX_HEALTH = 100
FREE_MOVES = 2  # first two moves the snake grows without dropping its tail

NEG_INF = float("-inf")
POS_INF = float("inf")
# large finite negatives used as "practically dead" adjustments (mirrors the
# C++ use of numeric_limits::lowest()/N so pruning still orders sensibly)
BIG = 1e300

# v1 API: (0,0) bottom-left, up=y+1, down=y-1, left=x-1, right=x+1
MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
MOVE_NAMES = ("up", "down", "left", "right")


# ------------------------------------------------------------------------- #
# Internal game state
# ------------------------------------------------------------------------- #
class SnakeState:
    __slots__ = ("id", "health", "body", "alive", "free_moves")

    def __init__(self, sid, health, body, free_moves):
        self.id = sid
        self.health = health
        self.body = list(body)  # list of (x, y); body[0] = head
        self.alive = True
        self.free_moves = free_moves

    def clone(self):
        s = SnakeState.__new__(SnakeState)
        s.id = self.id
        s.health = self.health
        s.body = list(self.body)
        s.alive = self.alive
        s.free_moves = self.free_moves
        return s

    @property
    def head(self):
        return self.body[0]

    @property
    def size(self):
        return len(self.body)


class State:
    __slots__ = ("w", "h", "food", "snakes")

    def __init__(self, w, h, food, snakes):
        self.w = w
        self.h = h
        self.food = set(food)
        self.snakes = snakes  # list[SnakeState]

    def clone(self):
        s = State.__new__(State)
        s.w = self.w
        s.h = self.h
        s.food = set(self.food)
        s.snakes = [sn.clone() for sn in self.snakes]
        return s

    def in_bounds(self, p):
        return 0 <= p[0] < self.w and 0 <= p[1] < self.h

    def num_alive(self):
        return sum(1 for s in self.snakes if s.alive)

    def occupancy(self):
        """Map cell -> (snake_index, turns_occupied). turns_occupied is how
        many turns until this segment vacates (size - body_index), matching
        C++ getTurnsOccupied."""
        occ = {}
        for i, s in enumerate(self.snakes):
            if not s.alive:
                continue
            n = len(s.body)
            for idx, p in enumerate(s.body):
                turns = n - idx
                # keep the max turns if a cell is listed twice (stacked tail)
                prev = occ.get(p)
                if prev is None or turns > prev[1]:
                    occ[p] = (i, turns)
        return occ


# ------------------------------------------------------------------------- #
# Board queries (operate on a precomputed occupancy snapshot)
# ------------------------------------------------------------------------- #
def expand(state, p):
    x, y = p
    out = []
    for dx, dy in MOVES.values():
        n = (x + dx, y + dy)
        if state.in_bounds(n):
            out.append(n)
    return out


def is_safe(state, occ, p, distance):
    """In-bounds, and any snake body there will be gone within `distance`
    turns (tail enterable)."""
    if not state.in_bounds(p):
        return False
    o = occ.get(p)
    if o is None:
        return True
    return o[1] <= distance


def bfs_food_dist(state, occ, start):
    """BFS distance (steps) to the nearest reachable food; -1 if none.
    Distance-aware safety, matching GameState::bfsFood."""
    if not state.food:
        return -1
    visited = {start}
    q = deque()
    q.append(start)
    depth = 0
    MARK = None
    q.append(MARK)
    while q:
        cur = q.popleft()
        if cur is MARK:
            depth += 1
            q.append(MARK)
            if q[0] is MARK:
                break
            continue
        for nb in expand(state, cur):
            if nb in visited:
                continue
            if is_safe(state, occ, nb, depth):
                visited.add(nb)
                if nb in state.food:
                    return depth + 1  # path length in steps
                q.append(nb)
    return -1


def voronoi(state, occ, index):
    """Multi-source BFS from every alive head, one depth layer at a time.
    Returns (owned_free_squares_for_index, owned_food_depth or -1)."""
    depth = 0
    food_depth = -1
    MARK_SNAKE = -1
    visited = {}   # point -> snake_index (or MARK_SNAKE if contested)
    counts = [0] * len(state.snakes)

    q = deque()
    for i, s in enumerate(state.snakes):
        if s.alive:
            h = s.head
            q.append((h, i))
            visited[h] = i
    if not q:
        return (0, -1)
    PAIR_MARK = None
    q.append(PAIR_MARK)

    while q:
        item = q.popleft()
        if item is PAIR_MARK:
            depth += 1
            q.append(PAIR_MARK)
            if q[0] is PAIR_MARK:
                break
            continue
        cur, idx = item
        for nb in expand(state, cur):
            if nb in visited:
                other = visited[nb]
                if other != MARK_SNAKE and other != idx:
                    counts[other] -= 1
                    visited[nb] = MARK_SNAKE
            else:
                if is_safe(state, occ, nb, depth):
                    if nb in state.food and idx == index and food_depth == -1:
                        food_depth = depth
                    counts[idx] += 1
                    visited[nb] = idx
                    q.append((nb, idx))
    return (counts[index], food_depth)


def get_opponent(state, occ, index):
    """BFS from our head; the first differently-owned occupied neighbour cell
    determines the opponent (matches GameState::getOpponent)."""
    me = state.snakes[index]
    start = me.head
    depth = 0
    visited = {start}
    q = deque()
    q.append(start)
    MARK = None
    q.append(MARK)
    while q:
        cur = q.popleft()
        if cur is MARK:
            depth += 1
            q.append(MARK)
            if q[0] is MARK:
                break
            continue
        o = occ.get(cur)
        if o is not None and o[0] != index:
            return o[0]
        for nb in expand(state, cur):
            if nb in visited:
                continue
            if is_safe(state, occ, nb, depth):
                visited.add(nb)
                q.append(nb)
    return index


# ------------------------------------------------------------------------- #
# Simulation (GameState::makeMove + cleanup)
# ------------------------------------------------------------------------- #
def make_move(state, dname, idx):
    """Apply a move for snake idx. Grows if head lands on food or a free move
    remains; otherwise drops tail. Sets alive=False on self/wall collision."""
    s = state.snakes[idx]
    if not s.alive:
        return
    dx, dy = MOVES[dname]
    hx, hy = s.head
    new_head = (hx + dx, hy + dy)
    s.health -= 1

    # wall
    if not state.in_bounds(new_head):
        s.alive = False
        return

    ate = new_head in state.food

    # self collision: the C++ GameState::makeMove checks isOccupantOf(head,idx)
    # on the board BEFORE popping the tail, so stepping onto ANY of our own
    # currently-occupied cells (including the tail) is death. Match that: test
    # against the full old body.
    if new_head in s.body:
        s.alive = False
        # still advance head so downstream sees the move
        s.body.insert(0, new_head)
        return

    s.body.insert(0, new_head)
    if ate:
        s.health = MAX_HEALTH
        state.food.discard(new_head)
    elif s.free_moves > 0:
        s.free_moves -= 1
    else:
        s.body.pop()


def cleanup(state):
    """Resolve head-to-head collisions and dead snakes (GameState::cleanup)."""
    # dead by health
    for s in state.snakes:
        if s.alive and s.health <= 0:
            s.alive = False

    alive = [s for s in state.snakes if s.alive]
    # head-to-head and body overlaps
    for s in alive:
        if not s.alive:
            continue
        h = s.head
        for o in alive:
            if o is s or not o.alive:
                continue
            if h == o.head:
                # head-on: shorter (or equal) dies
                if s.size <= o.size:
                    s.alive = False
                    break
            else:
                # ran into opponent body segment (excluding its head handled above)
                if h in o.body[1:]:
                    s.alive = False
                    break


# ------------------------------------------------------------------------- #
# Heuristic evaluation (MinimaxSnake::scoreState)
# ------------------------------------------------------------------------- #
def score_state(state, idx):
    s = state.snakes[idx]
    if not s.alive:
        return NEG_INF
    if state.num_alive() == 1:
        return POS_INF

    occ = state.occupancy()
    free_squares, owned_food_depth = voronoi(state, occ, idx)
    if free_squares == 0:
        return NEG_INF

    score = free_squares * FREE_WEIGHT
    score += 100000.0 / state.num_alive()

    # food
    food_length = owned_food_depth
    if food_length == -1:
        d = bfs_food_dist(state, occ, s.head)
        food_length = d if d != -1 else None
    if food_length is not None and food_length != -1:
        if s.health < food_length:
            return NEG_INF
        rope = s.health - food_length
        score += FOOD_WEIGHT * math.atan(rope / FOOD_EXP)

    score += free_squares * FREE_WEIGHT
    score += (1.0 / s.size) * LENGTH_WEIGHT
    return score


# ------------------------------------------------------------------------- #
# Alpha-beta minimax (MinimaxSnake::alphabeta)
# ------------------------------------------------------------------------- #
def legal_moves(state, snake):
    """Directions that don't immediately reverse into the neck."""
    h = snake.head
    out = []
    for name, (dx, dy) in MOVES.items():
        p = (h[0] + dx, h[1] + dy)
        if snake.size > 1 and p == snake.body[1]:
            continue
        out.append(name)
    return out


class _Search:
    def __init__(self, deadline):
        self.deadline = deadline

    def timed_out(self):
        return time.monotonic() > self.deadline

    def alphabeta(self, state, idx, alpha, beta, depth, max_depth, max_player):
        me = state.snakes[idx]
        if depth == max_depth or not me.alive or self.timed_out():
            return (score_state(state, idx), None)

        occ = state.occupancy()
        opp_idx = get_opponent(state, occ, idx)

        if max_player:
            cur_max = NEG_INF
            cur_move = None
            for mv in legal_moves(state, me):
                ns = state.clone()
                make_move(ns, mv, idx)
                new_snake = ns.snakes[idx]
                new_head = new_snake.head

                score_adj = 0.0
                # potential head-on collision with an equal/larger opponent
                for i, other in enumerate(ns.snakes):
                    if i == idx or not other.alive:
                        continue
                    for nb in expand(ns, other.head):
                        if nb == new_head and new_snake.size <= other.size:
                            score_adj += -BIG / 10
                            break
                # tail-follow onto a snake that may have just eaten (doubled tail)
                o = occ.get(new_head)
                if o is not None:
                    other = state.snakes[o[0]]
                    if len(other.body) >= 2 and other.body[-1] == other.body[-2]:
                        score_adj += -BIG / 16

                child, _ = self.alphabeta(
                    ns, idx, alpha, beta, depth + 1, max_depth, False
                )
                if score_adj < 0:
                    child = score_adj
                if child > cur_max:
                    cur_max = child
                    cur_move = mv
                if cur_max > alpha:
                    alpha = cur_max
                if beta <= alpha:
                    break
            return (cur_max, cur_move)
        else:
            cur_min = POS_INF
            cur_move = None
            if opp_idx == idx:
                # No reachable opponent. The C++ min branch still loops (over
                # our own moves, none applied) and recurses at depth+1 as the
                # max player, so this ply is consumed. Match that by advancing
                # depth rather than staying at the same level.
                return self.alphabeta(
                    state, idx, alpha, beta, depth + 1, max_depth, True
                )
            opp = state.snakes[opp_idx]
            for mv in legal_moves(state, opp):
                ns = state.clone()
                make_move(ns, mv, opp_idx)
                cleanup(ns)
                child, _ = self.alphabeta(
                    ns, idx, alpha, beta, depth + 1, max_depth, True
                )
                if child < cur_min:
                    cur_min = child
                    cur_move = mv
                if cur_min < beta:
                    beta = cur_min
                if beta <= alpha:
                    break
            return (cur_min, cur_move)


def fallback_move(state, idx):
    """Any in-bounds move that lands on a currently-safe (distance 1) cell."""
    s = state.snakes[idx]
    occ = state.occupancy()
    h = s.head
    safe = []
    for name, (dx, dy) in MOVES.items():
        p = (h[0] + dx, h[1] + dy)
        if is_safe(state, occ, p, 1):
            safe.append(name)
    if safe:
        return safe[0]
    return "up"


def decide_move(state, idx):
    deadline = time.monotonic() + (MAX_TIME_MS / 1000.0)
    searcher = _Search(deadline)
    score, mv = searcher.alphabeta(
        state, idx, NEG_INF, POS_INF, 0, MAX_DEPTH, True
    )

    if mv is None or score < 0:
        return fallback_move(state, idx)

    # verify the chosen move doesn't immediately kill us
    ns = state.clone()
    make_move(ns, mv, idx)
    cleanup(ns)
    if not ns.snakes[idx].alive:
        return fallback_move(state, idx)
    return mv


# ------------------------------------------------------------------------- #
# v1 API adapter
# ------------------------------------------------------------------------- #
def build_state(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    food = [(f["x"], f["y"]) for f in board.get("food", [])]
    turn = game_state.get("turn", 0)
    free_moves = max(0, FREE_MOVES - turn)

    snakes = []
    for sj in board["snakes"]:
        body = [(p["x"], p["y"]) for p in sj["body"]]
        snakes.append(SnakeState(sj["id"], sj.get("health", 100), body, free_moves))

    state = State(w, h, food, snakes)
    my_id = game_state["you"]["id"]
    idx = 0
    for i, s in enumerate(snakes):
        if s.id == my_id:
            idx = i
            break
    return state, idx


def safe_fallback(game_state):
    """Absolute last resort: pick an in-bounds move that avoids all snake
    bodies (tails enterable). Never raises."""
    try:
        you = game_state["you"]
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head = you["body"][0]
        hx, hy = head["x"], head["y"]
        # occupied cells excluding tails (tails are enterable)
        blocked = set()
        for s in board["snakes"]:
            b = s["body"]
            n = len(b)
            for i, p in enumerate(b):
                if i == n - 1:
                    continue  # tail may move
                blocked.add((p["x"], p["y"]))
        best = None
        for name, (dx, dy) in MOVES.items():
            nx, ny = hx + dx, hy + dy
            if not (0 <= nx < w and 0 <= ny < h):
                continue
            if (nx, ny) in blocked:
                continue
            return name
        # nothing clean; pick any in-bounds
        for name, (dx, dy) in MOVES.items():
            nx, ny = hx + dx, hy + dy
            if 0 <= nx < w and 0 <= ny < h:
                best = name
                break
        return best or "up"
    except Exception:
        return "up"


# ------------------------------------------------------------------------- #
# CodeClash / Battlesnake entry points
# ------------------------------------------------------------------------- #
def info():
    return {
        "apiversion": "1",
        "author": "aleksiy325",
        "color": "#000F00",
        "head": "pixel",
        "tail": "pixel",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        state, idx = build_state(game_state)
        mv = decide_move(state, idx)
        if mv not in MOVES:
            mv = safe_fallback(game_state)
        return {"move": mv}
    except Exception:
        return {"move": safe_fallback(game_state)}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
