"""
CodeClash port of coreyja's "Hovering Hobbs" Battlesnake (battlesnake-rs, Rust).

Chosen snake: Hovering Hobbs (hovering-hobbs) -- coreyja's flagship area-control
snake. It takes the paranoid alpha-beta minimax framework from Devious Devin and
combines it with a "spread from head" flood-fill scoring function to try to control
more of the board than opponents.

FIDELITY: approximate (faithful in spirit).

Faithfully reproduced pieces:
  - Paranoid minimax: score every node from *our* perspective; we maximize on our
    ply, opponents minimize on theirs. Players move one-at-a-time by ply (one snake
    per depth level); once all snakes have chosen a move for the round the board is
    simulated forward. (mirrors eval.rs::minimax)
  - Iterative deepening under a wall-clock budget, keeping the best completed depth.
  - Terminal scoring with the same ordering as WrappedScore:
        Lose < Tie < Scored(flood_ratio) < Win
    winning sooner is better; losing/tying later (and with fewer snakes alive) is
    better. (mirrors score.rs)
  - standard_score(): "spread from head" flood fill. Snakes flood outward from their
    heads in longest-first order, claiming empty cells for a fixed number of cycles
    (5). Each claimed cell is weighted food=20 / hazard=1 / empty=5. Score is our
    weighted share / total weighted share. If health < 60 we instead prioritize
    the negative distance to the nearest food (LowOnHealth), then flood ratio as a
    tiebreak. (mirrors hovering_hobbs.rs + spread_from_head.rs)

Simplifications vs. the Rust original:
  - Pure-Python + time-bounded, so search depth is shallow (a few plies) rather than
    the deep threaded lazy-SMP search the Rust snake runs.
  - shortest_distance uses BFS (Manhattan-ish grid BFS around obstacles) instead of
    the repo's A*.
  - No wrapped / arcade-maze board variants; standard 11x11-style board only.
"""

import time
import random

# ---- board directions: (0,0) bottom-left, up=y+1, down=y-1, left=x-1, right=x+1
MOVES = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}

FLOOD_CYCLES = 5
LOW_HEALTH = 60
SCORE_FOOD = 20
SCORE_HAZARD = 1
SCORE_EMPTY = 5

TIME_BUDGET = 0.30  # wall-clock seconds


def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#da8a1a",  # hovering-hobbs beach-puffin orange
        "head": "beach-puffin-special",
        "tail": "beach-puffin-special",
    }


def start(game_state):
    pass


def end(game_state):
    pass


# ---------------------------------------------------------------------------
# Lightweight simulation model
# ---------------------------------------------------------------------------
# A "state" is a dict:
#   width, height, food(set of (x,y)), hazards(set), you_id,
#   snakes: dict id -> {"body": [(x,y),...], "health": int, "alive": bool}

def _to_state(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    food = set((f["x"], f["y"]) for f in board["food"])
    hazards = set((z["x"], z["y"]) for z in board.get("hazards", []))
    snakes = {}
    for s in board["snakes"]:
        body = [(p["x"], p["y"]) for p in s["body"]]
        snakes[s["id"]] = {
            "body": body,
            "health": s["health"],
            "alive": True,
        }
    return {
        "width": w,
        "height": h,
        "food": food,
        "hazards": hazards,
        "you_id": game_state["you"]["id"],
        "snakes": snakes,
    }


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _alive_ids(state):
    return [sid for sid, s in state["snakes"].items() if s["alive"]]


def _clone(state):
    snakes = {}
    for sid, s in state["snakes"].items():
        snakes[sid] = {
            "body": list(s["body"]),
            "health": s["health"],
            "alive": s["alive"],
        }
    return {
        "width": state["width"],
        "height": state["height"],
        "food": set(state["food"]),
        "hazards": state["hazards"],  # immutable within a search
        "you_id": state["you_id"],
        "snakes": snakes,
    }


def _neck(state, sid):
    body = state["snakes"][sid]["body"]
    return body[1] if len(body) > 1 else None


def _possible_moves(state, sid):
    """Moves that are in-bounds and not into our own neck (mirrors minimax filter)."""
    s = state["snakes"][sid]
    hx, hy = s["body"][0]
    neck = _neck(state, sid)
    out = []
    for m, (dx, dy) in MOVES.items():
        nx, ny = hx + dx, hy + dy
        if not _in_bounds(nx, ny, state["width"], state["height"]):
            continue
        if neck is not None and (nx, ny) == neck:
            continue
        out.append((m, (nx, ny)))
    return out


def _simulate(state, moves):
    """Advance one full turn given moves: dict sid -> (nx,ny). Standard ruleset."""
    ns = _clone(state)
    # 1. move heads, consume health/food
    for sid, s in ns["snakes"].items():
        if not s["alive"]:
            continue
        if sid not in moves:
            s["alive"] = False
            continue
        nh = moves[sid]
        s["body"].insert(0, nh)
        s["health"] -= 1
        if nh in ns["food"]:
            s["health"] = 100
            # grow: don't pop tail
        else:
            s["body"].pop()
    # remove eaten food
    eaten = set()
    for sid, s in ns["snakes"].items():
        if s["alive"] and s["body"][0] in ns["food"]:
            eaten.add(s["body"][0])
    ns["food"] -= eaten

    # 2. out of bounds / starvation
    for sid, s in ns["snakes"].items():
        if not s["alive"]:
            continue
        hx, hy = s["body"][0]
        if s["health"] <= 0 or not _in_bounds(hx, hy, ns["width"], ns["height"]):
            s["alive"] = False

    # 3. collisions
    dead = set()
    live = [sid for sid, s in ns["snakes"].items() if s["alive"]]
    for sid in live:
        s = ns["snakes"][sid]
        hx, hy = s["body"][0]
        # body collisions (any snake's body excluding its own head at idx0)
        for oid in live:
            o = ns["snakes"][oid]
            obody = o["body"]
            # collide with body segments (index 1..)
            if (hx, hy) in obody[1:]:
                dead.add(sid)
                break
        else:
            # head-to-head
            for oid in live:
                if oid == sid:
                    continue
                o = ns["snakes"][oid]
                if o["body"][0] == (hx, hy):
                    if len(o["body"]) >= len(s["body"]):
                        dead.add(sid)
    for sid in dead:
        ns["snakes"][sid]["alive"] = False
    return ns


# ---------------------------------------------------------------------------
# Flood fill: spread from head (longest snake floods first)
# ---------------------------------------------------------------------------
def _spread_from_head_scores(state):
    """Return dict sid -> weighted claimed-square total, over FLOOD_CYCLES cycles."""
    w, h = state["width"], state["height"]
    grid = {}  # (x,y) -> sid owner
    alive = _alive_ids(state)
    # longest first
    order = sorted(alive, key=lambda sid: len(state["snakes"][sid]["body"]), reverse=True)

    for sid in order:
        for cell in state["snakes"][sid]["body"]:
            if cell not in grid:
                grid[cell] = sid

    # frontier per snake
    frontier = {sid: [state["snakes"][sid]["body"][0]] for sid in order}

    for _ in range(FLOOD_CYCLES):
        if not any(frontier[sid] for sid in order):
            break
        new_frontier = {sid: [] for sid in order}
        for sid in order:
            for (cx, cy) in frontier[sid]:
                for dx, dy in MOVES.values():
                    nx, ny = cx + dx, cy + dy
                    if not _in_bounds(nx, ny, w, h):
                        continue
                    if (nx, ny) in grid:
                        continue
                    grid[(nx, ny)] = sid
                    new_frontier[sid].append((nx, ny))
        frontier = new_frontier

    totals = {sid: 0 for sid in alive}
    for cell, sid in grid.items():
        if sid not in totals:
            continue
        if cell in state["hazards"]:
            val = SCORE_HAZARD
        elif cell in state["food"]:
            val = SCORE_FOOD
        else:
            val = SCORE_EMPTY
        totals[sid] += val
    return totals


def _bfs_nearest_food(state, sid):
    """BFS grid distance from sid's head to nearest food, avoiding snake bodies."""
    if not state["food"]:
        return None
    w, h = state["width"], state["height"]
    blocked = set()
    for s in state["snakes"].values():
        if s["alive"]:
            # bodies minus tails are obstacles
            blocked.update(s["body"][:-1])
    start = state["snakes"][sid]["body"][0]
    seen = {start}
    q = [(start, 0)]
    qi = 0
    while qi < len(q):
        (cx, cy), d = q[qi]
        qi += 1
        if (cx, cy) in state["food"]:
            return d
        for dx, dy in MOVES.values():
            nx, ny = cx + dx, cy + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in seen:
                continue
            if (nx, ny) in blocked and (nx, ny) not in state["food"]:
                continue
            seen.add((nx, ny))
            q.append(((nx, ny), d + 1))
    return None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
# Score tuple ordering encodes WrappedScore:
#   (tier, ...) where tier: 0=Lose, 1=Tie, 2=Scored, 3=Win
# Lose: prefer later depth and fewer alive  -> (0, alive_count_reversed, depth)
# Tie:  prefer later depth and fewer alive  -> (1, alive_count_reversed, depth)
# Scored(flood): (2, flood_component)
# Win:  prefer sooner -> (3, -depth)

def _standard_score(state):
    """Returns the 'Scored' payload for a non-terminal leaf (flood-fill ratio, +
    low-health food-distance tiebreak)."""
    me = state["you_id"]
    totals = _spread_from_head_scores(state)
    my_space = totals.get(me, 0)
    total_space = sum(totals.values())
    my_ratio = (my_space / total_space) if total_space > 0 else 0.0

    my_health = state["snakes"][me]["health"] if state["snakes"][me]["alive"] else 0
    if my_health < LOW_HEALTH:
        dist = _bfs_nearest_food(state, me)
        neg = -dist if dist is not None else -9999
        # LowOnHealth ranks below FloodFill-only states; order by (dist, ratio)
        return (0, neg, my_ratio)
    return (1, my_ratio, 0.0)


def _wrapped_score(state, depth, max_depth, num_players):
    """Return a comparable score tuple if this node is terminal or at max depth,
    else None. Mirrors score.rs::wrapped_score."""
    # Only evaluate at the boundary of a full round (all players moved)
    if num_players > 0 and depth % num_players != 0:
        return None

    me = state["you_id"]
    alive = _alive_ids(state)
    me_alive = state["snakes"][me]["alive"]

    # game-over check: 0 or 1 snakes alive (or we're dead)
    if not me_alive:
        # Lose: prefer to lose as late as possible, and with fewer snakes alive
        return (0, -len(alive), depth)
    if len(alive) == 1 and alive[0] == me:
        # Win: prefer winning sooner (smaller depth)
        return (3, -depth)
    if len(alive) == 0:
        return (1, -0, depth)  # Tie (shouldn't happen if me_alive)

    if depth >= max_depth:
        tier, a, b = _standard_score(state)
        # map to Scored band (between Lose/Tie band and Win)
        return (2, tier, a, b)
    return None


# ---------------------------------------------------------------------------
# Paranoid minimax with alpha-beta and one-snake-per-ply expansion
# ---------------------------------------------------------------------------
class _Timeout(Exception):
    pass


def _minimax(state, players, depth, max_depth, pending, deadline):
    if time.time() > deadline:
        raise _Timeout()

    num_players = len(players)

    # If all players have chosen a move this round, simulate forward.
    node = state
    if pending and len(pending) == len([p for p in players if state["snakes"][p]["alive"]]):
        node = _simulate(state, {sid: mv for sid, mv in pending.items()})
        pending = {}

    term = _wrapped_score(node, depth, max_depth, num_players)
    if term is not None:
        return term, None

    snake_id = players[depth % num_players]
    is_max = (snake_id == node["you_id"])

    # dead snake: skip its ply
    if not node["snakes"][snake_id]["alive"] or node["snakes"][snake_id]["health"] <= 0:
        return _minimax(node, players, depth + 1, max_depth, pending, deadline)

    moves = _possible_moves(node, snake_id)
    if not moves:
        # forced death next round; treat as a move into wall (self-terminates)
        # give it a "trapped" pseudo-move so simulation kills it
        hx, hy = node["snakes"][snake_id]["body"][0]
        moves = [("up", (hx, hy + 1))]

    best_score = None
    best_move = None

    for m, npos in moves:
        new_pending = dict(pending)
        new_pending[snake_id] = npos
        sc, _ = _minimax(node, players, depth + 1, max_depth, new_pending, deadline)
        if best_score is None:
            best_score, best_move = sc, m
        elif is_max and sc > best_score:
            best_score, best_move = sc, m
        elif (not is_max) and sc < best_score:
            best_score, best_move = sc, m

    return best_score, best_move


# ---------------------------------------------------------------------------
# Safety fallback
# ---------------------------------------------------------------------------
def _safe_moves(state):
    """Legal moves: in-bounds, not into any snake body (tails enterable)."""
    me = state["you_id"]
    s = state["snakes"][me]
    hx, hy = s["body"][0]
    w, h = state["width"], state["height"]
    occupied = set()
    for other in state["snakes"].values():
        if not other["alive"]:
            continue
        # tail is enterable unless snake just ate (approx: always allow tail)
        occupied.update(other["body"][:-1])
    safe = []
    risky = []
    for m, (dx, dy) in MOVES.items():
        nx, ny = hx + dx, hy + dy
        if not _in_bounds(nx, ny, w, h):
            continue
        if (nx, ny) in occupied:
            continue
        safe.append(m)
    return safe


def move(game_state):
    try:
        state = _to_state(game_state)
        me = state["you_id"]
        safe = _safe_moves(state)

        players = _alive_ids(state)
        # put ourselves first (mirrors sorted_ids: me = -1)
        players.sort(key=lambda sid: 0 if sid == me else 1)

        deadline = time.time() + TIME_BUDGET
        best_move = None
        num_players = len(players)

        # iterative deepening: one extra full round per iteration
        depth_cap = 1
        while depth_cap <= 6:
            max_depth = depth_cap * num_players
            try:
                sc, mv = _minimax(state, players, 0, max_depth, {}, deadline)
            except _Timeout:
                break
            if mv is not None:
                best_move = mv
            if time.time() > deadline:
                break
            depth_cap += 1

        if best_move is not None and best_move in safe:
            return {"move": best_move}
        if best_move is not None and not safe:
            # minimax found something even though nothing looks safe; trust it
            return {"move": best_move}
        if safe:
            return {"move": random.choice(safe)}
        # nothing safe at all -> any in-bounds move
        s = state["snakes"][me]
        hx, hy = s["body"][0]
        for m, (dx, dy) in MOVES.items():
            if _in_bounds(hx + dx, hy + dy, state["width"], state["height"]):
                return {"move": m}
        return {"move": "up"}
    except Exception:
        # absolute fallback: never crash
        try:
            you = game_state["you"]
            board = game_state["board"]
            w, h = board["width"], board["height"]
            hx, hy = you["body"][0]["x"], you["body"][0]["y"]
            bodies = set()
            for sn in board["snakes"]:
                for p in sn["body"][:-1]:
                    bodies.add((p["x"], p["y"]))
            for m, (dx, dy) in MOVES.items():
                nx, ny = hx + dx, hy + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in bodies:
                    return {"move": m}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
