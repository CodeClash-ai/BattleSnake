"""
CodeClash port of nbw's 2017 Battlesnake bot ("Ereptile Disruption").
Original: https://github.com/nbw/battlesnake (Ruby, 2017).

Strategy (faithfully reproduced from the Ruby source):
  1. Grid    : build a width x height array (area[x][y]); snakes -> blocked
               cells (non-numeric markers), food -> -1.
  2. Painter : "paint" weighted danger/attraction values onto the grid:
               walls, snakes (head/body radiating vectors incl. diagonals,
               enemy scaled by a length weight), food (health-scaled,
               radiating vectors). Lower values are more attractive.
  3. Tree    : recursively build all non-self-overlapping paths up to
               LEVELS deep from the head; each node carries its cell value
               and the running sum of values along the path.
  4. Squirrel: BFD ("breadth-first"-ish) traversal that keeps the best
               fraction of nodes per level and picks the lowest-sum path,
               returning the first direction of that path.

COORDINATE SYSTEM:
  The 2017 bot uses the OLD API: origin top-left, y increases DOWNWARD
  (up = y-1, down = y+1). The current v1 API uses origin bottom-left,
  y increases UPWARD (up = y+1, down = y-1).
  We remap by FLIPPING y on input (old_y = height-1 - v1_y). After that
  flip, the "up"/"down"/"left"/"right" direction strings map identically
  between the two systems, so the ported algorithm and its returned
  direction need no further changes.
"""

import math

# ---------------------------------------------------------------------------
# Config constants (from config/settings_dev.yml, the tuned values used)
# ---------------------------------------------------------------------------
WALL_DEGREE = 7
WALL_WEIGHT = 1

TREE_LEVELS = 5
TREE_MIN_THRESHOLD = 0.5
TREE_THRESHOLD = 0.6

SNAKE_ME_BODY_DEGREE = 2
SNAKE_ME_BODY_WEIGHT = 1
SNAKE_ME_HEAD_DEGREE = 2
SNAKE_ME_HEAD_WEIGHT = -1

SNAKE_ENEMY_BODY_DEGREE = 5
SNAKE_ENEMY_BODY_WEIGHT = 1
SNAKE_ENEMY_HEAD_DEGREE = 10
SNAKE_ENEMY_HEAD_WEIGHT = 2
SNAKE_ENEMY_LENGTH_WEIGHT = 0.6

FOOD_MULT = 2
FOOD_WEIGHT = -2
FOOD_DEGREE = 20

ST_METHOD = "B"  # Breadth-first ("B") is the default mode in server.rb.

# Grid markers for occupied cells (non-numeric => non-traversable).
ME_HEAD = "MH"
ME_BODY = "MB"
ENEMY_HEAD = "EH"
ENEMY_BODY = "EB"


# ---------------------------------------------------------------------------
# Coordinate (Ruby lib/coordinate.rb)
# ---------------------------------------------------------------------------
class Coordinate:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Coordinate) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


# ---------------------------------------------------------------------------
# Snake (Ruby lib/snake.rb)
#   head = coords[0]; body = coords[1:] (head dropped, like Ruby .drop(1))
# ---------------------------------------------------------------------------
class Snake:
    def __init__(self, sid, coords, health):
        # coords: list of Coordinate, already de-duplicated (Ruby .uniq)
        self.id = sid
        self.health = health
        self.head = coords[0]
        self.body = coords[1:]

    def paintable_directions(self, body_part):
        """Which directions around body_part are open (i.e. NOT occupied by
        another part of this same snake in the adjacent orthogonal cell)."""
        directions = []
        x_values = [self.head.x] + [p.x for p in self.body if p.y == body_part.y]
        y_values = [self.head.y] + [p.y for p in self.body if p.x == body_part.x]

        if (body_part.x - 1) not in x_values:
            directions.append("left")
        if (body_part.x + 1) not in x_values:
            directions.append("right")
        if (body_part.y - 1) not in y_values:
            directions.append("up")
        if (body_part.y + 1) not in y_values:
            directions.append("down")

        if "left" in directions and "up" in directions:
            directions.append("leftup")
        if "left" in directions and "down" in directions:
            directions.append("leftdown")
        if "right" in directions and "up" in directions:
            directions.append("rightup")
        if "right" in directions and "down" in directions:
            directions.append("rightdown")

        return directions


# ---------------------------------------------------------------------------
# Grid (Ruby lib/grid.rb)
# ---------------------------------------------------------------------------
class Grid:
    def __init__(self, height, width, food, me, snakes):
        self.height = height
        self.width = width
        self.food = food          # list of Coordinate
        self.me = me              # my snake id
        self.snakes = snakes      # list of Snake
        self.area = self._make_area()

    def within_bounds(self, x, y):
        if x < 0 or x >= self.width:
            return False
        if y < 0 or y >= self.height:
            return False
        return True

    def traversable(self, x, y):
        return self.within_bounds(x, y) and isinstance(self.area[x][y], (int, float))

    def my_snake(self):
        for s in self.snakes:
            if s.id == self.me:
                return s
        return None

    def _make_area(self):
        area = [[0 for _ in range(self.height)] for _ in range(self.width)]
        self._add_snakes(area)
        self._add_food(area)
        return area

    def _add_snakes(self, area):
        for snake in self.snakes:
            me = (snake.id == self.me)
            for b in snake.body:
                if self.within_bounds(b.x, b.y):
                    area[b.x][b.y] = ME_BODY if me else ENEMY_BODY
            if self.within_bounds(snake.head.x, snake.head.y):
                area[snake.head.x][snake.head.y] = ME_HEAD if me else ENEMY_HEAD

    def _add_food(self, area):
        for f in self.food:
            if self.within_bounds(f.x, f.y):
                area[f.x][f.y] = -1


# ---------------------------------------------------------------------------
# Painter (Ruby lib/painter.rb)
# ---------------------------------------------------------------------------
class _PV:
    __slots__ = ("dx", "dy", "val")

    def __init__(self, dx, dy, val):
        self.dx = dx
        self.dy = dy
        self.val = val


class Painter:
    def __init__(self, grid):
        self.grid = grid

    def paint(self):
        self._paint_food()
        self._paint_walls()
        self._paint_snakes()

    def _paint_walls(self):
        degree = WALL_DEGREE
        weight = WALL_WEIGHT
        height = self.grid.height
        width = self.grid.width
        area = self.grid.area

        for x in range(width):
            for y in range(degree):
                if y < height and isinstance(area[x][y], (int, float)):
                    area[x][y] += (degree - y) * weight
                by = height - 1 - y
                if 0 <= by < height and isinstance(area[x][by], (int, float)):
                    area[x][by] += (degree - y) * weight

        for y in range(height):
            for x in range(degree):
                if x < width and isinstance(area[x][y], (int, float)):
                    area[x][y] += (degree - x) * weight
                bx = width - 1 - x
                if 0 <= bx < width and isinstance(area[bx][y], (int, float)):
                    area[bx][y] += (degree - x) * weight

    def _paint_snakes(self):
        my = self.grid.my_snake()
        my_body_len = len(my.body) if my else 0
        for snake in self.grid.snakes:
            if snake.id == self.grid.me:
                configs = {
                    "head_degree": SNAKE_ME_HEAD_DEGREE,
                    "head_weight": SNAKE_ME_HEAD_WEIGHT,
                    "body_degree": SNAKE_ME_BODY_DEGREE,
                    "body_weight": SNAKE_ME_BODY_WEIGHT,
                    "length_weight": 1,
                }
            else:
                # Ruby computes a dynamic length_ratio/length_weight here, but
                # the config hash it actually builds uses the STATIC config
                # value (Settings.get("snake","enemy","length_weight")). We
                # reproduce the config the Ruby code truly uses.
                configs = {
                    "head_degree": SNAKE_ENEMY_HEAD_DEGREE,
                    "head_weight": SNAKE_ENEMY_HEAD_WEIGHT,
                    "body_degree": SNAKE_ENEMY_BODY_DEGREE,
                    "body_weight": SNAKE_ENEMY_BODY_WEIGHT,
                    "length_weight": SNAKE_ENEMY_LENGTH_WEIGHT,
                }
            self._paint_snake(snake, configs)

    def _paint_food(self):
        my = self.grid.my_snake()
        health = my.health if my else 100
        health_mult = self._food_health_equation(health / 100.0)
        degree = FOOD_DEGREE
        weight = FOOD_WEIGHT * health_mult
        area = self.grid.area

        for f in self.grid.food:
            vectors = []
            f_x, f_y = f.x, f.y

            if self.grid.within_bounds(f_x, f_y):
                # the food cell itself carries a value too
                area[f_x][f_y] += weight * (degree + 1)

            for d in range(degree):
                for direction in ("left", "right", "up", "down",
                                  "leftup", "leftdown", "rightup", "rightdown"):
                    if direction == "left":
                        vectors.append(_PV(-1 * (d + 1), 0, weight * (degree - d)))
                    elif direction == "right":
                        vectors.append(_PV((d + 1), 0, weight * (degree - d)))
                    elif direction == "up":
                        vectors.append(_PV(0, -1 * (d + 1), weight * (degree - d)))
                    elif direction == "down":
                        vectors.append(_PV(0, (d + 1), weight * (degree - d)))
                    elif direction == "leftup":
                        vectors += self._diagonal_vectors(degree - d, -1, -1, weight * (d + 1))
                    elif direction == "leftdown":
                        vectors += self._diagonal_vectors(degree - d, -1, 1, weight * (d + 1))
                    elif direction == "rightup":
                        vectors += self._diagonal_vectors(degree - d, 1, -1, weight * (d + 1))
                    elif direction == "rightdown":
                        vectors += self._diagonal_vectors(degree - d, 1, 1, weight * (d + 1))

            for v in vectors:
                x = f_x + v.dx
                y = f_y + v.dy
                if self.grid.within_bounds(x, y) and isinstance(area[x][y], (int, float)):
                    area[x][y] += v.val

    def _paint_snake(self, snake, configs):
        area = self.grid.area

        # Head
        head_degree = configs["head_degree"]
        head_weight = configs["head_weight"] * configs["length_weight"]
        pdirs = snake.paintable_directions(snake.head)
        head_vectors = self._snake_paint_vectors(pdirs, head_degree, head_weight)
        for v in head_vectors:
            x = snake.head.x + v.dx
            y = snake.head.y + v.dy
            if self.grid.traversable(x, y):
                area[x][y] += v.val

        # Body
        body_degree = configs["body_degree"]
        body_weight = configs["body_weight"] * configs["length_weight"]
        for coord in snake.body:
            s_x, s_y = coord.x, coord.y
            pdirs = snake.paintable_directions(coord)
            vectors = self._snake_paint_vectors(pdirs, body_degree, body_weight)
            for v in vectors:
                x = s_x + v.dx
                y = s_y + v.dy
                if self.grid.traversable(x, y):
                    area[x][y] += v.val

    def _snake_paint_vectors(self, paintable_directions, degree, weight):
        vectors = []
        for d in range(degree):
            for direction in paintable_directions:
                if direction == "left":
                    vectors.append(_PV(-1 * (d + 1), 0, weight * (degree - d)))
                elif direction == "right":
                    vectors.append(_PV((d + 1), 0, weight * (degree - d)))
                elif direction == "up":
                    vectors.append(_PV(0, -1 * (d + 1), weight * (degree - d)))
                elif direction == "down":
                    vectors.append(_PV(0, (d + 1), weight * (degree - d)))
                elif direction == "leftup":
                    vectors += self._diagonal_vectors(degree - (d - 1), -1, -1, weight * (d + 1))
                elif direction == "leftdown":
                    vectors += self._diagonal_vectors(degree - (d - 1), -1, 1, weight * (d + 1))
                elif direction == "rightup":
                    vectors += self._diagonal_vectors(degree - (d - 1), 1, -1, weight * (d + 1))
                elif direction == "rightdown":
                    vectors += self._diagonal_vectors(degree - (d - 1), 1, 1, weight * (d + 1))
        return vectors

    def _diagonal_vectors(self, degree, dx_mult, dy_mult, val):
        if degree <= 0:
            return []
        vectors = []
        for d in range(degree - 1):
            da = degree - (d + 1)
            db = d + 1
            vectors.append(_PV(dx_mult * da, dy_mult * db, val))
        return vectors

    def _food_health_equation(self, health_percent):
        return (FOOD_MULT * (100 * math.exp(-4 * health_percent) - math.exp(-1))
                / (100 - math.exp(-1)) + 1.0)


# ---------------------------------------------------------------------------
# Snode + Tree (Ruby lib/snode.rb, lib/tree.rb)
# ---------------------------------------------------------------------------
class Snode:
    __slots__ = ("parent", "children", "dir", "coord", "val", "sum", "level")

    def __init__(self, parent, direction, level, coord, val, s):
        self.parent = parent
        self.children = []
        self.dir = direction
        self.coord = coord
        self.val = val
        self.sum = s
        self.level = level


class Tree:
    def __init__(self, grid):
        self.grid = grid
        self.tree = None
        self.count = 1
        self.tree_bottom = []
        self.levels = TREE_LEVELS

    def build_tree(self):
        head = self.grid.my_snake().head
        self.tree = Snode(None, None, 0, head, 0, 0)
        self._add_node(self.tree)

    def _add_node(self, parent):
        if parent.level >= self.levels:
            self.tree_bottom.append(parent)
            return

        current_path = self._get_path(parent)
        p_x, p_y = parent.coord.x, parent.coord.y

        avail_dir = ["left", "right", "up", "down"]
        tried_dir = []
        for direction in avail_dir:
            if direction == "up":
                x, y = p_x, p_y - 1
            elif direction == "down":
                x, y = p_x, p_y + 1
            elif direction == "left":
                x, y = p_x - 1, p_y
            else:  # right
                x, y = p_x + 1, p_y

            candidate = Coordinate(x, y)
            if self.grid.traversable(x, y) and candidate not in current_path:
                child = Snode(
                    parent,
                    direction,
                    parent.level + 1,
                    candidate,
                    self.grid.area[x][y],
                    parent.sum + self.grid.area[x][y],
                )
                parent.children.append(child)
                self.count += 1
                self._add_node(child)
            else:
                tried_dir.append(direction)

        if avail_dir == tried_dir:
            self.tree_bottom.append(parent)

    def _get_path(self, node):
        # iterative to avoid recursion depth concerns
        path = []
        while node is not None:
            path.append(node.coord)
            node = node.parent
        return path


# ---------------------------------------------------------------------------
# Squirrel (Ruby lib/squirrel.rb)
# ---------------------------------------------------------------------------
class Squirrel:
    def __init__(self, tree):
        self.tree = tree
        self.levels = TREE_LEVELS
        self.min_threshold = TREE_MIN_THRESHOLD
        self.threshold = TREE_THRESHOLD

    def bottoms_up_method(self):
        if not self.tree.tree_bottom:
            return self._emergency_dir()
        max_level = max(t.level for t in self.tree.tree_bottom)
        candidates = [t for t in self.tree.tree_bottom if t.level == max_level]
        winner = min(candidates, key=lambda t: t.sum)
        return self._bottoms_up_dir(winner).dir

    def bfd_method(self):
        winners = self._child_filter(self.tree.tree.children, 0)
        if not winners:
            return self._emergency_dir()
        winner_sum = winners[0].sum
        tied = [self._bottoms_up_dir(w) for w in winners if w.sum == winner_sum]
        return min(tied, key=lambda t: t.sum).dir

    def _emergency_dir(self):
        # Ruby's inline fallback when no surviving branches: first traversable
        # of left/right/up/down, else "left".
        head = self.tree.tree.coord
        p_x, p_y = head.x, head.y
        for direction in ("left", "right", "up", "down"):
            if direction == "up":
                x, y = p_x, p_y - 1
            elif direction == "down":
                x, y = p_x, p_y + 1
            elif direction == "left":
                x, y = p_x - 1, p_y
            else:
                x, y = p_x + 1, p_y
            if self.tree.grid.traversable(x, y):
                return direction
        return "left"

    def _child_filter(self, nodes, level):
        if level >= 2:
            nodes_with_children = [p for p in nodes if p.children]
            if len(nodes_with_children) == 0:
                return sorted(nodes, key=lambda n: n.sum)
            children = []
            for p in nodes_with_children:
                children += p.children
            children.sort(key=lambda n: n.sum)
            threshold_index = self._threshold_calc(level + 1, len(children))
            # Ruby: children[0..threshold_index] is inclusive of the endpoint
            surviving = children[:threshold_index + 1]
            return self._child_filter(surviving, level + 1)
        else:
            flat = []
            for n in nodes:
                flat += n.children
            return self._child_filter(flat, level + 1)

    def _bottoms_up_dir(self, node):
        # walk up until the node whose parent is the origin (level 0)
        while node.parent is not None and node.parent.level != 0:
            node = node.parent
        return node

    def _threshold_calc(self, level, length):
        optimal_num_nodes = 3 ** level
        if length < math.floor(optimal_num_nodes * self.min_threshold):
            return length
        return math.floor(optimal_num_nodes * self.threshold)


# ---------------------------------------------------------------------------
# Robustness fallback: guaranteed-legal move (v1 coordinates)
# ---------------------------------------------------------------------------
def _fallback_move(game_state):
    """In-bounds move that does not enter any snake body (tails enterable)."""
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        you = game_state["you"]
        head = you["body"][0]
        hx, hy = head["x"], head["y"]

        blocked = set()
        for s in board.get("snakes", []):
            body = s.get("body", [])
            # tails move away next turn, so they are enterable -> drop last cell
            cells = body[:-1] if len(body) > 1 else body
            for c in cells:
                blocked.add((c["x"], c["y"]))

        # v1 deltas: up=y+1, down=y-1, left=x-1, right=x+1
        for direction, (nx, ny) in (
            ("up", (hx, hy + 1)),
            ("down", (hx, hy - 1)),
            ("left", (hx - 1, hy)),
            ("right", (hx + 1, hy)),
        ):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
                return direction
    except Exception:
        pass
    return "up"


def _is_legal(game_state, direction):
    try:
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head = game_state["you"]["body"][0]
        hx, hy = head["x"], head["y"]
        deltas = {"up": (hx, hy + 1), "down": (hx, hy - 1),
                  "left": (hx - 1, hy), "right": (hx + 1, hy)}
        if direction not in deltas:
            return False
        nx, ny = deltas[direction]
        if not (0 <= nx < w and 0 <= ny < h):
            return False
        for s in board.get("snakes", []):
            b = s.get("body", [])
            cells = b[:-1] if len(b) > 1 else b
            for c in cells:
                if c["x"] == nx and c["y"] == ny:
                    return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CodeClash / Battlesnake v1 interface
# ---------------------------------------------------------------------------
def move(game_state):
    try:
        board = game_state["board"]
        width = board["width"]
        height = board["height"]
        me_id = game_state["you"]["id"]

        # Remap v1 (bottom-left, y-up) -> old API (top-left, y-down) by
        # flipping y. Direction strings match v1 after the flip.
        def fy(y):
            return height - 1 - y

        snakes = []
        for s in board.get("snakes", []):
            seen = set()
            coords = []
            for c in s.get("body", []):  # de-dup preserving order (Ruby .uniq)
                key = (c["x"], c["y"])
                if key not in seen:
                    seen.add(key)
                    coords.append(Coordinate(c["x"], fy(c["y"])))
            if not coords:
                continue
            snakes.append(Snake(s["id"], coords, s.get("health", 100)))

        food = [Coordinate(f["x"], fy(f["y"])) for f in board.get("food", [])]

        if not any(s.id == me_id for s in snakes):
            return {"move": _fallback_move(game_state)}

        grid = Grid(height=height, width=width, food=food, me=me_id, snakes=snakes)
        Painter(grid).paint()

        tree = Tree(grid)
        tree.build_tree()

        squirrel = Squirrel(tree)
        if ST_METHOD == "D":
            direction = squirrel.bottoms_up_method()
        else:
            direction = squirrel.bfd_method()

        # Safety net: never crash or self-collide / hit a wall.
        if not _is_legal(game_state, direction):
            direction = _fallback_move(game_state)

        return {"move": direction}
    except Exception:
        return {"move": _fallback_move(game_state)}


def info():
    return {
        "apiversion": "1",
        "author": "nbw",
        "color": "#ff6666",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
