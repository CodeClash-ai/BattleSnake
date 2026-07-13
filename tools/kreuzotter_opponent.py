import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
CodeClash port of Team "Niedersaechsische Kreuzotter" (m-schier/battlesnake-2019),
2nd place Intermediate Division, Battlesnake 2019.

Faithful reimplementation of the original C# submission's adversarial game-tree
search (MaxN with AlphaBeta fallback for duels), reflex-mask opponent selection,
iterative deepening, a full game simulation ("FastWorld.UpdateMovementTick"), and
the primary flood-fill / length / hunger heuristics.

Original C#: MaxN.cs, AlphaBeta.cs, Util.cs, FastWorld.cs, FastSnake.cs,
PrimaryMultiHeuristic.cs, PrimaryDuellingHeuristic.cs and the Absolute* / *Advantage
metrics. The original internal model used a TOP-LEFT coordinate system (North=y-1);
this port works directly in the v1 API BOTTOM-LEFT system (up=y+1). Direction naming
is remapped accordingly; the algorithm and heuristics are otherwise reproduced.

Pure stdlib, single file. Depth-capped iterative deepening with a wall-clock guard
to stay comfortably under 1s.
"""

import math
import time
from collections import deque

# ---------------------------------------------------------------------------
# Directions (v1 API, bottom-left origin: up=y+1, down=y-1, left=x-1, right=x+1)
# The original iterated directions in the order North, West, South, East.
# We keep the same iteration order (using v1 semantics) for behavioural fidelity.
# ---------------------------------------------------------------------------
UP = "up"
DOWN = "down"
LEFT = "left"
RIGHT = "right"

# original order: North, West, South, East  -> in v1: up, left, down, right
DIRECTIONS = [UP, LEFT, DOWN, RIGHT]

_DELTA = {
    UP: (0, 1),
    DOWN: (0, -1),
    LEFT: (-1, 0),
    RIGHT: (1, 0),
}


def _advance(pos, d):
    dx, dy = _DELTA[d]
    return (pos[0] + dx, pos[1] + dy)


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _single_step_direction(frm, to):
    if frm[0] < to[0]:
        return RIGHT
    if frm[0] > to[0]:
        return LEFT
    if frm[1] < to[1]:
        return UP
    return DOWN


# Kill reason codes (mirror InternalModel.Status)
ALIVE = 0
KILLED_HEAD_ON_HEAD = 1
KILLED_ENEMY_BODY = 2
KILLED_STARVATION = 3
KILLED_OWN_BODY = 4
KILLED_WALL = 5


def _score_kill_reason(status):
    # BaseDuellingHeuristic.ScoreKillReason: higher is worse
    if status == KILLED_HEAD_ON_HEAD:
        return 1
    if status in (KILLED_STARVATION, KILLED_ENEMY_BODY):
        return 2
    if status in (KILLED_OWN_BODY, KILLED_WALL):
        return 3
    return 0


# ---------------------------------------------------------------------------
# Fast world / snake model (port of FastWorld.cs + FastSnake.cs)
# fields grid stores occupant: None (empty/fruit handled separately),
# or ('snake', id, direction_left). We keep a simpler dict-based representation.
# ---------------------------------------------------------------------------

EMPTY = 0
SNAKE = 1
FRUIT = 2


class FastSnake:
    __slots__ = ("index", "head", "tail", "health", "length", "max_length",
                 "pending_max_length", "status", "last_direction")

    def __init__(self, index):
        self.index = index
        self.head = None
        self.tail = None
        self.health = 100
        self.length = 1
        self.max_length = 3
        self.pending_max_length = 3
        self.status = ALIVE
        self.last_direction = UP

    @property
    def alive(self):
        return self.status == ALIVE

    def clone(self):
        s = FastSnake(self.index)
        s.head = self.head
        s.tail = self.tail
        s.health = self.health
        s.length = self.length
        s.max_length = self.max_length
        s.pending_max_length = self.pending_max_length
        s.status = self.status
        s.last_direction = self.last_direction
        return s

    def grow(self):
        self.pending_max_length += 1
        self.health = 101  # matches original (+1, decreased later)

    def update_post_tick(self):
        self.max_length = self.pending_max_length

    def will_grow_on_update(self):
        return self.length != self.max_length

    def peek_length(self):
        return self.length if self.length == self.max_length else self.length + 1


class FastWorld:
    __slots__ = ("width", "height", "turn", "occ", "sid", "sdir",
                 "fruits", "snakes")

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.turn = 0
        # occupant grid, snake-id grid, direction-left grid, indexed [y][x]
        self.occ = [[EMPTY] * width for _ in range(height)]
        self.sid = [[0] * width for _ in range(height)]
        self.sdir = [[UP] * width for _ in range(height)]
        self.fruits = set()
        self.snakes = []

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def occ_at(self, pos):
        return self.occ[pos[1]][pos[0]]

    def clone(self):
        w = FastWorld(self.width, self.height)
        w.turn = self.turn
        w.occ = [row[:] for row in self.occ]
        w.sid = [row[:] for row in self.sid]
        w.sdir = [row[:] for row in self.sdir]
        w.fruits = set(self.fruits)
        w.snakes = [s.clone() for s in self.snakes]
        return w

    @property
    def is_decided(self):
        alive = sum(1 for s in self.snakes if s.alive)
        return alive <= 1

    # ---- construction from v1 API game_state ----
    @staticmethod
    def from_api(game_state):
        board = game_state["board"]
        w = FastWorld(board["width"], board["height"])
        w.turn = game_state.get("turn", 0)

        for f in board.get("food", []):
            p = (f["x"], f["y"])
            if w.occ[p[1]][p[0]] == EMPTY:
                w.occ[p[1]][p[0]] = FRUIT
                w.fruits.add(p)

        for i, s in enumerate(board["snakes"]):
            body = [(c["x"], c["y"]) for c in s["body"]]
            snake = FastSnake(i)
            head = body[0]
            snake.head = head

            # growth-left: duplicate body parts at the tail indicate pending growth
            tail_coord = body[-1]
            growth_left = 0
            for j in range(len(body) - 2, -1, -1):
                if body[j] == tail_coord:
                    growth_left += 1
                else:
                    break
            effective_length = len(body) - growth_left

            # head direction (from body[1] -> body[0])
            head_dir = UP
            if effective_length > 1:
                head_dir = _single_step_direction(body[1], body[0])
            w.occ[head[1]][head[0]] = SNAKE
            w.sid[head[1]][head[0]] = i
            w.sdir[head[1]][head[0]] = head_dir

            # lay down body parts up to effective length; the direction stored
            # on each cell is the direction the snake *left* that cell in.
            for j in range(1, effective_length):
                c = body[j]
                if w.occ[c[1]][c[0]] == SNAKE:
                    continue  # avoid double placement on self-overlap
                d_left = _single_step_direction(body[j], body[j - 1])
                w.occ[c[1]][c[0]] = SNAKE
                w.sid[c[1]][c[0]] = i
                w.sdir[c[1]][c[0]] = d_left

            snake.health = s["health"]
            snake.length = effective_length
            snake.max_length = len(body)
            snake.pending_max_length = len(body)
            # effective tail = last distinct body cell
            snake.tail = body[effective_length - 1]
            snake.last_direction = head_dir
            w.snakes.append(snake)

        return w

    def certainly_deadly(self, index, d):
        self_snake = self.snakes[index]
        nxt = _advance(self_snake.head, d)
        if not self.in_bounds(nxt):
            return True
        if self.occ[nxt[1]][nxt[0]] != SNAKE:
            return False
        # running into another snake may be safe (they might die)
        if self.sid[nxt[1]][nxt[0]] != index:
            return False
        # running into our own tail may be safe
        return self_snake.tail != nxt

    def _perform_tail_move(self, s):
        if s.length == s.max_length:
            t = s.tail
            new_tail = _advance(t, self.sdir[t[1]][t[0]])
            self.occ[t[1]][t[0]] = EMPTY
            s.tail = new_tail
            s.length -= 1

    def _perform_head_move(self, s, d):
        h = s.head
        # write direction we left old head in
        self.sdir[h[1]][h[0]] = d
        s.head = _advance(h, d)
        nh = s.head
        self.occ[nh[1]][nh[0]] = SNAKE
        self.sid[nh[1]][nh[0]] = index_val = s.index
        self.sdir[nh[1]][nh[0]] = d
        s.length += 1
        s.last_direction = d

    def _kill(self, s, reason):
        # clear cells from tail to head
        current = s.tail
        while True:
            d = self.sdir[current[1]][current[0]]
            self.occ[current[1]][current[0]] = EMPTY
            if current == s.head:
                break
            current = _advance(current, d)
        s.status = reason

    def update_movement_tick(self, moves):
        snakes = self.snakes
        n = len(snakes)
        desired = []
        for i in range(n):
            s = snakes[i]
            if s.alive:
                desired.append(_advance(s.head, moves[i]))
            else:
                desired.append((-1, -1))

        # kill out of bounds
        for i in range(n):
            s = snakes[i]
            if not s.alive:
                continue
            p = desired[i]
            if not self.in_bounds(p):
                self._kill(s, KILLED_WALL)

        # head-on-head collisions (multi-way), longest survives (unless tie)
        for i in range(n):
            if not snakes[i].alive:
                continue
            target = desired[i]
            matches = 1
            longest = snakes[i].peek_length()
            longest_count = 1
            for j in range(i + 1, n):
                if not snakes[j].alive:
                    continue
                if desired[j] == target:
                    matches += 1
                    pl = snakes[j].peek_length()
                    if longest < pl:
                        longest = pl
                        longest_count = 1
                    elif longest == pl:
                        longest_count += 1
            if matches == 1:
                continue
            for j in range(i, n):
                if not snakes[j].alive:
                    continue
                if desired[j] == target and (snakes[j].peek_length() < longest or longest_count > 1):
                    self._kill(snakes[j], KILLED_HEAD_ON_HEAD)

        # consume fruit
        for i in range(n):
            s = snakes[i]
            if not s.alive:
                continue
            nh = desired[i]
            if self.occ[nh[1]][nh[0]] == FRUIT:
                self.fruits.discard(nh)
                self.occ[nh[1]][nh[0]] = EMPTY
                s.grow()

        # head-on-body / tail collisions
        for i in range(n):
            s = snakes[i]
            if not s.alive:
                continue
            nh = desired[i]
            if self.occ[nh[1]][nh[0]] == SNAKE:
                other_id = self.sid[nh[1]][nh[0]]
                other = snakes[other_id]
                if other.tail != nh or other.will_grow_on_update():
                    if other_id == i:
                        self._kill(s, KILLED_OWN_BODY)
                    else:
                        self._kill(s, KILLED_ENEMY_BODY)

        # starvation
        for i in range(n):
            s = snakes[i]
            if not s.alive:
                continue
            s.health -= 1
            if s.health <= 0:
                self._kill(s, KILLED_STARVATION)

        # move tails then heads
        for i in range(n):
            if snakes[i].alive:
                self._perform_tail_move(snakes[i])
        for i in range(n):
            if snakes[i].alive:
                self._perform_head_move(snakes[i], moves[i])

        for i in range(n):
            snakes[i].update_post_tick()

        self.turn += 1


# ---------------------------------------------------------------------------
# Flood fill helpers (port of Util.cs)
# ---------------------------------------------------------------------------

def count_basic_flood_fill(world, start):
    """BFS from start over empty/fruit tiles. Returns (count, distances[y][x])."""
    w, h = world.width, world.height
    dist = [[0] * w for _ in range(h)]
    q = deque()
    q.append((start, 0))
    count = 0
    while q:
        (cx, cy), cd = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            nd = cd + 1
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if dist[ny][nx] > 0:
                continue
            dist[ny][nx] = nd
            occ = world.occ[ny][nx]
            if occ != EMPTY and occ != FRUIT:
                continue
            q.append(((nx, ny), nd))
            count += 1
    return count, dist


class AdversarialFillResult:
    __slots__ = ("tile_snake", "tile_dist", "empty_counts")

    def __init__(self, tile_snake, tile_dist, empty_counts):
        self.tile_snake = tile_snake  # [y][x] -> snake index or None
        self.tile_dist = tile_dist    # [y][x] -> distance
        self.empty_counts = empty_counts


def generate_flood_fill_board(world):
    """Simultaneous multi-source BFS, longest snake expands first (port)."""
    w, h = world.width, world.height
    tile_snake = [[None] * w for _ in range(h)]
    tile_dist = [[0] * w for _ in range(h)]
    empty_counts = [0] * len(world.snakes)

    seeds = [(s.index, 0, s.head) for s in world.snakes]
    # sort by max length descending so longest snake expands most freely
    seeds.sort(key=lambda it: world.snakes[it[0]].max_length, reverse=True)

    q = deque(seeds)
    while q:
        snake_idx, cd, (cx, cy) = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if tile_snake[ny][nx] is not None:
                continue
            tile_snake[ny][nx] = snake_idx
            tile_dist[ny][nx] = cd + 1
            if world.occ[ny][nx] == SNAKE:
                continue
            empty_counts[snake_idx] += 1
            q.append((snake_idx, cd + 1, (nx, ny)))

    return AdversarialFillResult(tile_snake, tile_dist, empty_counts)


class CachedMultiMetricState:
    __slots__ = ("world", "_adv")

    def __init__(self, world):
        self.world = world
        self._adv = None

    @property
    def adversarial_fill(self):
        if self._adv is None:
            self._adv = generate_flood_fill_board(self.world)
        return self._adv


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def metric_absolute_control(state, index):
    fill = state.adversarial_fill.empty_counts
    friendly = fill[index]
    total = sum(fill)
    if total == 0:
        return 0.0
    return ((friendly / float(total)) - 0.5) * 2.0


def metric_absolute_hunger(state, index,
                           base_reserve=10.0, distance_mult=1.2,
                           satisfaction_threshold=75):
    w = state.world
    s = w.snakes[index]
    if s.health > satisfaction_threshold:
        return 1.0
    adv = state.adversarial_fill
    best = math.inf
    for (fx, fy) in w.fruits:
        if adv.tile_snake[fy][fx] == index:
            best = min(best, adv.tile_dist[fy][fx])
    own_pressure = min(s.health - best * distance_mult - base_reserve, 0)
    logistic = math.pow(0.85, -own_pressure)
    return (logistic - 0.5) * 2.0


def metric_absolute_distance_to_own_tail(state, index):
    w = state.world
    s = w.snakes[index]
    t = s.tail
    reachable = state.adversarial_fill.tile_snake[t[1]][t[0]] == index
    if not reachable:
        sufficient = state.adversarial_fill.empty_counts[index] > s.max_length
        return 1.0 if sufficient else -1.0
    return 1.0


def _score_delta_advantage(delta, delta_x_scale=0.2):
    return (1.0 / (1.0 + math.exp(-(delta * delta_x_scale))) - 0.5) * 2.0


def _food_distance_metric(w, index, dist, decay=0.2):
    best = math.inf
    for (fx, fy) in w.fruits:
        d = dist[fy][fx]
        if d <= 0:
            continue
        best = min(best, d)
    if best is math.inf:
        return 0.0
    return math.exp(-decay * best)


def metric_absolute_combined_delta_length_food(w, index, fill_count, fill_dist,
                                               fruit_mult_factor=1.0):
    max_len = 0
    sum_len = 0
    other_count = 0
    for i, s in enumerate(w.snakes):
        if i == index or not s.alive:
            continue
        sum_len += s.length
        other_count += 1
        if s.length > max_len:
            max_len = s.length
    if other_count == 0:
        average_len = 0.0
    else:
        average_len = sum_len / float(other_count)
    interp_len = 0.9 * max_len + 0.1 * average_len
    delta_adv = w.snakes[index].length - interp_len
    delta_metric = _score_delta_advantage(delta_adv)
    delta_on_eat = _score_delta_advantage(delta_adv + 1)
    food_mult = (delta_on_eat - delta_metric) * fruit_mult_factor
    return delta_metric + _food_distance_metric(w, index, fill_dist) * food_mult


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

class PrimaryMultiHeuristic:
    """Port of PrimaryMultiHeuristic + BaseMultiHeuristic."""
    TAIL_SCORE_MULT = 10.0

    def __init__(self, bounty_snake):
        self.bounty = bounty_snake

    def is_terminal(self, state):
        return state.world.is_decided or not state.world.snakes[self.bounty].alive

    def score(self, state, index):
        me = state.world.snakes[index]
        s = 0.0
        if not state.world.snakes[self.bounty].alive and index != self.bounty:
            s += 2000.0
        if not me.alive:
            return s - 1000.0 + state.world.turn / 100.0 - _score_kill_reason(me.status)
        if self.is_terminal(state):
            return s + 1000.0 - state.world.turn / 100.0
        return self._score_detail(state, index)

    def _score_detail(self, state, index):
        w = state.world
        me = w.snakes[index]
        fill_count, fill_dist = count_basic_flood_fill(w, me.head)
        delta_len = 12.0 * metric_absolute_combined_delta_length_food(
            w, index, fill_count, fill_dist)
        control = 1.0 * metric_absolute_control(state, index)
        hunger = 10.0 * metric_absolute_hunger(state, index)
        dist_tail = self.TAIL_SCORE_MULT * metric_absolute_distance_to_own_tail(state, index)
        score = delta_len + control + hunger
        if me.max_length > 6:
            score += dist_tail
        return score


def _duel_total_fill_advantage(own_count, enemy_count):
    """Port of TotalFillAdvantage.ScoreCached.
    Basic-flood-fill tile counts from each head: (own/(own+enemy) - 0.5)*2."""
    denom = own_count + enemy_count
    if denom == 0:
        return 0.0
    return (own_count / float(denom) - 0.5) * 2.0


def _duel_adversarial_fill_advantage(adv, own_index, enemy_index):
    """Port of AdversarialFillAdvantage.ScoreCached.
    Counts *all* adversarial-fill tiles owned by own vs enemy (including snake
    body tiles that were assigned an owner), normalised over own+enemy."""
    friendly = 0
    enemy = 0
    ts = adv.tile_snake
    for row in ts:
        for owner in row:
            if owner == own_index:
                friendly += 1
            elif owner == enemy_index:
                enemy += 1
    denom = friendly + enemy
    if denom == 0:
        # matches C# division by zero producing NaN guarded implicitly; be safe
        return 0.0
    return (friendly / float(denom) - 0.5) * 2.0


def _duel_hunger_pressure_advantage(world, adv, own_index, enemy_index,
                                    satisfaction_threshold=75):
    """Port of HungerPressureAdvantage.ScoreCached."""
    best_own = math.inf
    best_enemy = math.inf
    for (fx, fy) in world.fruits:
        owner = adv.tile_snake[fy][fx]
        if owner == own_index:
            best_own = min(best_own, adv.tile_dist[fy][fx])
        elif owner == enemy_index:
            best_enemy = min(best_enemy, adv.tile_dist[fy][fx])

    own_s = world.snakes[own_index]
    enemy_s = world.snakes[enemy_index]
    own_pressure = min(own_s.health - best_own * 1.2 - 10.0, 0)
    enemy_pressure = min(enemy_s.health - best_enemy * 1.2 - 10.0, 0)

    if own_s.health > satisfaction_threshold:
        own_pressure = 0.0
    if enemy_s.health > satisfaction_threshold:
        enemy_pressure = 0.0

    if own_pressure == enemy_pressure:
        return 0.0
    return (enemy_pressure / (own_pressure + enemy_pressure) - 0.5) * 2.0


def _duel_combined_delta_length(world, own_index, enemy_index, own_fill_dist,
                                delta_x_scale=0.2):
    """Port of (duel) CombinedDeltaLengthFoodMetric.ScoreCached.
    Uses direct own-minus-enemy length delta and own basic-fill food distance;
    fruit multiplier factor is implicitly 1 (deltaOnEat - delta)."""
    delta_adv = world.snakes[own_index].length - world.snakes[enemy_index].length
    delta_metric = _score_delta_advantage(delta_adv, delta_x_scale)
    delta_on_eat = _score_delta_advantage(delta_adv + 1, delta_x_scale)
    food_mult = delta_on_eat - delta_metric
    return delta_metric + _food_distance_metric(world, own_index, own_fill_dist) * food_mult


class PrimaryDuellingHeuristic:
    """Port of PrimaryDuellingHeuristic + BaseDuellingHeuristic.

    Faithful reproduction of the four duel metrics (see original C# files
    TotalFillAdvantage, HungerPressureAdvantage, AdversarialFillAdvantage and
    the duel CombinedDeltaLengthFoodMetric) weighted totalFill 0.7, hunger 10,
    adversarial fill 4, combined length 4.
    """

    def __init__(self, snake_index, enemy_index):
        self.snake_index = snake_index
        self.enemy_index = enemy_index

    def is_terminal(self, world):
        return (not world.snakes[self.snake_index].alive
                or not world.snakes[self.enemy_index].alive)

    def score(self, world):
        me = world.snakes[self.snake_index]
        enemy = world.snakes[self.enemy_index]
        if not me.alive and not enemy.alive:
            return -900.0 + world.turn / 100.0
        if not me.alive:
            return -1000.0 + world.turn / 100.0 - _score_kill_reason(me.status)
        if not enemy.alive:
            return 1000.0 - world.turn / 100.0
        return self._score_detail(world)

    def _score_detail(self, world):
        i = self.snake_index
        j = self.enemy_index
        state = CachedMultiMetricState(world)
        adv = state.adversarial_fill

        # TotalFillAdvantage: basic flood fill from own and enemy heads
        own_count, own_fill_dist = count_basic_flood_fill(world, world.snakes[i].head)
        enemy_count, _ = count_basic_flood_fill(world, world.snakes[j].head)
        total_fill_adv = _duel_total_fill_advantage(own_count, enemy_count)

        # AdversarialFillAdvantage: count of owned tiles (own vs enemy)
        adversarial_fill_adv = _duel_adversarial_fill_advantage(adv, i, j)

        # HungerPressureAdvantage
        hunger_adv = _duel_hunger_pressure_advantage(world, adv, i, j)

        # CombinedDeltaLengthFoodMetric (duel form): uses own basic-fill distances
        combined_len_adv = _duel_combined_delta_length(world, i, j, own_fill_dist)

        return (0.7 * total_fill_adv
                + 10.0 * hunger_adv
                + 4.0 * adversarial_fill_adv
                + 4.0 * combined_len_adv)


# ---------------------------------------------------------------------------
# Reflex evasion (port of ReflexEvasionHeuristic + Util.ImprovedReflexBasedEvade)
# ---------------------------------------------------------------------------

def reflex_evasion_score(w, index, move):
    if w.certainly_deadly(index, move):
        return -1000.0
    s = w.snakes[index]
    new_head = _advance(s.head, move)

    enemy_collision = 0.0
    if w.occ[new_head[1]][new_head[0]] == SNAKE:
        enemy_collision -= 1.0

    fruit = 0.0
    if w.occ[new_head[1]][new_head[0]] == FRUIT:
        fruit = 1.0

    potential = 0.0
    for i, other in enumerate(w.snakes):
        if not other.alive or i == index:
            continue
        if _manhattan(other.head, new_head) == 1:
            delta = s.length - other.length
            if delta == 0:
                potential -= 0.5
            elif delta > 0:
                potential += 0.3
            else:
                potential -= 1.0

    hold = 1.0 if move == s.last_direction else 0.0

    return hold * 1.0 + fruit * 3.0 + potential * 10.0 + enemy_collision * 30.0


def improved_reflex_based_evade(w, index):
    best = UP
    best_score = -math.inf
    for d in DIRECTIONS:
        sc = reflex_evasion_score(w, index, d)
        if sc > best_score:
            best_score = sc
            best = d
    return best


# ---------------------------------------------------------------------------
# Search: reflex mask, ordering, AlphaBeta duel, MaxN multi
# ---------------------------------------------------------------------------

class StopSearch(Exception):
    pass


def _has_closer_part(world, snake, target, max_distance):
    # enumerate snake parts from tail to head
    current = snake.tail
    while True:
        if _manhattan(target, current) <= max_distance:
            return True
        if current == snake.head:
            break
        current = _advance(current, world.sdir[current[1]][current[0]])
    return False


def find_mask_for_depth(world, own_index, depth):
    n = len(world.snakes)
    result = [True] * n
    max_desired = depth * 2
    own_head = world.snakes[own_index].head
    for i in range(n):
        if i == own_index:
            result[i] = False
            continue
        if not world.snakes[i].alive:
            continue
        result[i] = not _has_closer_part(world, world.snakes[i], own_head, max_desired)
    return result


def calculate_stepping_ordering(world, own_index, reflex_mask):
    order = [own_index]
    for i in range(len(world.snakes)):
        if reflex_mask[i] or i == own_index:
            continue
        order.append(i)
    return order


class _Deadline:
    __slots__ = ("t_end",)

    def __init__(self, t_end):
        self.t_end = t_end

    def check(self):
        if time.monotonic() >= self.t_end:
            raise StopSearch()


# ---- AlphaBeta duel (port of AlphaBeta.cs) ----

def alphabeta_best(world, heuristic, own_index, enemy_index, max_depth,
                   current_depth, alpha, beta_initial, deadline):
    terminal = heuristic.is_terminal(world)
    limit_reached = current_depth >= max_depth
    if terminal or limit_reached:
        return UP, heuristic.score(world)

    best_own = UP
    desired = [improved_reflex_based_evade(world, i) for i in range(len(world.snakes))]

    checked_own = False
    for i_idx in range(len(DIRECTIONS)):
        must_own = (not checked_own) and i_idx == len(DIRECTIONS) - 1
        d_own = DIRECTIONS[i_idx]
        if not must_own and world.certainly_deadly(own_index, d_own):
            continue
        checked_own = True

        beta = beta_initial
        checked_enemy = True  # matches original (initialised True)
        for j_idx in range(len(DIRECTIONS)):
            deadline.check()
            must_enemy = (not checked_enemy) and j_idx == len(DIRECTIONS) - 1
            d_enemy = DIRECTIONS[j_idx]
            if not must_enemy and world.certainly_deadly(enemy_index, d_enemy):
                continue
            desired[own_index] = d_own
            desired[enemy_index] = d_enemy
            inst = world.clone()
            inst.update_movement_tick(desired)
            _, score = alphabeta_best(inst, heuristic, own_index, enemy_index,
                                      max_depth, current_depth + 1, alpha, beta, deadline)
            if score < beta:
                beta = score
            if alpha >= beta:
                break
        if beta > alpha:
            alpha = beta
            best_own = d_own
        if alpha >= beta_initial:
            break

    return best_own, alpha


# ---- MaxN multi (port of MaxN.PseudoPlyStep) ----

def _score_advantage(cached_state, reflex_mask, heuristic):
    count = len(cached_state.world.snakes)
    phi_abs = []
    total = 0.0
    for i in range(count):
        if reflex_mask[i]:
            phi_abs.append(0.0)
        else:
            val = heuristic.score(cached_state, i)
            phi_abs.append(val)
            total += val
    avg = total / count
    phi_rel = [v - avg for v in phi_abs]
    return phi_abs, phi_rel


def pseudo_ply_step(world, reflex_mask, depth, heuristic, own_index,
                    current_depth, current_ply_depth, ordering, moves, deadline):
    deadline.check()

    if current_ply_depth == len(ordering):
        new_w = world.clone()
        new_w.update_movement_tick(moves)
        cached = CachedMultiMetricState(new_w)
        next_depth = current_depth + 1
        old_moves = list(moves)
        if next_depth == depth or heuristic.is_terminal(cached):
            phi_abs, phi_rel = _score_advantage(cached, reflex_mask, heuristic)
        else:
            phi_abs, phi_rel, _ = pseudo_ply_step(
                new_w, reflex_mask, depth, heuristic, own_index,
                next_depth, 0, ordering, None, deadline)
        return phi_abs, phi_rel, old_moves

    if current_ply_depth == 0:
        moves = []
        for i in range(len(world.snakes)):
            if world.snakes[i].alive and reflex_mask[i]:
                moves.append(improved_reflex_based_evade(world, i))
            else:
                moves.append(UP)

    own = ordering[current_ply_depth]
    alpha = -math.inf
    phi_rel_max = None
    phi_abs_max = None
    dir_max = None

    for i_idx in range(len(DIRECTIONS)):
        must_eval = phi_rel_max is None and i_idx == len(DIRECTIONS) - 1
        d = DIRECTIONS[i_idx]
        if not must_eval and world.certainly_deadly(own, d):
            continue
        moves[own] = d
        phi_abs_s, phi_rel_s, directions = pseudo_ply_step(
            world, reflex_mask, depth, heuristic, own_index,
            current_depth, current_ply_depth + 1, ordering, moves, deadline)
        phi_star = phi_rel_s[own]
        if alpha < phi_star:
            alpha = phi_star
            phi_rel_max = phi_rel_s
            phi_abs_max = phi_abs_s
            dir_max = directions

    return phi_abs_max, phi_rel_max, dir_max


def search_selecting_strategy(world, own_index, depth, deadline):
    reflex_mask = find_mask_for_depth(world, own_index, depth)
    simulated_count = sum(1 for m in reflex_mask if not m)
    ordering = calculate_stepping_ordering(world, own_index, reflex_mask)

    if simulated_count == 2:
        heuristic = PrimaryDuellingHeuristic(ordering[0], ordering[1])
        direction, _ = alphabeta_best(world, heuristic, ordering[0], ordering[1],
                                      depth, 0, -math.inf, math.inf, deadline)
        return direction

    heuristic = PrimaryMultiHeuristic(own_index)
    _, _, directions = pseudo_ply_step(
        world, reflex_mask, depth, heuristic, own_index, 0, 0, ordering, None, deadline)
    return directions[own_index]


# Depth cap for the iterative deepening (keeps search bounded even if fast).
MAX_DEPTH = int(__import__("os").environ.get("KREUZ_MAX_DEPTH", "3"))
TIME_BUDGET = float(__import__("os").environ.get("KREUZ_TIME_BUDGET", "0.03"))  # seconds


def choose_move(world, own_index):
    t_end = time.monotonic() + TIME_BUDGET
    deadline = _Deadline(t_end)
    best = None
    for depth in range(1, MAX_DEPTH + 1):
        try:
            result = search_selecting_strategy(world, own_index, depth, deadline)
            if result is not None:
                best = result
        except StopSearch:
            break
    return best


# ---------------------------------------------------------------------------
# Safe fallback (never crash / never self-collide)
# ---------------------------------------------------------------------------

def _safe_fallback(game_state):
    you = game_state["you"]
    board = game_state["board"]
    w, h = board["width"], board["height"]
    head = (you["head"]["x"], you["head"]["y"])

    occupied = set()
    tails = set()
    for s in board["snakes"]:
        body = [(c["x"], c["y"]) for c in s["body"]]
        for c in body:
            occupied.add(c)
        # a tail cell will be vacated next turn unless the snake just ate
        if len(body) >= 2 and body[-1] != body[-2]:
            tails.add(body[-1])

    def ok(d):
        nx, ny = _advance(head, d)
        if not (0 <= nx < w and 0 <= ny < h):
            return False
        p = (nx, ny)
        if p in occupied and p not in tails:
            return False
        return True

    for d in (UP, DOWN, LEFT, RIGHT):
        if ok(d):
            return d
    # nothing safe; at least stay in bounds
    for d in (UP, DOWN, LEFT, RIGHT):
        nx, ny = _advance(head, d)
        if 0 <= nx < w and 0 <= ny < h:
            return d
    return UP


# ---------------------------------------------------------------------------
# CodeClash / Battlesnake v1 entry points
# ---------------------------------------------------------------------------

def info():
    return {
        "apiversion": "1",
        "author": "m-schier",
        "color": "#E3CE7A",
        "head": "evil",
        "tail": "curled",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def move(game_state):
    try:
        world = FastWorld.from_api(game_state)
        my_id = game_state["you"]["id"]
        own_index = None
        for i, s in enumerate(game_state["board"]["snakes"]):
            if s["id"] == my_id:
                own_index = i
                break
        if own_index is None:
            return {"move": _safe_fallback(game_state)}

        chosen = choose_move(world, own_index)

        # Validate the chosen move is not certainly deadly; otherwise fall back.
        if chosen is None or world.certainly_deadly(own_index, chosen):
            fb = _safe_fallback(game_state)
            # prefer chosen if fallback also unsafe but chosen at least in-bounds
            if chosen is not None:
                nx, ny = _advance(world.snakes[own_index].head, chosen)
                if world.in_bounds((nx, ny)) and world.certainly_deadly(own_index, fb):
                    return {"move": chosen}
            return {"move": fb}

        return {"move": chosen}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
