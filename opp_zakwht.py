"""
Port of zakwht/battlesnake-2018 (Java, 2018) to the Battlesnake v1 API.

Original strategy (ca.casualt.battlesnake.game.Board / SmartSnake):
  - Build a grid marking snake bodies as walls, food as food.
  - If we are NOT longer than an enemy snake, mark the 4 cells adjacent to
    that enemy's head as walls too (avoid losing/tying head-to-head).
  - Choose a mode:
        health <= 50           -> HUNGRY
        longer than all others -> ATTACK
        otherwise              -> HUNGRY (Java falls through to HUNGRY)
  - Move priority by mode (each a BFS returning the FIRST step of the
    shortest path to any goal cell):
        HUNGRY: goToFood -> goToAttack -> goToTail
        ATTACK: goToAttack -> goToFood -> goToTail
  - goToFood:   BFS to nearest food cell.
  - goToAttack: BFS to any enemy head or a cell adjacent to an enemy head.
  - goToTail:   BFS to a cell adjacent to one of our own body segments,
                scanning from tail inward.
  - Fallback when no path found: Move.left (unconditionally).

The 2018 code used a top-left origin with y increasing downward. The v1 API
uses a bottom-left origin with y increasing upward. Since all pathfinding here
is symmetric in geometry, we implement the BFS directly in v1 coordinates; the
only place orientation matters is the literal "left" fallback, which is the
same in both systems (x - 1).
"""

from collections import deque


def info():
    return {
        "apiversion": "1",
        "author": "zakwht",
        "color": "#f2c55c",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---------------------------------------------------------------------------
# Geometry helpers (v1 coordinates: bottom-left origin, up = y+1)
# ---------------------------------------------------------------------------

# Ordered up, down, left, right (matches getPossibleMoves ordering in Board.java)
_DIRS = [
    ("up", 0, 1),
    ("down", 0, -1),
    ("left", -1, 0),
    ("right", 1, 0),
]


def _adjacent(x, y):
    # Matches Board.findAdjacent: left, right, down, up
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def move(game_state):
    try:
        return {"move": _decide(game_state)}
    except Exception:
        # Arena legal fallback only (never crash). Mirrors Java Move.left.
        return {"move": "left"}


def _decide(game_state):
    board = game_state["board"]
    w = board["width"]
    h = board["height"]
    you = game_state["you"]
    my_body = [(p["x"], p["y"]) for p in you["body"]]
    head = my_body[0]
    my_len = you.get("length", len(my_body))
    my_health = you.get("health", 100)

    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board["food"]]

    # --- toGrid: build the set of blocked (WALL/head) cells -----------------
    # A cell is "filled" (impassable to BFS) if it is a snake body segment,
    # an enemy head, or adjacent to an enemy head we are not longer than.
    blocked = set()
    enemy_heads = []
    longest_other = None

    my_id = you["id"]
    for snake in snakes:
        body = [(p["x"], p["y"]) for p in snake["body"]]
        for seg in body:
            blocked.add(seg)
        sid = snake["id"]
        s_len = snake.get("length", len(body))
        if sid == my_id:
            continue
        # track longest other snake
        if longest_other is None or s_len > longest_other:
            longest_other = s_len
        h_pt = body[0]
        enemy_heads.append(h_pt)
        # If we are NOT longer than this snake, fence off around its head.
        if not (my_len > s_len):
            for ax, ay in _adjacent(*h_pt):
                if _in_bounds(ax, ay, w, h):
                    blocked.add((ax, ay))

    def is_filled(x, y):
        if not _in_bounds(x, y, w, h):
            return True
        # Food is passable (in Java, FOOD counts as not-filled).
        return (x, y) in blocked

    # --- mode selection -----------------------------------------------------
    # Java: health<=50 -> HUNGRY; length > longestSnakeLength() -> ATTACK;
    # else HUNGRY. When there is no other snake, longestSnakeLength() returns
    # Integer.MIN_VALUE, so ATTACK is chosen; with no enemy heads goToAttack
    # yields nothing, so the effective priority is identical to HUNGRY. We
    # keep the observable behaviour by defaulting to HUNGRY in that case.
    HUNGER_ZONE = 50
    if my_health <= HUNGER_ZONE:
        mode = "HUNGRY"
    elif longest_other is not None and my_len > longest_other:
        mode = "ATTACK"
    else:
        mode = "HUNGRY"

    # --- BFS returning the first step of the shortest path to any goal ------
    def find_path(goals):
        goal_set = set(g for g in goals if g != head and _in_bounds(g[0], g[1], w, h))
        if not goal_set:
            return None
        # BFS from head. Frontier holds (point, initial_move).
        visited = {head}
        queue = deque()
        # seed with immediate neighbours (assigning their own initial move)
        for name, dx, dy in _DIRS:
            nx, ny = head[0] + dx, head[1] + dy
            if is_filled(nx, ny):
                continue
            if (nx, ny) in visited:
                continue
            visited.add((nx, ny))
            queue.append(((nx, ny), name))
        while queue:
            (px, py), initial = queue.popleft()
            if (px, py) in goal_set:
                return initial
            for name, dx, dy in _DIRS:
                nx, ny = px + dx, py + dy
                if is_filled(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                queue.append(((nx, ny), initial))
        return None

    def go_to_food():
        return find_path(food)

    def go_to_attack():
        goals = []
        for hp in enemy_heads:
            goals.extend(_adjacent(*hp))
            goals.append(hp)
        return find_path(goals)

    def go_to_tail():
        # Scan our body from tail inward; target cells adjacent to each segment.
        for i in range(len(my_body) - 1, 0, -1):
            seg = my_body[i]
            m = find_path(_adjacent(*seg))
            if m is not None:
                return m
        return None

    chosen = None
    if mode == "HUNGRY":
        chosen = go_to_food()
        if chosen is None:
            chosen = go_to_attack()
        if chosen is None:
            chosen = go_to_tail()
    elif mode == "ATTACK":
        chosen = go_to_attack()
        if chosen is None:
            chosen = go_to_food()
        if chosen is None:
            chosen = go_to_tail()

    # Java: if (move == null) move = Move.left;  (unconditional)
    if chosen is None:
        chosen = "left"

    return chosen


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
