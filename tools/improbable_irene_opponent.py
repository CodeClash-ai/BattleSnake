"""
Port of `improbable_irene` from https://github.com/coreyja/battlesnake-rs
(battlesnake-rs/src/improbable_irene.rs). Owner: coreyja. Botname: improbable-irene.

FIDELITY: faithful reimplementation of the MCTS approach.
- Monte Carlo Tree Search with 2-ply expansion (my move -> opponents' joint responses).
- Selection via UCB1-Normal (constant 16; return +inf when visits <= 8*ln(iters)).
- Random-rollout simulation: up to 25 steps of "random reasonable moves" for each snake,
  then evaluate.
- Leaf evaluation: terminal -> +1 win / -1 loss / -0.25 draw; otherwise a
  "spread from head" flood fill (squares_per_snake_with_scores, cycles=5,
  food=5, hazard=1, empty=5) scored as my_space / total_space.
- If we are the only snake left -> go Right.
Adapted to modern v1 API (bottom-left origin, y-up) and a ~0.3s wall-clock cap.
"""

import math
import random
import time

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
MOVE_ORDER = ["up", "down", "left", "right"]

import os
TIME_LIMIT = float(os.environ.get("IRENE_TIME_LIMIT", "0.03"))  # seconds wall-clock guard
MAX_ITERATIONS = int(os.environ.get("IRENE_MAX_ITERATIONS", "120"))  # search cap
SIM_STEPS = 25
FLOOD_CYCLES = 5
SCORE_FOOD = 5
SCORE_HAZARD = 1
SCORE_EMPTY = 5


# ---------------------------------------------------------------------------
# Lightweight game state
# ---------------------------------------------------------------------------
class State:
    __slots__ = ("width", "height", "food", "hazards", "snakes", "you_id")

    def __init__(self, width, height, food, hazards, snakes, you_id):
        self.width = width
        self.height = height
        self.food = food          # set of (x, y)
        self.hazards = hazards    # set of (x, y)
        self.snakes = snakes      # list of dicts: id, health, body(list of (x,y))
        self.you_id = you_id

    @staticmethod
    def from_wire(gs):
        board = gs["board"]
        width = board["width"]
        height = board["height"]
        food = set((f["x"], f["y"]) for f in board.get("food", []))
        hazards = set((h["x"], h["y"]) for h in board.get("hazards", []))
        snakes = []
        for s in board["snakes"]:
            body = [(p["x"], p["y"]) for p in s["body"]]
            snakes.append({
                "id": s["id"],
                "health": s.get("health", 100),
                "body": body,
            })
        you_id = gs["you"]["id"]
        return State(width, height, food, hazards, snakes, you_id)

    def clone(self):
        snakes = [{"id": s["id"], "health": s["health"], "body": list(s["body"])}
                  for s in self.snakes]
        return State(self.width, self.height, set(self.food), self.hazards,
                     snakes, self.you_id)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def is_over(self):
        return len(self.snakes) <= 1

    def get_winner(self):
        if len(self.snakes) == 1:
            return self.snakes[0]["id"]
        return None  # draw (0 snakes) or not over

    def find(self, sid):
        for s in self.snakes:
            if s["id"] == sid:
                return s
        return None


# ---------------------------------------------------------------------------
# Move legality (reasonable moves): avoid out-of-bounds and stepping into any
# occupied body cell except a tail that will vacate (tails enterable).
# ---------------------------------------------------------------------------
def occupied_cells(state, exclude_tail=True):
    """Map of body cells -> True. Tails are excluded when exclude_tail (they move)."""
    occ = set()
    for s in state.snakes:
        body = s["body"]
        n = len(body)
        for i, seg in enumerate(body):
            # tail vacates unless the snake just ate (tail overlaps prev seg)
            if exclude_tail and i == n - 1 and n > 1:
                if body[-1] != body[-2]:
                    continue
            occ.add(seg)
    return occ


def reasonable_moves_for_snake(state, snake, occ):
    head = snake["body"][0]
    result = []
    for mv in MOVE_ORDER:
        dx, dy = MOVES[mv]
        nx, ny = head[0] + dx, head[1] + dy
        if not state.in_bounds(nx, ny):
            continue
        if (nx, ny) in occ:
            continue
        result.append(mv)
    if not result:
        # No safe move; still must return something.
        result = ["up"]
    return result


# ---------------------------------------------------------------------------
# Simulate one turn given a move for each snake (by id).
# ---------------------------------------------------------------------------
def simulate_turn(state, moves_by_id):
    ns = state.clone()
    new_heads = {}
    for s in ns.snakes:
        mv = moves_by_id.get(s["id"], "up")
        dx, dy = MOVES[mv]
        hx, hy = s["body"][0]
        nh = (hx + dx, hy + dy)
        new_heads[s["id"]] = nh
        s["body"].insert(0, nh)
        s["health"] -= 1
        # eat?
        if nh in ns.food:
            s["health"] = 100
            ns.food.discard(nh)
            # grow: don't pop tail
        else:
            s["body"].pop()

    # Resolve deaths.
    dead = set()
    # out of bounds / health / self+body collisions
    for s in ns.snakes:
        head = s["body"][0]
        if not ns.in_bounds(head[0], head[1]):
            dead.add(s["id"])
            continue
        if s["health"] <= 0:
            dead.add(s["id"])
            continue

    # body collisions (excluding own head) and head-to-head
    for s in ns.snakes:
        if s["id"] in dead:
            continue
        head = s["body"][0]
        for other in ns.snakes:
            ob = other["body"]
            if other["id"] == s["id"]:
                # self collision with own body (skip head index 0)
                if head in ob[1:]:
                    dead.add(s["id"])
                    break
            else:
                # collide with other's body (non-head)
                if head in ob[1:]:
                    dead.add(s["id"])
                    break
                # head to head
                if head == ob[0]:
                    if len(s["body"]) <= len(ob):
                        dead.add(s["id"])
                        break

    ns.snakes = [s for s in ns.snakes if s["id"] not in dead]
    return ns


def random_reasonable_turn(state, rng):
    occ = occupied_cells(state, exclude_tail=True)
    moves = {}
    for s in state.snakes:
        opts = reasonable_moves_for_snake(state, s, occ)
        moves[s["id"]] = rng.choice(opts)
    return simulate_turn(state, moves)


# ---------------------------------------------------------------------------
# Flood-fill scoring: "spread from head" (BFS). Longer snakes claim first.
# ---------------------------------------------------------------------------
def squares_per_snake_with_scores(state):
    w, h = state.width, state.height

    # sort snake ids by length descending
    ordered = sorted(state.snakes, key=lambda s: -len(s["body"]))
    ids = [s["id"] for s in ordered]

    grid = {}  # (x,y) -> sid
    # mark all bodies
    for s in ordered:
        for seg in s["body"]:
            grid[seg] = s["id"]

    # BFS frontiers per snake, starting from heads
    frontiers = {s["id"]: [s["body"][0]] for s in ordered}

    for _ in range(FLOOD_CYCLES):
        if all(len(frontiers[i]) == 0 for i in ids):
            break
        new_frontiers = {i: [] for i in ids}
        for i in ids:  # process in length order (longer first wins ties)
            for (x, y) in frontiers[i]:
                for dx, dy in MOVES.values():
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        continue
                    cell = (nx, ny)
                    if cell in grid:
                        continue
                    grid[cell] = i
                    new_frontiers[i].append(cell)
        frontiers = new_frontiers

    totals = {i: 0 for i in ids}
    for cell, sid in grid.items():
        if cell in state.hazards:
            val = SCORE_HAZARD
        elif cell in state.food:
            val = SCORE_FOOD
        else:
            val = SCORE_EMPTY
        totals[sid] += val
    return totals


def score_state(state):
    me = state.you_id
    if state.is_over():
        winner = state.get_winner()
        if winner is None:
            return -0.25
        return 1.0 if winner == me else -1.0
    totals = squares_per_snake_with_scores(state)
    my_space = totals.get(me, 0)
    total_space = sum(totals.values())
    if total_space == 0:
        return 0.0
    return my_space / total_space


# ---------------------------------------------------------------------------
# MCTS
# ---------------------------------------------------------------------------
class Node:
    __slots__ = ("state", "parent", "my_move", "children",
                 "visits", "total_score", "sum_sq", "expanded", "is_my_turn")

    def __init__(self, state, parent=None, my_move=None, is_my_turn=True):
        self.state = state
        self.parent = parent
        self.my_move = my_move          # the "my move" that led to this node (my-move layer)
        self.children = None
        self.visits = 0
        self.total_score = 0.0
        self.sum_sq = 0.0
        self.expanded = False
        self.is_my_turn = is_my_turn

    def average_score(self):
        if self.visits == 0:
            return None
        return self.total_score / self.visits

    def ucb1_normal(self, total_iters):
        v = self.visits
        if v <= 8.0 * math.log(max(total_iters, 2)):
            return float("inf")
        avg = self.total_score / v
        var_num = self.sum_sq - v * (avg ** 2)
        first = var_num / (v - 1) if v > 1 else 0.0
        second = math.log(max(total_iters - 1, 1)) / v
        inside = 16.0 * first * second
        if inside < 0:
            inside = 0.0
        return avg + math.sqrt(inside)


def expand(node):
    """Build the 2-ply children structure.

    my-turn node -> for each reasonable my-move, create a my-move child node;
    each my-move child -> for each combination of opponent moves, create an
    outcome node (is_my_turn=True) holding the resulting state.
    """
    node.expanded = True
    state = node.state
    if state.is_over():
        node.children = []
        return

    me = state.find(state.you_id)
    if me is None:
        node.children = []
        return

    occ = occupied_cells(state, exclude_tail=True)
    my_moves = reasonable_moves_for_snake(state, me, occ)

    opponents = [s for s in state.snakes if s["id"] != state.you_id]
    opp_move_lists = []
    for o in opponents:
        opp_move_lists.append((o["id"], reasonable_moves_for_snake(state, o, occ)))

    children = []
    for mv in my_moves:
        mv_child = Node(state, parent=node, my_move=mv, is_my_turn=False)
        mv_child.expanded = True
        outcomes = []
        for combo in _combos(opp_move_lists):
            moves_by_id = {state.you_id: mv}
            moves_by_id.update(combo)
            nxt = simulate_turn(state, moves_by_id)
            outcomes.append(Node(nxt, parent=mv_child, my_move=mv, is_my_turn=True))
        if not outcomes:
            nxt = simulate_turn(state, {state.you_id: mv})
            outcomes.append(Node(nxt, parent=mv_child, my_move=mv, is_my_turn=True))
        mv_child.children = outcomes
        children.append(mv_child)
    node.children = children


def _combos(move_lists):
    """Cartesian product of opponent moves, capped to keep branching small."""
    if not move_lists:
        return [{}]
    # Cap combinations to avoid explosion.
    results = [{}]
    for (oid, moves) in move_lists:
        new_results = []
        for r in results:
            for m in moves:
                nr = dict(r)
                nr[oid] = m
                new_results.append(nr)
        results = new_results
        if len(results) > 32:
            random.shuffle(results)
            results = results[:32]
    return results


def next_leaf(node, total_iters):
    cur = node
    while cur.expanded and cur.children:
        nxt = max(cur.children, key=lambda c: c.ucb1_normal(total_iters))
        if nxt is None:
            break
        cur = nxt
    return cur


def simulate(node, rng):
    state = node.state
    steps = 0
    while steps < SIM_STEPS and not state.is_over():
        steps += 1
        state = random_reasonable_turn(state, rng)
    return score_state(state)


def backpropagate(node, score):
    cur = node
    while cur is not None:
        cur.visits += 1
        cur.total_score += score
        cur.sum_sq += score * score
        cur = cur.parent


def mcts(root_state, deadline, rng):
    root = Node(root_state, is_my_turn=True)
    expand(root)
    iters = 0
    while iters < MAX_ITERATIONS and time.time() < deadline:
        iters += 1
        leaf = next_leaf(root, iters)
        if leaf.visits > 0 and not leaf.expanded:
            expand(leaf)
            leaf = next_leaf(root, iters)
        score = simulate(leaf, rng)
        backpropagate(leaf, score)
    return root


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#5a25a8",
        "head": "hydra",
        "tail": "mystic-moon",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _fallback_move(state):
    """Any in-bounds move not into a snake body (tails enterable)."""
    me = state.find(state.you_id)
    if me is None:
        return "up"
    occ = occupied_cells(state, exclude_tail=True)
    opts = reasonable_moves_for_snake(state, me, occ)
    if opts:
        return opts[0]
    # last resort: any in-bounds
    head = me["body"][0]
    for mv in MOVE_ORDER:
        dx, dy = MOVES[mv]
        if state.in_bounds(head[0] + dx, head[1] + dy):
            return mv
    return "up"


def move(game_state):
    try:
        state = State.from_wire(game_state)
        deadline = time.time() + TIME_LIMIT
        rng = random.Random(game_state.get("turn", 0) * 2654435761 & 0xFFFFFFFF)

        # Only snake left -> go Right (matches Rust behaviour).
        if len(state.snakes) <= 1:
            return {"move": "right"}

        root = mcts(state, deadline, rng)

        best = None
        best_avg = None
        if root.children:
            for c in root.children:
                a = c.average_score()
                if a is None:
                    continue
                if best_avg is None or a > best_avg:
                    best_avg = a
                    best = c
        if best is not None and best.my_move is not None:
            chosen = best.my_move
            # Safety: ensure legal.
            me = state.find(state.you_id)
            occ = occupied_cells(state, exclude_tail=True)
            legal = reasonable_moves_for_snake(state, me, occ)
            if chosen in legal or not legal:
                return {"move": chosen}
        return {"move": _fallback_move(state)}
    except Exception:
        try:
            state = State.from_wire(game_state)
            return {"move": _fallback_move(state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
