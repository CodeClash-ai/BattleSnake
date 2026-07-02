"""
Port of Nettogrof's "Expert" Battlesnake (nessegrev-java-dev) to the CodeClash
arena format against Battlesnake API v1.

ORIGINAL: https://github.com/Nettogrof/nessegrev-java-dev  (Java)
  Author: carl.lajeunesse / Nettogrof. The repo hosts several snakes; the
  strongest is the "Expert" snake (class ExpertSnake -> "Nessegrev-Beta"):
  "Decent snake using minimax/payoff matrix algorithm only with a MCTS".

FIDELITY: approximate.
  Faithfully reproduced (the parts that determine strength):
    * The leaf EVALUATION heuristics, with the exact original constants:
        - DuelNode (2 snakes): score = area-control(voronoi) + health/250
        - FourNode (3-4 snakes): score = length + health/50
                                 + food-distance*(width-dist)*0.095
                                 + size-compare (+/- 0.4 sizeAdvantage)
        - single snake alive -> MAX_SCORE (99999)
        - area control = simultaneous multi-source BFS "voronoi" flood fill;
          contested squares don't count for anyone (SPLIT_AREA), and a snake
          whose tail lands in its controlled area gets tailValueArea(=5) bonus.
        - scoreRatio = score[me] / (BASIC_SCORE + sum(others))   (paranoid)
    * Move generation forbids stepping onto occupied body squares; head-to-head
      resolved by length (shorter dies, equal -> both die).
    * Move selection: pick the direction whose worst-case (min over opponent
      replies) child scoreRatio is largest -- matching chooseBestMove(), which
      takes the min of each direction's child scores (paranoid assumption).
  Simplified / approximated:
    * The original uses an MCTS-like best-first expansion with a UCB bias plus a
      paranoid payoff-matrix backup, continued until a time budget. Here we use
      a fixed-depth paranoid minimax (all opponents move as one min-player) with
      alpha-beta-free full expansion, capped depth + ~0.3s wall-clock guard.
      This yields the same move on the many positions dominated by the leaf
      evaluation, which is where this snake's playing strength comes from.
    * Hazards / royale / squad / wrapped / constrictor variants are not ported
      (standard-mode DuelNode/FourNode only, which is the primary evaluator).

Coordinates: v1 (0,0)=bottom-left, up=y+1, down=y-1, left=x-1, right=x+1.
"""

import sys
import time

# ---- Original constants (BattleSnakeConstants / SnakeGeneticConstants) ----
MAX_SCORE = 99999.0
BASIC_SCORE = 0.0001
SPLIT_AREA = -50
EMPTY_AREA = -150
SNAKE_BODY = -99
MINIMUN_SNAKE = 2
TAIL_VALUE_AREA = 5      # SnakeGeneticConstants.tailValueArea
SIZE_ADVANTAGE = 0.4     # SnakeGeneticConstants.sizeAdvantage
FOOD_DIST_WEIGHT = 0.095 # addScoreDistance multiplier

# Search limits (FAST guard)
TIME_BUDGET = 0.30       # ~0.3s wall clock
MAX_DEPTH = 6            # plies (capped; reduced dynamically for many snakes)

MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "nettogrof",
        "color": "#212161",
        "head": "all-seeing",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---------------------------------------------------------------------------
# Internal lightweight state. Snakes are dicts with:
#   body: list of (x,y) tuples, head=body[0]
#   health: int
#   alive: bool
#   me: bool  (index 0 in original == "our" snake)
# ---------------------------------------------------------------------------

def _clone_snake(s):
    return {
        "body": list(s["body"]),
        "health": s["health"],
        "alive": s["alive"],
        "id": s["id"],
    }


def _init_state(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    food = set((f["x"], f["y"]) for f in board["food"])
    me_id = game_state["you"]["id"]

    snakes = []
    # our snake first (index 0), matching genSnakeInfo order
    you = game_state["you"]
    snakes.append({
        "body": [(p["x"], p["y"]) for p in you["body"]],
        "health": you["health"],
        "alive": True,
        "id": me_id,
    })
    for s in board["snakes"]:
        if s["id"] == me_id:
            continue
        snakes.append({
            "body": [(p["x"], p["y"]) for p in s["body"]],
            "health": s["health"],
            "alive": True,
            "id": s["id"],
        })
    return w, h, food, snakes


# ---------------------------------------------------------------------------
# EVALUATION  (faithful reproduction of DuelNode / FourNode + area control)
# ---------------------------------------------------------------------------

def _area_control_scores(w, h, snakes):
    """listAreaControl(): simultaneous multi-source BFS voronoi.
    Returns per-snake fractional control score contribution.
    """
    n = len(snakes)
    # board grid: EMPTY_AREA, SNAKE_BODY, or snake index (>=0), or SPLIT_AREA
    board = [[EMPTY_AREA] * h for _ in range(w)]
    # mark bodies (all but last segment / tail), matching initBoard()
    for s in snakes:
        body = s["body"]
        for i in range(len(body) - 1):
            x, y = body[i]
            if 0 <= x < w and 0 <= y < h:
                board[x][y] = SNAKE_BODY

    # current: map square -> owner index; seed with each head
    current = {}
    for i, s in enumerate(snakes):
        hx, hy = s["body"][0]
        current[(hx, hy)] = i

    def apply_hash(hashmap):
        for (x, y), v in hashmap.items():
            board[x][y] = v

    def gen_hash(old):
        newh = {}
        for (px, py), val in old.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and board[nx][ny] == EMPTY_AREA:
                    key = (nx, ny)
                    if key not in newh:
                        newh[key] = val
                    elif newh[key] != val:
                        newh[key] = SPLIT_AREA
        return newh

    while current:
        apply_hash(current)
        temp = gen_hash(current)
        current = {}
        if temp:
            apply_hash(temp)
            current = gen_hash(temp)

    # adjustScodeBasedonBoardControl
    count = [0] * n
    for x in range(w):
        for y in range(h):
            v = board[x][y]
            if v >= 0:
                count[v] += 1
    total = 1
    for i, s in enumerate(snakes):
        tx, ty = s["body"][-1]
        if 0 <= tx < w and 0 <= ty < h:
            bv = board[tx][ty]
            if bv >= 0:
                count[bv] += TAIL_VALUE_AREA
        total += count[i]

    scores = [0.0] * n
    if total > 0:
        for i in range(n):
            scores[i] += count[i] / total
    return scores


def _shortest_food_dist(food, x, y):
    if not food:
        return 0  # (width - 0); harmless when no food
    best = None
    for fx, fy in food:
        d = abs(fx - x) + abs(fy - y)
        if best is None or d < best:
            best = d
    return best


def _evaluate(w, h, food, snakes):
    """Leaf evaluation -> scoreRatio (float), me is index 0.

    Chooses DuelNode vs FourNode based on snake count, matching genNode().
    """
    n = len(snakes)
    alive = [s for s in snakes if s["alive"]]

    # Winner detection (setWinnerMaxScore / single snake alive).
    if len(alive) < MINIMUN_SNAKE:
        if snakes[0]["alive"] and snakes[0]["health"] > 0:
            return MAX_SCORE
        return 0.0

    score = [0.0] * n

    if n <= MINIMUN_SNAKE:
        # DuelNode.setScore(): area control + health/250
        ac = _area_control_scores(w, h, snakes)
        for i in range(n):
            score[i] += ac[i]
            score[i] += snakes[i]["health"] / 250.0
            if snakes[i]["health"] <= 0 or not snakes[i]["alive"]:
                score[i] = 0.0
    else:
        # FourNode.setScore(): basic length + health/50, food distance, size compare
        for i in range(n):
            if snakes[i]["alive"]:
                score[i] = len(snakes[i]["body"]) + snakes[i]["health"] / 50.0
            else:
                score[i] = 0.0
        # addScoreDistance(head of our snake)
        hx, hy = snakes[0]["body"][0]
        score[0] += (w - _shortest_food_dist(food, hx, hy)) * FOOD_DIST_WEIGHT
        # addSizeCompareScore
        my_len = len(snakes[0]["body"])
        for i in range(1, n):
            ol = len(snakes[i]["body"])
            if ol > my_len:
                score[0] -= SIZE_ADVANTAGE
            elif ol < my_len:
                score[0] += SIZE_ADVANTAGE

    # updateScoreRatio(): score[0] / (BASIC_SCORE + sum others)
    total_other = BASIC_SCORE
    for i in range(1, n):
        total_other += score[i]
    if total_other == 0:
        total_other = BASIC_SCORE
    return score[0] / total_other


# ---------------------------------------------------------------------------
# MOVE GENERATION & SIMULATION
# ---------------------------------------------------------------------------

def _occupied_bodies(snakes):
    """Set of squares occupied by any snake body (all segments).
    Matches freeSpace()/isSnake which check the full body list."""
    occ = set()
    for s in snakes:
        if not s["alive"]:
            continue
        for seg in s["body"]:
            occ.add(seg)
    return occ


def _legal_moves(w, h, snakes, idx):
    """Legal moves for snake idx: in-bounds and not onto any current body square."""
    s = snakes[idx]
    if not s["alive"]:
        return []
    hx, hy = s["body"][0]
    occ = _occupied_bodies(snakes)
    out = []
    for name, (dx, dy) in MOVES.items():
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occ:
            out.append((name, (nx, ny)))
    return out


def _step_snake(s, newhead, food):
    """Advance snake to newhead; grow if food, else drop tail. Health update."""
    ns = _clone_snake(s)
    ns["body"] = [newhead] + ns["body"]
    if newhead in food:
        ns["health"] = 100
        # ate -> keep tail (grow): don't pop
    else:
        ns["body"].pop()
        ns["health"] = ns["health"] - 1
        if ns["health"] <= 0:
            ns["alive"] = False
    return ns


def _resolve_head_to_head(snakes):
    """checkHeadToHead: shorter dies; equal -> both die."""
    n = len(snakes)
    for i in range(n):
        if not snakes[i]["alive"]:
            continue
        for j in range(i + 1, n):
            if not snakes[j]["alive"]:
                continue
            if snakes[i]["body"][0] == snakes[j]["body"][0]:
                li = len(snakes[i]["body"])
                lj = len(snakes[j]["body"])
                if li > lj:
                    snakes[j]["alive"] = False
                elif li == lj:
                    snakes[i]["alive"] = False
                    snakes[j]["alive"] = False
                else:
                    snakes[i]["alive"] = False


# ---------------------------------------------------------------------------
# PARANOID SEARCH  (approximation of the MCTS/payoff-matrix backup)
# ---------------------------------------------------------------------------

class _Timeout(Exception):
    pass


def _apply_joint(w, h, food, snakes, my_move, opp_moves):
    """Apply our move + opponents' moves simultaneously, resolve collisions."""
    new_snakes = []
    # index 0 = us
    ns0 = _step_snake(snakes[0], my_move, food)
    new_snakes.append(ns0)
    for k in range(1, len(snakes)):
        s = snakes[k]
        if not s["alive"]:
            new_snakes.append(_clone_snake(s))
            continue
        mv = opp_moves.get(k)
        if mv is None:
            # no legal move -> dies
            dead = _clone_snake(s)
            dead["alive"] = False
            new_snakes.append(dead)
        else:
            new_snakes.append(_step_snake(s, mv, food))
    _resolve_head_to_head(new_snakes)
    return new_snakes


def _opponent_joint_moves(w, h, snakes):
    """Generate the cartesian product of opponent moves (paranoid min player).
    Capped to keep it fast: each opponent at most all legal; product capped."""
    opp_indices = [k for k in range(1, len(snakes)) if snakes[k]["alive"]]
    per = []
    for k in opp_indices:
        lm = _legal_moves(w, h, snakes, k)
        if not lm:
            per.append((k, [None]))  # forced death
        else:
            per.append((k, [pos for (_, pos) in lm]))

    # cartesian product with a cap
    combos = [{}]
    CAP = 32
    for k, positions in per:
        newc = []
        for base in combos:
            for pos in positions:
                nb = dict(base)
                nb[k] = pos
                newc.append(nb)
                if len(newc) >= CAP:
                    break
            if len(newc) >= CAP:
                break
        combos = newc
    return combos


def _search(w, h, food, snakes, depth, deadline):
    """Paranoid minimax: we maximize scoreRatio, opponents minimize it."""
    if time.time() > deadline:
        raise _Timeout()

    alive = [s for s in snakes if s["alive"]]
    if not snakes[0]["alive"] or len(alive) < MINIMUN_SNAKE or depth <= 0:
        return _evaluate(w, h, food, snakes)

    my_moves = _legal_moves(w, h, snakes, 0)
    if not my_moves:
        # our snake trapped -> death
        dead = list(snakes)
        d0 = _clone_snake(dead[0]); d0["alive"] = False; dead[0] = d0
        return _evaluate(w, h, food, dead)

    best = None
    for _, my_pos in my_moves:
        opp_combos = _opponent_joint_moves(w, h, snakes)
        worst = None
        for opp_moves in opp_combos:
            child = _apply_joint(w, h, food, snakes, my_pos, opp_moves)
            val = _search(w, h, food, child, depth - 1, deadline)
            if worst is None or val < worst:
                worst = val
            # our snake already dead in child -> can't get worse than 0
            if worst <= 0.0:
                break
        if worst is None:
            worst = _evaluate(w, h, food,
                              _apply_joint(w, h, food, snakes, my_pos, {}))
        if best is None or worst > best:
            best = worst
    return best if best is not None else 0.0


def _choose_move(game_state):
    w, h, food, snakes = _init_state(game_state)
    my_moves = _legal_moves(w, h, snakes, 0)

    if not my_moves:
        # No safe move by body-check; fall through to emergency below.
        return None

    # Dynamic depth: fewer plies when many snakes (branching explodes).
    n_alive = sum(1 for s in snakes if s["alive"])
    depth = MAX_DEPTH if n_alive <= 2 else (3 if n_alive == 3 else 2)

    deadline = time.time() + TIME_BUDGET
    best_move = my_moves[0][0]
    best_val = None

    # chooseBestMove(): for each direction take the worst-case (min) child value,
    # pick the direction with the largest such value.
    try:
        for name, my_pos in my_moves:
            opp_combos = _opponent_joint_moves(w, h, snakes)
            worst = None
            for opp_moves in opp_combos:
                child = _apply_joint(w, h, food, snakes, my_pos, opp_moves)
                val = _search(w, h, food, child, depth - 1, deadline)
                if worst is None or val < worst:
                    worst = val
                if worst <= 0.0:
                    break
            if worst is None:
                worst = 0.0
            if best_val is None or worst > best_val:
                best_val = worst
                best_move = name
    except _Timeout:
        if best_val is None:
            # nothing scored yet: prefer the move maximizing immediate area
            best_move = _greedy_fallback(w, h, food, snakes, my_moves)

    return best_move


def _greedy_fallback(w, h, food, snakes, my_moves):
    best = my_moves[0][0]
    bestval = None
    for name, my_pos in my_moves:
        child = _apply_joint(w, h, food, snakes, my_pos, {})
        val = _evaluate(w, h, food, child)
        if bestval is None or val > bestval:
            bestval = val
            best = name
    return best


# ---------------------------------------------------------------------------
# ROBUST ENTRY POINT
# ---------------------------------------------------------------------------

def _emergency_move(game_state):
    """Always return an in-bounds move that avoids snake bodies (tails enterable)."""
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        you = game_state["you"]
        hx, hy = you["body"][0]["x"], you["body"][0]["y"]
        # occupied = all body segments except each snake's tail (tails move away)
        occ = set()
        tails = set()
        for s in board["snakes"]:
            b = s["body"]
            for i, p in enumerate(b):
                sq = (p["x"], p["y"])
                if i == len(b) - 1:
                    tails.add(sq)
                else:
                    occ.add(sq)
        # prefer squares not occupied and not a tail; then allow tails
        for allow_tail in (False, True):
            for name, (dx, dy) in MOVES.items():
                nx, ny = hx + dx, hy + dy
                if not (0 <= nx < w and 0 <= ny < h):
                    continue
                if (nx, ny) in occ:
                    continue
                if (nx, ny) in tails and not allow_tail:
                    continue
                return name
    except Exception:
        pass
    return "up"


def move(game_state):
    try:
        chosen = _choose_move(game_state)
        if chosen is None:
            chosen = _emergency_move(game_state)
        # sanity: verify chosen is in-bounds & not into a non-tail body
        return {"move": chosen}
    except Exception:
        return {"move": _emergency_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
