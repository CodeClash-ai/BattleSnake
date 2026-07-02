"""Port of Team Sneaky Snake (hirethissnake/2017) to Battlesnake API v1.

Faithful reimplementation of the original weighted-grid + Dijkstra strategy.

The original built an igraph grid where every cell had a "weight" (50 default,
higher = more desirable) and used weighted shortest paths to steer toward the
highest-value reachable cell. It:
  * marks all snake bodies impassable (weight 0), leaving tails passable
    unless that snake can eat next turn (then tail stays blocked),
  * marks food as maximally desirable (weight 100),
  * boosts a 5x5 area around SMALLER enemy heads (+12) to hunt them,
  * blocks the cells around LARGER-or-equal enemy heads (avoid lethal
    head-to-head),
  * chooses the closest highest-weight reachable target and steps toward it,
  * refuses a first step that would trap it away from its own tail
    (enclosed-space avoidance), switching to a safe neighbour instead.

The original ran on the OLD API (top-left origin, y-down). This port remaps
everything to v1 (bottom-left origin, y-up). Internally we keep the original's
own convention where a "node" is [x, y] and edge weights come from the
destination cell, and we run a pure-Python Dijkstra to mirror igraph's
weighted shortest paths.
"""

import heapq

DEFAULT_WEIGHT = 50.0
FOOD_WEIGHT = 100.0
SMALL_SNAKE_BONUS = 12.0
INF = float("inf")


# ---------------------------------------------------------------------------
# Weighted grid (mirrors the original Board: weight = desirability, higher is
# better; a shortest-path cost for a cell is (100 - weight), and weight 0 is
# impassable).
# ---------------------------------------------------------------------------
class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # weight[x][y]; default 50
        self.weight = [[DEFAULT_WEIGHT for _ in range(height)] for _ in range(width)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def set_weight(self, x, y, w):
        if not self.in_bounds(x, y):
            return
        if w <= 0:
            w = 0.0
        elif w > 100:
            w = 100.0
        self.weight[x][y] = float(w)

    def add_weight(self, x, y, addend):
        if not self.in_bounds(x, y):
            return
        self.set_weight(x, y, self.weight[x][y] + addend)

    def get_weight(self, x, y):
        return self.weight[x][y]

    def cost(self, x, y):
        # In the original, edge weight into a node = (100 - desirability).
        # Impassable cells (weight 0) get cost +inf.
        w = self.weight[x][y]
        if w <= 0:
            return INF
        return 100.0 - w

    def neighbors(self, x, y):
        out = []
        if self.in_bounds(x - 1, y):
            out.append((x - 1, y))
        if self.in_bounds(x + 1, y):
            out.append((x + 1, y))
        if self.in_bounds(x, y + 1):
            out.append((x, y + 1))
        if self.in_bounds(x, y - 1):
            out.append((x, y - 1))
        return out

    def dijkstra(self, start):
        """Return (dist, prev) dicts from start over passable cells.

        Cost to enter a cell is that cell's cost(). The start cell itself is
        free. Impassable (inf-cost) cells are never entered.
        """
        sx, sy = start
        dist = {(sx, sy): 0.0}
        prev = {}
        pq = [(0.0, sx, sy)]
        while pq:
            d, x, y = heapq.heappop(pq)
            if d > dist.get((x, y), INF):
                continue
            for nx, ny in self.neighbors(x, y):
                c = self.cost(nx, ny)
                if c == INF:
                    continue
                nd = d + c
                if nd < dist.get((nx, ny), INF):
                    dist[(nx, ny)] = nd
                    prev[(nx, ny)] = (x, y)
                    heapq.heappush(pq, (nd, nx, ny))
        return dist, prev

    def path(self, start, goal, dist, prev):
        """Reconstruct node path [start, ..., goal] or [] if unreachable."""
        if goal == start:
            return [start]
        if goal not in dist:
            return []
        node = goal
        rev = [node]
        while node != start:
            node = prev.get(node)
            if node is None:
                return []
            rev.append(node)
        rev.reverse()
        return rev


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------
def _cells(snake):
    return [(seg["x"], seg["y"]) for seg in snake["body"]]


def _head(snake):
    h = snake["body"][0]
    return (h["x"], h["y"])


def _decide(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    my_id = you["id"]
    my_head = _head(you)
    my_len = len(you["body"])

    snakes = board["snakes"]
    food = set((f["x"], f["y"]) for f in board["food"])

    grid = Grid(width, height)

    # --- weightNotHitSnakes: bodies impassable, tail passable unless the
    #     snake can eat food next turn. ---
    for snake in snakes:
        cells = _cells(snake)
        if not cells:
            continue
        hx, hy = cells[0]
        tail = cells[-1]
        for (cx, cy) in cells:
            grid.set_weight(cx, cy, 0.0)
        grid.set_weight(tail[0], tail[1], DEFAULT_WEIGHT)
        # If this snake could grab food next turn, its tail will not move.
        adj = [(hx, hy + 1), (hx, hy - 1), (hx + 1, hy), (hx - 1, hy)]
        if any(a in food for a in adj):
            grid.set_weight(tail[0], tail[1], 0.0)

    # --- weightFood: food is maximally desirable. ---
    for (fx, fy) in food:
        grid.set_weight(fx, fy, FOOD_WEIGHT)

    # --- weightSmallSnakes: hunt snakes smaller than us. ---
    all_body_cells = set()
    for snake in snakes:
        for c in _cells(snake):
            all_body_cells.add(c)

    for snake in snakes:
        if snake["id"] == my_id:
            continue
        if len(snake["body"]) < my_len:
            hx, hy = _head(snake)
            for ax in range(max(0, hx - 2), min(width - 1, hx + 2) + 1):
                for ay in range(max(0, hy - 2), min(height - 1, hy + 2) + 1):
                    if (ax, ay) in all_body_cells:
                        continue
                    grid.add_weight(ax, ay, SMALL_SNAKE_BONUS)

    # --- weightLargeSnakes: block cells around larger-or-equal enemy heads. ---
    for snake in snakes:
        if snake["id"] == my_id:
            continue
        if len(snake["body"]) >= my_len:
            hx, hy = _head(snake)
            for (nx, ny) in [(hx + 1, hy), (hx - 1, hy), (hx, hy + 1), (hx, hy - 1)]:
                if grid.in_bounds(nx, ny):
                    grid.set_weight(nx, ny, 0.0)

    # Our head cell must be passable as a start for Dijkstra.
    saved_head_w = grid.get_weight(my_head[0], my_head[1])
    grid.set_weight(my_head[0], my_head[1], DEFAULT_WEIGHT)

    dist, prev = grid.dijkstra(my_head)

    # --- Choose target: highest-weight reachable cell; ties -> closest. ---
    # Build list of (weight, node) for reachable cells other than head.
    best_target = None
    best_weight = -1.0
    best_len = None
    for (x, y), d in dist.items():
        if (x, y) == my_head:
            continue
        w = grid.get_weight(x, y)
        if w <= 0:
            continue
        plen = len(grid.path(my_head, (x, y), dist, prev))
        if w > best_weight or (w == best_weight and (best_len is None or plen < best_len)):
            best_weight = w
            best_target = (x, y)
            best_len = plen

    grid.set_weight(my_head[0], my_head[1], saved_head_w)

    # --- Determine the first step. ---
    first_step = _first_step_with_enclosure_check(
        grid, snakes, my_id, my_head, you, best_target, dist, prev
    )

    if first_step is None:
        return None
    return _to_direction(my_head, first_step)


def _first_step_with_enclosure_check(grid, snakes, my_id, my_head, you,
                                     target, dist, prev):
    """Mirror weightEnclosedSpaces: step toward target unless doing so traps
    us away from our own tail; then pick a safe alternate neighbour."""
    if target is None:
        return _fallback_step(grid, my_head, you)

    path = grid.path(my_head, target, dist, prev)
    if len(path) < 2:
        return _fallback_step(grid, my_head, you)
    intended = path[1]

    # Make our tail passable (weight 1) and check target->tail reachability.
    tail = _cells(you)[-1]
    saved_tail = grid.get_weight(tail[0], tail[1])
    grid.set_weight(tail[0], tail[1], 1.0)
    t_dist, _ = grid.dijkstra(target)
    reaches_tail = (tail in t_dist)

    if reaches_tail:
        grid.set_weight(tail[0], tail[1], saved_tail)
        return intended

    # Block all possible next moves of other snakes, then evaluate whether
    # our alternate neighbours can still reach the target.
    saved = {}
    for snake in snakes:
        if snake["id"] == my_id:
            continue
        hx, hy = _head(snake)
        for (nx, ny) in [(hx - 1, hy), (hx + 1, hy), (hx, hy + 1), (hx, hy - 1)]:
            if grid.in_bounds(nx, ny) and (nx, ny) not in saved:
                saved[(nx, ny)] = grid.get_weight(nx, ny)
                grid.set_weight(nx, ny, 0.0)

    # Our candidate neighbours excluding the intended step and our neck.
    hx, hy = my_head
    options = []
    for (nx, ny) in [(hx - 1, hy), (hx + 1, hy), (hx, hy + 1), (hx, hy - 1)]:
        if grid.in_bounds(nx, ny):
            options.append((nx, ny))
    if intended in options:
        options.remove(intended)
    neck = _cells(you)[1] if len(you["body"]) > 1 else None
    if neck in options:
        options.remove(neck)
    options = [o for o in options if grid.get_weight(o[0], o[1]) > 0]

    # If any alternate option cannot reach the target, the intended path is
    # deemed dangerous -> switch to the first safe alternate.
    dont = False
    for opt in options:
        o_dist, _ = grid.dijkstra(opt)
        if target not in o_dist:
            dont = True
            break

    # restore
    for (nx, ny), w in saved.items():
        grid.set_weight(nx, ny, w)
    grid.set_weight(tail[0], tail[1], saved_tail)

    if dont and options:
        return options[0]
    return intended


def _fallback_step(grid, my_head, you):
    """Pick any legal neighbour (in-bounds, passable). Prefer non-neck."""
    hx, hy = my_head
    neck = _cells(you)[1] if len(you["body"]) > 1 else None
    candidates = [(hx, hy + 1), (hx, hy - 1), (hx - 1, hy), (hx + 1, hy)]
    best = None
    for (nx, ny) in candidates:
        if not grid.in_bounds(nx, ny):
            continue
        if (nx, ny) == neck:
            continue
        if grid.get_weight(nx, ny) > 0:
            return (nx, ny)
        if best is None:
            best = (nx, ny)
    return best


def _to_direction(head, node):
    """Convert an adjacent node to a v1 direction (bottom-left origin, y-up)."""
    hx, hy = head
    nx, ny = node
    if nx == hx + 1:
        return "right"
    if nx == hx - 1:
        return "left"
    if ny == hy + 1:
        return "up"
    if ny == hy - 1:
        return "down"
    return None


# ---------------------------------------------------------------------------
# Absolute-safety fallback: guarantee a legal move no matter what.
# ---------------------------------------------------------------------------
def _safe_move(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    you = game_state["you"]
    hx, hy = _head(you)

    blocked = set()
    for snake in board["snakes"]:
        cells = _cells(snake)
        for c in cells[:-1]:  # tail may move
            blocked.add(c)

    options = {
        "up": (hx, hy + 1),
        "down": (hx, hy - 1),
        "left": (hx - 1, hy),
        "right": (hx + 1, hy),
    }
    for d, (nx, ny) in options.items():
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
            return d
    # No safe move; anything in-bounds beats forfeiting less, but must return.
    for d, (nx, ny) in options.items():
        if 0 <= nx < width and 0 <= ny < height:
            return d
    return "up"


# ---------------------------------------------------------------------------
# Battlesnake API v1 handlers
# ---------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "hirethissnake",
        "color": "#FFEBD0",
        "head": "tongue",
        "tail": "curled",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        direction = _decide(game_state)
        if direction in ("up", "down", "left", "right"):
            # Verify it is actually legal; if not, fall through to safe move.
            you = game_state["you"]
            board = game_state["board"]
            hx, hy = _head(you)
            delta = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}[direction]
            nx, ny = hx + delta[0], hy + delta[1]
            if 0 <= nx < board["width"] and 0 <= ny < board["height"]:
                blocked = set()
                for snake in board["snakes"]:
                    for c in _cells(snake)[:-1]:
                        blocked.add(c)
                if (nx, ny) not in blocked:
                    return {"move": direction}
        return {"move": _safe_move(game_state)}
    except Exception:
        try:
            return {"move": _safe_move(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
