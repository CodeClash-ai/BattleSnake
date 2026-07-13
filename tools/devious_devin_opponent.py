"""
devious-devin — port of coreyja/battlesnake-rs `devious_devin_eval` (flagship minimax snake).

FIDELITY: approximate. Faithfully reimplements the paranoid minimax + the
`ScoreEndState` board-evaluation ordering (Lose < Tie < ShorterThanOpponent
< LongerThanOpponent < Win) and the A*-style shortest-path distances
(closest-food distance, opponent-head distance) from the original Rust
`score()` and `a_prime` modules. The Rust engine wraps that score with a
`WrappedScore` that additionally encodes, for terminal (Lose/Tie) states, the
number of snakes left alive (prefer fewer) and, for wins, a preference to win
sooner; those tie-breaks are reproduced here too. Search depth and total
wall-clock are capped for speed, so the tree explored is smaller than the Rust
engine's, and opponents are evaluated as a single paranoid layer per round
rather than the Rust per-snake ply cycle.

Pure stdlib. Modern Battlesnake v1 API (bottom-left origin, y-up).
"""

import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ---- geometry / API ----------------------------------------------------------
# up: y+1, down: y-1, left: x-1, right: x+1
MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}

# Search / time controls
MAX_DEPTH = int(os.environ.get("DEVIN_MAX_DEPTH", "3"))            # plies (each ply = one full round of moves)
TIME_LIMIT = float(os.environ.get("DEVIN_TIME_LIMIT", "0.03"))        # wall-clock guard in seconds
FOOD_PENALTY = 1         # matches APrimeOptions default (food_penalty=1)


def info():
    # Values taken verbatim from the original Rust `about()`:
    #   color "#99cc00", head "trans-rights-scarf", tail "rbc-necktie".
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#99cc00",
        "head": "trans-rights-scarf",
        "tail": "rbc-necktie",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---- board model -------------------------------------------------------------
class Board:
    """Lightweight mutable board used for minimax simulation."""

    __slots__ = ("w", "h", "food", "snakes", "me_id")

    def __init__(self, w, h, food, snakes, me_id):
        self.w = w
        self.h = h
        self.food = food          # set of (x, y)
        self.snakes = snakes      # dict id -> {"body":[(x,y)...], "health":int, "alive":bool}
        self.me_id = me_id

    def clone(self):
        snakes = {}
        for sid, s in self.snakes.items():
            snakes[sid] = {
                "body": list(s["body"]),
                "health": s["health"],
                "alive": s["alive"],
            }
        return Board(self.w, self.h, set(self.food), snakes, self.me_id)


def build_board(game_state):
    b = game_state["board"]
    w, h = b["width"], b["height"]
    food = set((f["x"], f["y"]) for f in b.get("food", []))
    snakes = {}
    for s in b["snakes"]:
        body = [(p["x"], p["y"]) for p in s["body"]]
        snakes[s["id"]] = {"body": body, "health": s.get("health", 100), "alive": True}
    me_id = game_state["you"]["id"]
    return Board(w, h, food, snakes, me_id)


def in_bounds(b, x, y):
    return 0 <= x < b.w and 0 <= y < b.h


def occupied_bodies(b, exclude_tail_of=None):
    """Set of cells occupied by snake bodies. Tails are enterable (they move),
    so we optionally drop each alive snake's last body segment."""
    cells = set()
    for sid, s in b.snakes.items():
        if not s["alive"]:
            continue
        body = s["body"]
        # tail is enterable unless the snake just ate (body[-1]==body[-2])
        if len(body) >= 2 and body[-1] != body[-2]:
            cells.update(body[:-1])
        else:
            cells.update(body)
    return cells


# ---- A* / BFS distances (avoid snake bodies, food penalty) -------------------
def shortest_distance(b, start, targets):
    """Cost of shortest path from start to nearest target avoiding snake bodies.
    Mirrors a_prime: stepping onto food costs +1 extra; targets are always
    reachable even if occupied. Returns int cost or None."""
    if not targets:
        return None
    targets = set(targets)
    blocked = occupied_bodies(b)
    import heapq

    def heuristic(pos):
        return min(abs(pos[0] - t[0]) + abs(pos[1] - t[1]) for t in targets)

    best = {start: 0}
    pq = [(heuristic(start), 0, start)]
    while pq:
        _, cost, cur = heapq.heappop(pq)
        if cur in targets:
            return cost
        if cost > best.get(cur, 1 << 30):
            continue
        for dx, dy in MOVES.values():
            nx, ny = cur[0] + dx, cur[1] + dy
            n = (nx, ny)
            if not in_bounds(b, nx, ny):
                continue
            if n not in targets and n in blocked:
                continue
            step = 1
            if n in b.food and n not in targets:
                step += FOOD_PENALTY
            ncost = cost + step
            if ncost < best.get(n, 1 << 30):
                best[n] = ncost
                heapq.heappush(pq, (ncost + heuristic(n), ncost, n))
    return None


def dist_to_closest_food(b, start):
    return shortest_distance(b, start, list(b.food))


# ---- scoring (mirror of ScoreEndState ordering) ------------------------------
# We encode ScoreEndState variants as tuples so Python ordering matches the Rust
# derive(Ord) on the enum (variant index dominates, then field-by-field).
#   0 Lose(depth)
#   1 Tie(depth)
#   2 ShorterThanOpponent(len_diff, neg_food_dist_opt, health)
#   3 LongerThanOpponent(neg_dist_to_opp_opt, len_diff, health)
#   4 Win(depth)
# Rust Option<i32>: None < Some(x). We encode Option as (0,) for None and
# (1, x) for Some(x) so tuple comparison matches.
def _opt(v):
    return (0, 0) if v is None else (1, v)


def score(b):
    """Reimplementation of devious_devin_eval::score for a live (non-terminal) board."""
    me = b.snakes[b.me_id]
    my_head = me["body"][0]
    my_length = len(me["body"])
    my_health = me["health"]

    opponents = [s for sid, s in b.snakes.items() if sid != b.me_id and s["alive"]]
    if not opponents:
        # No living opponents -> effectively winning; treat as very strong Long state.
        return (3, _opt(0), 10 ** 6, my_health)

    opp_heads = [o["body"][0] for o in opponents]
    max_opp_len = max(len(o["body"]) for o in opponents)
    length_difference = my_length - max_opp_len

    if max_opp_len >= my_length or my_health < 20:
        neg_food = dist_to_closest_food(b, my_head)
        neg_food = None if neg_food is None else -neg_food
        return (2, length_difference, _opt(neg_food), max(my_health, 50))

    neg_dist_to_opp = shortest_distance(b, my_head, opp_heads)
    neg_dist_to_opp = None if neg_dist_to_opp is None else -neg_dist_to_opp
    return (3, _opt(neg_dist_to_opp), max(length_difference, 4), max(my_health, 50))


# Terminal scores. The Rust `WrappedScore` orders terminal states as
#   Lose(Reverse(alive_count), depth) < Tie(Reverse(alive_count), depth)
#   < Scored(..) < Win(Reverse(depth))
# For Lose/Tie: prefer *fewer* snakes alive (Reverse) then *deeper* depth
# (survive longer). For Win: prefer to win *sooner* (Reverse(depth)).
# Our `score()` tuples above live in the "Scored" band (variant tags 2 and 3),
# so terminal tags must bracket them: 0/1 below, 4 above.
def win_score(depth):
    # Prefer winning sooner: smaller depth is better -> negate so larger tuple wins.
    return (4, -depth)


def lose_score(depth, alive_count):
    # Prefer fewer snakes alive (Reverse) then deeper depth (survive longer).
    return (0, -alive_count, depth)


def tie_score(depth, alive_count):
    return (1, -alive_count, depth)


# ---- simulation of one full turn (all snakes move) ---------------------------
def snake_moves(b, s):
    """Legal-ish candidate moves for a snake: in-bounds, not reversing into neck."""
    head = s["body"][0]
    neck = s["body"][1] if len(s["body"]) > 1 else None
    out = []
    for name, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        if not in_bounds(b, nx, ny):
            continue
        if neck is not None and (nx, ny) == neck:
            continue
        out.append((name, (nx, ny)))
    if not out:
        # forced move (still in-bounds if possible); fall back to any in-bounds
        for name, (dx, dy) in MOVES.items():
            nx, ny = head[0] + dx, head[1] + dy
            if in_bounds(b, nx, ny):
                out.append((name, (nx, ny)))
        if not out:
            out.append(("up", (head[0], head[1] + 1)))
    return out


def apply_moves(b, chosen):
    """Return new board after applying {sid: (x,y)} for all alive snakes.
    Handles food, health, self/other collisions, head-to-head."""
    nb = b.clone()
    new_heads = {}
    for sid, s in nb.snakes.items():
        if not s["alive"]:
            continue
        if sid not in chosen:
            s["alive"] = False
            continue
        new_heads[sid] = chosen[sid]

    # move bodies, handle food/health
    for sid, head in new_heads.items():
        s = nb.snakes[sid]
        ate = head in nb.food
        s["body"].insert(0, head)
        if ate:
            s["health"] = 100
            # grow: keep tail (do not pop)
        else:
            s["health"] -= 1
            s["body"].pop()

    # remove eaten food
    for sid, head in new_heads.items():
        if head in nb.food:
            nb.food.discard(head)

    # deaths: out of health
    for sid, s in nb.snakes.items():
        if s["alive"] and s["health"] <= 0:
            s["alive"] = False

    # collisions
    alive_ids = [sid for sid in new_heads if nb.snakes[sid]["alive"]]
    to_kill = set()
    for sid in alive_ids:
        head = nb.snakes[sid]["body"][0]
        if not in_bounds(nb, head[0], head[1]):
            to_kill.add(sid)
            continue
        # body collisions (any snake's body excluding own head)
        for osid in alive_ids:
            o = nb.snakes[osid]
            obody = o["body"]
            if osid == sid:
                collide_body = obody[1:]
            else:
                collide_body = obody[1:]  # other's head handled below via H2H
            if head in collide_body:
                to_kill.add(sid)
                break
    # head-to-head
    for sid in alive_ids:
        if sid in to_kill:
            continue
        head = nb.snakes[sid]["body"][0]
        for osid in alive_ids:
            if osid == sid:
                continue
            oh = nb.snakes[osid]["body"][0]
            if head == oh:
                # loser is the shorter (or both if equal)
                if len(nb.snakes[sid]["body"]) <= len(nb.snakes[osid]["body"]):
                    to_kill.add(sid)
    for sid in to_kill:
        nb.snakes[sid]["alive"] = False

    return nb


def alive_count(b):
    return sum(1 for s in b.snakes.values() if s["alive"])


# ---- paranoid minimax --------------------------------------------------------
def terminal_state(b, depth):
    """Return a terminal score tuple if game is over from my perspective, else None.
    `depth` is the ply count reached (larger = deeper). Matches the Rust
    WrappedScore terminal encoding (fewer snakes alive preferred, deeper depth
    preferred for Lose/Tie; sooner Win preferred)."""
    me_alive = b.snakes[b.me_id]["alive"]
    opps_alive = [sid for sid, s in b.snakes.items() if sid != b.me_id and s["alive"]]
    n_alive = alive_count(b)
    if not me_alive and not opps_alive:
        return tie_score(depth, n_alive)
    if not me_alive:
        return lose_score(depth, n_alive)
    if not opps_alive:
        return win_score(depth)
    return None


def minimax(b, depth, is_max, deadline):
    """Paranoid minimax. is_max=True -> my move layer; else opponents' layer.
    `depth` counts remaining plies. We separate my move from opponents' combined
    move (one ply each)."""
    # depth here is "remaining"; terminal depth uses (MAX_DEPTH - remaining) so
    # that sooner terminals get a smaller depth value.
    term = terminal_state(b, MAX_DEPTH - depth)
    if term is not None:
        return term, None
    if depth <= 0 or time.monotonic() > deadline:
        return score(b), None

    me_id = b.me_id

    if is_max:
        my_moves = snake_moves(b, b.snakes[me_id])
        best = None
        best_move = my_moves[0][0]
        for name, head in my_moves:
            val, _ = minimax_opponents(b, {me_id: head}, depth, deadline)
            if best is None or val > best:
                best = val
                best_move = name
            if time.monotonic() > deadline:
                break
        return best, best_move
    else:
        return minimax_opponents(b, {}, depth, deadline)


def minimax_opponents(b, my_choice, depth, deadline):
    """Opponents pick jointly the worst outcome for me (paranoid), given my_choice."""
    me_id = b.me_id
    opponents = [sid for sid, s in b.snakes.items() if sid != me_id and s["alive"]]

    if not opponents:
        nb = apply_moves(b, dict(my_choice))
        return minimax(nb, depth - 1, True, deadline)

    # Enumerate joint opponent moves. To bound cost, only enumerate the closest
    # opponent's moves fully and give others a greedy-toward-me heuristic move.
    # For faithfulness on 1v1 (the common eval case) we enumerate the single
    # opponent's moves exactly.
    worst = None
    if len(opponents) == 1:
        osid = opponents[0]
        combos = [{osid: h} for _, h in snake_moves(b, b.snakes[osid])]
    else:
        # limited enumeration: full for first opp, fixed greedy for the rest
        first = opponents[0]
        rest = opponents[1:]
        rest_choice = {}
        my_head = b.snakes[me_id]["body"][0]
        for rid in rest:
            mvs = snake_moves(b, b.snakes[rid])
            # greedy: move minimizing distance to my head
            mvs.sort(key=lambda nm: abs(nm[1][0] - my_head[0]) + abs(nm[1][1] - my_head[1]))
            rest_choice[rid] = mvs[0][1]
        combos = []
        for _, h in snake_moves(b, b.snakes[first]):
            c = dict(rest_choice)
            c[first] = h
            combos.append(c)

    for oc in combos:
        chosen = dict(my_choice)
        chosen.update(oc)
        nb = apply_moves(b, chosen)
        val, _ = minimax(nb, depth - 1, True, deadline)
        if worst is None or val < worst:
            worst = val
        if time.monotonic() > deadline:
            break
    return worst, None


# ---- safe fallback -----------------------------------------------------------
def safe_fallback(b):
    """Return any in-bounds move not into a snake body (tails enterable)."""
    me = b.snakes[b.me_id]
    head = me["body"][0]
    neck = me["body"][1] if len(me["body"]) > 1 else None
    blocked = occupied_bodies(b)
    for name, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        if not in_bounds(b, nx, ny):
            continue
        if neck is not None and (nx, ny) == neck:
            continue
        if (nx, ny) in blocked:
            continue
        return name
    # nothing safe; pick any in-bounds
    for name, (dx, dy) in MOVES.items():
        nx, ny = head[0] + dx, head[1] + dy
        if in_bounds(b, nx, ny):
            return name
    return "up"


# ---- entrypoint --------------------------------------------------------------
def move(game_state):
    try:
        b = build_board(game_state)
        deadline = time.monotonic() + TIME_LIMIT

        best_move = None
        # iterative deepening for a good time-bounded answer
        for depth in range(2, MAX_DEPTH + 1):
            if time.monotonic() > deadline:
                break
            val, mv = minimax(b, depth, True, deadline)
            if mv is not None:
                best_move = mv
            if time.monotonic() > deadline:
                break

        if best_move is None:
            best_move = safe_fallback(b)

        # final safety: never step into a known body or out of bounds
        me = b.snakes[b.me_id]
        head = me["body"][0]
        dx, dy = MOVES[best_move]
        nx, ny = head[0] + dx, head[1] + dy
        blocked = occupied_bodies(b)
        if not in_bounds(b, nx, ny) or (nx, ny) in blocked:
            best_move = safe_fallback(b)

        return {"move": best_move}
    except Exception:
        # absolute last resort
        try:
            b = build_board(game_state)
            return {"move": safe_fallback(b)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
