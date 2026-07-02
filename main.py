"""Port of nbw/battlesnake_crystal (Crystal) to v1 Battlesnake API.

Strategy (faithful to original):
  World.calculate:
    - ConnectedComponents.survival_mode? -> if my snake is isolated in its own
      connected area (no enemy heads adjacent to the same area, or solo game),
      use SurvivalSnake (pick open direction with fewest open edges).
    - Otherwise use VoronoiAnalyzer: build a Voronoi flood grid from all snake
      heads, enumerate paths of depth SEARCH_DEGREE (default 3) from my head,
      simulate each with FutureVoronoi, and choose the path maximizing my area.

Coordinate remap: the original used top-left origin with y growing DOWN
(UP={0,-1}, DOWN={0,1}). v1 uses bottom-left with y growing UP. To reuse the
original logic (including its direction labels) verbatim, we flip y on input:
    y_internal = height - 1 - y_v1
so UP/DOWN labels emitted by the original code remain correct in v1.
"""

import sys

EMPTY = "empty"
FOOD = "food"
SNAKE = "snake"
SNAKE_HEAD = "snake_head"

# Original direction constants (top-left / y-down internal grid)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = [LEFT, UP, RIGHT, DOWN]


class GridPoint:
    __slots__ = ("x", "y", "content", "content_id")

    def __init__(self, content=EMPTY, content_id=-1):
        self.content = content
        self.content_id = content_id
        self.x = 0
        self.y = 0

    def set_coord(self, x, y):
        self.x = x
        self.y = y

    def snake(self):
        return self.content in (SNAKE, SNAKE_HEAD)

    def snake_head(self):
        return self.content == SNAKE_HEAD


class Grid:
    def __init__(self, gs):
        board = gs["board"]
        self.width = board["width"]
        self.height = board["height"]
        self._h = self.height

        # Flip y so internal grid is top-left / y-down like the original.
        def fy(y):
            return self._h - 1 - y

        self.food = [(p["x"], fy(p["y"])) for p in board["food"]]

        me_id = gs["you"]["id"]
        self.snakes = []          # list of dicts: id, body[(x,y)]
        self._my_index = 0
        for i, s in enumerate(board["snakes"]):
            body = [(p["x"], fy(p["y"])) for p in s["body"]]
            self.snakes.append({"id": s["id"], "body": body})
            if s["id"] == me_id:
                self._my_index = i

        self.grid = [GridPoint() for _ in range(self.width * self.height)]
        self._generate()

    def get_point(self, x, y):
        return self.grid[int(x + y * self.width)]

    def _generate(self):
        # coords
        for index, gp in enumerate(self.grid):
            xi = index % self.width
            yi = index // self.width
            self.get_point(xi, yi).set_coord(xi, yi)
        # food
        for i, (x, y) in enumerate(self.food):
            p = self.get_point(x, y)
            p.content = FOOD
            p.content_id = i
        # snakes
        for i, snake in enumerate(self.snakes):
            # unique parts (dedupe, preserve order)
            seen = set()
            body = []
            for pt in snake["body"]:
                if pt not in seen:
                    seen.add(pt)
                    body.append(pt)
            for (x, y) in body:
                gp = self.get_point(x, y)
                gp.content = SNAKE
                gp.content_id = i
            hx, hy = body[0]
            self.get_point(hx, hy).content = SNAKE_HEAD

    def empty_point(self, x, y):
        if x < 0 or x > self.width - 1:
            return False
        if y < 0 or y > self.height - 1:
            return False
        c = self.get_point(x, y).content
        if c in (SNAKE, SNAKE_HEAD):
            return False
        return True

    def snake_head_p(self, point):
        return point.snake_head()

    def snake_body_p(self, point):
        return point.snake()

    @property
    def my_snake_head(self):
        hx, hy = self.snakes[self._my_index]["body"][0]
        return self.get_point(hx, hy)

    @property
    def my_snake_index(self):
        return self._my_index


# ---------------------------------------------------------------------------
# Connected Components
# ---------------------------------------------------------------------------
class ConnCompPoint:
    __slots__ = ("value", "label", "gp")

    def __init__(self, gp):
        self.value = 0
        self.label = 0
        self.gp = gp

    @property
    def x(self):
        return self.gp.x

    @property
    def y(self):
        return self.gp.y


class ConnectedComponents:
    def __init__(self, grid_obj):
        self._g = grid_obj
        self.width = grid_obj.width
        self.height = grid_obj.height
        self._label_count = 0
        self._merge_ledger = []
        self._cc = [ConnCompPoint(gp) for gp in grid_obj.grid]

    def get_point(self, x, y):
        return self._cc[int(x + y * self.width)]

    def process(self):
        self._first_pass()
        self._second_pass()
        self._merge()

    def survival_mode(self):
        snakes = self._g.snakes
        if len(snakes) <= 1:
            return True

        my_adj = self._adjacent_empty_labels(self._g.my_snake_head)

        if len(my_adj) <= 1:
            enemy_snakes = [s for i, s in enumerate(snakes)
                            if i != self._g.my_snake_index]
            enemy_components = []
            for snake in enemy_snakes:
                hx, hy = snake["body"][0]
                head = self._g.get_point(hx, hy)
                for lbl in self._adjacent_empty_labels(head):
                    if lbl not in enemy_components:
                        enemy_components.append(lbl)
            if not my_adj:
                # No open space adjacent to my head; treat as survival.
                return True
            my_area = my_adj[0]
            return my_area not in enemy_components
        else:
            return False

    def _adjacent_empty_labels(self, point):
        labels = []
        for dx, dy in DIRECTIONS:
            x = point.x + dx
            y = point.y + dy
            if self._g.empty_point(x, y):
                lbl = self.get_point(x, y).label
                if lbl not in labels:
                    labels.append(lbl)
        return labels

    def _first_pass(self):
        for index, point in enumerate(self._g.grid):
            if point.snake():
                self._cc[index].value = 1

    def _second_pass(self):
        for point in self._cc:
            self._analyze_point(point)

    def _merge(self):
        for relation in self._merge_ledger:
            relation = sorted(relation)
            mn = relation[0]
            for r in relation[1:]:
                for p in self._cc:
                    if p.label == r:
                        p.label = mn

    def _one_dir_check(self, point, dr):
        side = self._point_at(point, dr)
        if side.value == point.value:
            point.label = side.label
        else:
            self._label_count += 1
            point.label = self._label_count

    def _two_dir_check(self, point):
        left = self._point_at(point, LEFT)
        up = self._point_at(point, UP)
        if (left.value == point.value and up.value == point.value
                and up.label != left.label):
            self._merge_ledger.append([left.label, up.label])
            point.label = min(left.label, up.label)
        elif left.value == point.value:
            point.label = left.label
        elif left.value != point.value and up.value == point.value:
            point.label = up.label
        elif left.value != point.value and up.value != point.value:
            self._label_count += 1
            point.label = self._label_count

    def _analyze_point(self, point):
        top_row = (point.y == 0)
        first_column = (point.x == 0)
        if top_row:
            self._one_dir_check(point, LEFT)
        elif first_column:
            self._one_dir_check(point, UP)
        else:
            self._two_dir_check(point)

    def _point_at(self, p, dr):
        return self.get_point(p.x + dr[0], p.y + dr[1])


# ---------------------------------------------------------------------------
# Survival Snake
# ---------------------------------------------------------------------------
class SurvivalSnake:
    # order matters (original DIRECTIONS = [LEFT, UP, RIGHT, DOWN])
    def __init__(self, grid_obj):
        self._g = grid_obj

    @property
    def my_snake_head(self):
        return self._g.my_snake_head

    def process(self):
        open_dir = self._collect_open_directions()
        if not open_dir:
            return "left"
        min_edges = min(self._num_open_edges(d) for d in open_dir)
        candidate = [d for d in open_dir
                     if self._num_open_edges(d) == min_edges]
        if LEFT in candidate:
            return "left"
        if UP in candidate:
            return "up"
        if RIGHT in candidate:
            return "right"
        if DOWN in candidate:
            return "down"
        return "left"

    def _collect_open_directions(self):
        head = self.my_snake_head
        dirs = []
        for dx, dy in DIRECTIONS:
            if self._g.empty_point(head.x + dx, head.y + dy):
                dirs.append((dx, dy))
        return dirs

    def _num_open_edges(self, d):
        head = self.my_snake_head
        px = head.x + d[0]
        py = head.y + d[1]
        count = 0
        for dx, dy in DIRECTIONS:
            if self._g.empty_point(px + dx, py + dy):
                count += 1
        return count


# ---------------------------------------------------------------------------
# Voronoi
# ---------------------------------------------------------------------------
INTERSECTION = -1
NOT_OWNED = -2


class VoronoiPoint:
    __slots__ = ("point", "status", "steps", "intersection", "owner_id")

    def __init__(self, gp, status=""):
        self.point = gp
        self.status = status
        self.steps = 0
        self.intersection = False
        cid = gp.content_id
        self.owner_id = cid if cid >= 0 else NOT_OWNED

    @property
    def x(self):
        return self.point.x

    @property
    def y(self):
        return self.point.y

    def mark_visited(self, steps, owner_id):
        self.status = "visited"
        self.owner_id = owner_id
        self.steps = steps

    def visited(self):
        return self.status == "visited"

    def unvisited(self):
        return self.status != "visited"

    def clone(self):
        vp = VoronoiPoint.__new__(VoronoiPoint)
        vp.point = self.point
        vp.status = self.status
        vp.steps = self.steps
        vp.intersection = self.intersection
        vp.owner_id = self.owner_id
        return vp


class Voronoi:
    def __init__(self, grid_obj):
        self.grid_obj = grid_obj
        self.width = grid_obj.width
        self.height = grid_obj.height
        self.vor_grid = []
        self._snake_heads = []
        self._make_grid()

    def get_point(self, x, y):
        return self.vor_grid[int(x + y * self.width)]

    # overridable hooks
    def empty_point(self, x, y):
        return self.grid_obj.empty_point(x, y)

    def snake_head_p(self, point):
        return self.grid_obj.snake_head_p(point)

    def snake_body_p(self, point):
        return self.grid_obj.snake_body_p(point)

    def process(self):
        self._flood_grid()

    def tally_my_section(self):
        return self._area_of_owner(self.grid_obj.my_snake_index)

    @property
    def my_voronoi_snake_head(self):
        head = self.grid_obj.my_snake_head
        return self.get_point(head.x, head.y)

    def _make_grid(self):
        for gp in self.grid_obj.grid:
            vp = VoronoiPoint(gp)
            if self.snake_head_p(gp):
                vp.owner_id = gp.content_id
                self._snake_heads.append(vp)
            self.vor_grid.append(vp)

    def _flood_grid(self):
        points = self._snake_heads
        while any(self._has_unvisited_neighbours(p) for p in points):
            new_points = []
            for p in points:
                new_points.extend(self._flood_point(p))
            points = new_points
            if not points:
                break

    def _flood_point(self, point):
        new_points = []
        for dx, dy in DIRECTIONS:
            x = point.x + dx
            y = point.y + dy
            if self.empty_point(x, y):
                possible = self.get_point(x, y)
                new_step = point.steps + 1
                if (possible.visited()
                        and possible.owner_id != point.owner_id
                        and possible.steps == new_step):
                    possible.intersection = True
                    possible.owner_id = INTERSECTION
                elif not possible.visited():
                    possible.mark_visited(new_step, point.owner_id)
                    new_points.append(possible)
        return new_points

    def _has_unvisited_neighbours(self, point):
        for dx, dy in DIRECTIONS:
            x = point.x + dx
            y = point.y + dy
            if self.empty_point(x, y) and self.get_point(x, y).unvisited():
                return True
        return False

    def _area_of_owner(self, owner_id):
        return sum(1 for p in self.vor_grid if p.owner_id == owner_id)


class FutureVoronoi(Voronoi):
    def __init__(self, grid_obj, path):
        self._path = path
        self._path_points = set((p.x, p.y) for p in path)
        super().__init__(grid_obj)

    @property
    def my_snake_index(self):
        return self.grid_obj.my_snake_index

    def empty_point(self, x, y):
        return (not self._is_path_point(x, y)
                and self.grid_obj.empty_point(x, y))

    def snake_head_p(self, point):
        if point.content_id == self.my_snake_index:
            head = self._path[-1]
            return head.x == point.x and head.y == point.y
        return self.grid_obj.snake_head_p(point)

    def snake_body_p(self, point):
        if point.content_id == self.my_snake_index:
            return (self._is_path_point(point.x, point.y)
                    or self.grid_obj.snake_body_p(point))
        return self.grid_obj.snake_body_p(point)

    def _is_path_point(self, x, y):
        return (x, y) in self._path_points


# ---------------------------------------------------------------------------
# Voronoi Analyzer
# ---------------------------------------------------------------------------
class VoronoiAnalyzer:
    def __init__(self, grid_obj):
        self._grid = Voronoi(grid_obj)

    def process(self):
        self._grid.process()
        search_degree = 3
        paths = self._build_my_paths(search_degree)

        def score(path):
            fv = FutureVoronoi(self._grid.grid_obj, path)
            fv.process()
            return fv.tally_my_section()

        ordered = sorted(paths, key=score)
        return self._direction_to_path(ordered[-1])

    def _direction_to_path(self, path):
        if len(path) < 2:
            return "up"
        point = path[1]
        head = self._grid.my_voronoi_snake_head
        if point.x > head.x:
            return "right"
        elif point.x < head.x:
            return "left"
        elif point.y > head.y:
            return "down"
        else:
            return "up"

    def _build_my_paths(self, degree):
        paths = [[self._grid.my_voronoi_snake_head]]
        count = 0
        while count < degree:
            new_paths = []
            for path in paths:
                path_head = path[-1]
                surr = self._surrounding_points(path_head, count + 1)
                for new_point in surr:
                    p = list(path)
                    np = new_point.clone()
                    np.owner_id = p[0].owner_id
                    np.point.content_id = p[0].owner_id
                    p.append(np)
                    new_paths.append(p)
            count += 1
            paths = new_paths
            if not paths:
                # keep last non-empty set
                paths = [[self._grid.my_voronoi_snake_head]]
                break
        return paths

    def _surrounding_points(self, point, value):
        out = []
        for dx, dy in DIRECTIONS:
            x = point.x + dx
            y = point.y + dy
            if self._grid.empty_point(x, y) and self._grid.get_point(x, y).steps == value:
                out.append(self._grid.get_point(x, y))
        return out


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, gs):
        self._grid = Grid(gs)

    def calculate(self):
        if self._survival_mode():
            return SurvivalSnake(self._grid).process()
        else:
            return VoronoiAnalyzer(self._grid).process()

    def _survival_mode(self):
        cc = ConnectedComponents(self._grid)
        cc.process()
        return cc.survival_mode()


# ---------------------------------------------------------------------------
# v1 API glue + robust fallback
# ---------------------------------------------------------------------------
def _safe_fallback(game_state):
    """Return any in-bounds move not into a snake body (tails enterable)."""
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    occupied = set()
    for s in board["snakes"]:
        body = s["body"]
        for i, seg in enumerate(body):
            # tail is enterable unless the snake just ate (health==100 keeps tail)
            if i == len(body) - 1 and s.get("health", 0) < 100:
                continue
            occupied.add((seg["x"], seg["y"]))

    moves = {"up": (hx, hy + 1), "down": (hx, hy - 1),
             "left": (hx - 1, hy), "right": (hx + 1, hy)}
    for name, (nx, ny) in moves.items():
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
            return name
    return "up"


def info():
    return {
        "apiversion": "1",
        "author": "nbw",
        "color": "#54a4a4",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        direction = World(game_state).calculate()
        if direction not in ("up", "down", "left", "right"):
            direction = _safe_fallback(game_state)
        else:
            # Validate: ensure the chosen move is legal; else fall back.
            board = game_state["board"]
            w, h = board["width"], board["height"]
            head = game_state["you"]["body"][0]
            hx, hy = head["x"], head["y"]
            delta = {"up": (0, 1), "down": (0, -1),
                     "left": (-1, 0), "right": (1, 0)}[direction]
            nx, ny = hx + delta[0], hy + delta[1]
            occupied = set()
            for s in board["snakes"]:
                body = s["body"]
                for i, seg in enumerate(body):
                    if i == len(body) - 1 and s.get("health", 0) < 100:
                        continue
                    occupied.add((seg["x"], seg["y"]))
            if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) in occupied:
                direction = _safe_fallback(game_state)
        return {"move": direction}
    except Exception:
        try:
            return {"move": _safe_fallback(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        test = {"turn": 10, "board": {"width": 11, "height": 11,
                "food": [{"x": 2, "y": 8}, {"x": 5, "y": 5}], "hazards": [],
                "snakes": [
                    {"id": "me", "name": "me", "health": 80,
                     "body": [{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 3}],
                     "head": {"x": 5, "y": 5}, "length": 3},
                    {"id": "foe", "name": "foe", "health": 75,
                     "body": [{"x": 8, "y": 8}, {"x": 8, "y": 7}],
                     "head": {"x": 8, "y": 8}, "length": 2}]},
                "you": {"id": "me", "name": "me", "health": 80,
                        "body": [{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 3}],
                        "head": {"x": 5, "y": 5}, "length": 3}}
        r = move(test)
        assert r["move"] in ("up", "down", "left", "right"), r
        # legality check
        hx, hy = 5, 5
        d = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}[r["move"]]
        nx, ny = hx + d[0], hy + d[1]
        assert 0 <= nx < 11 and 0 <= ny < 11, r
        assert (nx, ny) not in {(5, 4), (5, 3), (8, 8), (8, 7)}, r
        print("SELFTEST pass:", r)
    else:
        from server import run_server
        run_server({"info": info, "start": start, "move": move, "end": end})
