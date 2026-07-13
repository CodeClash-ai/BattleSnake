import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""
Port of JerryKott's "Medusa" Battlesnake (Cincom Smalltalk, 2017), 2nd place
advanced category. Faithfully reimplements the original move/decision logic
(the Medusa#behave strategy chain, A* PathNode search, tile safeSpace flood
fill, bubble/quadrant heuristics) against the current Battlesnake v1 API.

Original repo: https://github.com/JerryKott/Battlesnake2017 (Smalltalk .pst fileout)

COORDINATE REMAP:
  The 2017 code used a top-left origin, y-DOWN board:
      Directions = { (0,-1):up, (0,1):down, (-1,0):left, (1,0):right }
  The current v1 API uses a bottom-left origin, y-UP board:
      up=y+1, down=y-1, left=x-1, right=x+1
  We keep all of Medusa's internal geometry (distances, quadrants, corners,
  A*) exactly as written by working in the ORIGINAL top-left/y-down space,
  and only flip the y axis when reading v1 state in and when emitting the
  final "up/down/left/right" move name. This preserves the original behaviour
  bit-for-bit (e.g. "closest corner" is still a real corner, quadrant splits
  are symmetric so unaffected).

Original constants (from the fileout):
  StepCost = 100, InitialSnakeLength = 3, WinningGoldCount = 4,
  HighPassingCost = 0xFFFFFFF, Medusa bubbleSize = 3.
"""

# ---------------------------------------------------------------------------
# Constants (verbatim from the Smalltalk shared variables)
# ---------------------------------------------------------------------------
STEP_COST = 100
INITIAL_SNAKE_LENGTH = 3
HIGH_PASSING_COST = 0xFFFFFFF

# Directions dictionary from the original, in ORIGINAL (top-left, y-down) space.
# offset (dx, dy) -> name
DIRECTIONS = {
    (0, -1): "up",
    (0, 1): "down",
    (-1, 0): "left",
    (1, 0): "right",
}
# The four rectangular move offsets, in original space.
MOVE_OFFSETS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


def _sign(n):
    return (n > 0) - (n < 0)


def battlesnake_distance(dx, dy):
    # (p2 - p1) battlesnakeDistance == manhattan distance
    return abs(dx) + abs(dy)


# ---------------------------------------------------------------------------
# Board / tile model
#
# We build a fresh Board each turn (matching the effect of updateState:, which
# resets tile contents, snakes, paths and neighbour caches every request).
# All coordinates below are ORIGINAL top-left/y-down coordinates.
# ---------------------------------------------------------------------------
class Snake:
    """A snake. `is_medusa` marks our own snake. `segments` are (x,y) tuples,
    head first, in original coordinates."""

    def __init__(self, sid, name, health, segments, is_medusa):
        self.id = sid
        self.name = name
        self.health = health
        self.segments = segments            # [head, ..., tail], original coords
        self.is_medusa = is_medusa

    @property
    def length(self):
        return len(self.segments)

    @property
    def power(self):
        return self.length

    @property
    def head(self):
        return self.segments[0]

    @property
    def tail(self):
        return self.segments[-1]

    # Snake >> isWeakerThanMedusa
    def is_weaker_than_medusa(self, board):
        return self.power < board.medusa.power

    def sees_food(self, board):
        # Snake >> seesFood : any head neighbour has food
        for nb in board.neighbours(self.head):
            if board.has_food(nb):
                return True
        return False


class Board:
    def __init__(self, width, height, food, snakes, my_id):
        self.width = width
        self.height = height
        self.food = set(food)               # set of (x,y) original coords
        self.snakes = []                    # list[Snake]
        self.medusa = None

        # Occupancy maps keyed by (x,y):
        #   snake_part[pos] -> (snake, index_in_segments)
        self.snake_part = {}
        for sd in snakes:
            is_me = (sd["id"] == my_id)
            snk = Snake(sd["id"], sd.get("name", ""), sd.get("health", 100),
                        sd["_segments"], is_me)
            self.snakes.append(snk)
            if is_me:
                self.medusa = snk
            for idx, pos in enumerate(snk.segments):
                # First segment written wins for head detection; but for
                # overlaps we keep earliest index (head has index 0).
                prev = self.snake_part.get(pos)
                if prev is None or idx < prev[1]:
                    self.snake_part[pos] = (snk, idx)

        self._neighbour_cache = {}
        self._safespace_cache = {}

    # --- geometry -----------------------------------------------------------
    def in_bounds(self, pos):
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbours(self, pos):
        """BoardTile >> neighbours: the 4 orthogonal in-bounds tiles.
        (Off-board neighbours become Walls in the original; here we simply
        omit them and treat off-board as non-traversable everywhere.)"""
        cached = self._neighbour_cache.get(pos)
        if cached is not None:
            return cached
        x, y = pos
        res = []
        for dx, dy in MOVE_OFFSETS:
            np = (x + dx, y + dy)
            if self.in_bounds(np):
                res.append(np)
        self._neighbour_cache[pos] = res
        return res

    def corner_tiles(self):
        # Board >> cornerTiles (top-left origin): TL, TR, BR, BL
        return [(0, 0),
                (self.width - 1, 0),
                (self.width - 1, self.height - 1),
                (0, self.height - 1)]

    # --- tile content queries ----------------------------------------------
    def has_food(self, pos):
        return pos in self.food

    def snake_at(self, pos):
        entry = self.snake_part.get(pos)
        return entry[0] if entry else None

    def part_index(self, pos):
        entry = self.snake_part.get(pos)
        return entry[1] if entry else None

    def is_occupied_by_snake(self, pos):
        return pos in self.snake_part

    def is_empty(self, pos):
        # EmptySpace: a tile with no snake part and no reward.
        # (Reward tiles are NOT empty; walls/off-board not empty either.)
        if pos in self.snake_part:
            return False
        if pos in self.food:
            return False
        return self.in_bounds(pos)

    def has_reward(self, pos):
        return pos in self.food  # gold does not exist in v1

    def has_snake_head(self, pos):
        return self.part_index(pos) == 0

    def has_enemy_head(self, pos):
        # BoardTile >> hasEnemyHead : head and snake is a plain (enemy) Snake
        entry = self.snake_part.get(pos)
        if entry is None:
            return False
        snk, idx = entry
        return idx == 0 and not snk.is_medusa

    # SnakePart >> tailLength : distance from this segment to the last segment
    def tail_length(self, pos):
        entry = self.snake_part.get(pos)
        if entry is None:
            return 0
        snk, idx = entry
        return (snk.length - 1) - idx

    # --- traversability -----------------------------------------------------
    def content_is_traversable(self, pos):
        """Dispatch on the tile's content type, mirroring the Smalltalk
        isTraversable overrides."""
        if not self.in_bounds(pos):
            return False  # Wall isTraversable -> false
        entry = self.snake_part.get(pos)
        if entry is not None:
            snk, idx = entry
            if idx == 0:
                # Head >> isTraversable : snake isWeakerThanMedusa
                return snk.is_weaker_than_medusa(self)
            # Body >> isTraversable : it's the tail, snake longer than
            # InitialSnakeLength, and head has no imminent food.
            is_tail = (idx == snk.length - 1)
            return (snk.length > INITIAL_SNAKE_LENGTH
                    and is_tail
                    and not snk.sees_food(self))
        # EmptySpace / Reward -> TileContent >> isTraversable :
        #   safe > 1 and dangerous == 0, over the tile's neighbours.
        safe = 0
        dangerous = 0
        for nb in self.neighbours(pos):
            if self.is_empty(nb) or self.has_reward(nb):
                safe += 1
            if self.has_snake_head(nb):
                snk = self.snake_at(nb)
                if snk.is_medusa or snk.is_weaker_than_medusa(self):
                    safe += 1
                else:
                    dangerous += 1
        return safe > 1 and dangerous == 0

    def may_be_traversable_in(self, pos, future_turns):
        """BoardTile >> mayBeTraversableIn:"""
        if not self.in_bounds(pos):
            return False
        entry = self.snake_part.get(pos)
        if entry is not None:
            # SnakePart >> mayBeTraversableIn: tailLength <= futureTurns
            return self.tail_length(pos) <= future_turns
        # TileContent default: isTraversable (ignores futureTurns)
        return self.content_is_traversable(pos)

    def passing_cost_in(self, pos, number_of_moves):
        """BoardTile >> passingCostIn:"""
        if self.may_be_traversable_in(pos, number_of_moves):
            return 0
        if not self.in_bounds(pos):
            return HIGH_PASSING_COST
        entry = self.snake_part.get(pos)
        if entry is None:
            return HIGH_PASSING_COST  # non-traversable empty-ish tile
        return 0 if self.tail_length(pos) < number_of_moves else HIGH_PASSING_COST

    # --- isSafe / safeSpace -------------------------------------------------
    def is_safe(self, pos):
        # BoardTile >> isSafe : traversable and no neighbour has an enemy head
        if not self.content_is_traversable(pos):
            return False
        for nb in self.neighbours(pos):
            if self.has_enemy_head(nb):
                return False
        return True

    def safe_space(self, pos):
        """BoardTile >> safeSpace : flood fill of safe tiles reachable from
        this tile. If the tile itself is unsafe, we start from its neighbours
        (excluding itself), exactly as the original does."""
        cached = self._safespace_cache.get(pos)
        if cached is not None:
            return cached
        remaining = []
        visited = set()
        if not self.is_safe(pos):
            visited.add(pos)
            remaining.extend(self.neighbours(pos))
        # safeSpaceWith:excluding: begins by adding self to `remaining`.
        remaining.append(pos)
        safe = set()
        # Use a queue (removeFirst semantics).
        qi = 0
        while qi < len(remaining):
            current = remaining[qi]
            qi += 1
            if current in visited:
                continue
            if self.is_safe(current):
                safe.add(current)
                remaining.extend(self.neighbours(current))
            visited.add(current)
        self._safespace_cache[pos] = safe
        return safe

    # --- distance helpers ---------------------------------------------------
    def area_within_distance(self, distance):
        # BoardTile >> areaWithinDistance: 2*d*(d+1)
        return 2 * distance * (distance + 1)

    def tiles_within_distance(self, pos, distance):
        # BoardTile >> tilesWithinDistance: (diamond within manhattan dist)
        px, py = pos
        tiles = set()
        x_min = max(px - distance, 0)
        x_max = min(px + distance, self.width - 1)
        for x in range(x_min, x_max + 1):
            x_off = abs(x - px)
            y_from = max(py - distance + x_off, 0)
            y_to = min(py + distance - x_off, self.height - 1)
            for y in range(y_from, y_to + 1):
                tiles.add((x, y))
        return tiles

    def traversable_tiles_within_distance(self, pos, distance):
        return {t for t in self.tiles_within_distance(pos, distance)
                if self.content_is_traversable(t)}


# ---------------------------------------------------------------------------
# A* (PathNode >> findPathToTarget), including risk cost.
# Returns a list of tiles (original coords) EXCLUDING the start tile, i.e. the
# steps to walk, matching backtrackPath: which removes the first element.
# ---------------------------------------------------------------------------
def _probability_of_reaching(board, head_pos, tile, number_of_moves):
    # Head >> probabilityOfReaching:in:
    hx, hy = head_pos
    tx, ty = tile
    distance = battlesnake_distance(tx - hx, ty - hy)
    if distance > number_of_moves:
        return 0
    if distance == 0:
        return 10 * STEP_COST
    area = board.area_within_distance(distance)
    return round((10 * STEP_COST) / area)


def find_path(board, start, target):
    if start == target:
        # backtrackPath removes the first (start) node -> empty path.
        return []

    import heapq

    tx, ty = target

    def dist_to_target(pos):
        return battlesnake_distance(pos[0] - tx, pos[1] - ty)

    # Per-node bookkeeping.
    parent = {start: None}
    dist_from_start = {start: 0}

    def cost_of_risk(pos, dfs):
        cost = board.passing_cost_in(pos, dfs)
        for snk in board.snakes:
            if not snk.is_medusa:  # isEnemy
                cost += _probability_of_reaching(board, snk.head, pos, dfs)
        return cost

    def cost_of_travel(pos):
        dfs = dist_from_start[pos]
        g = dfs * STEP_COST
        h = dist_to_target(pos) * STEP_COST
        return g + h + cost_of_risk(pos, dfs)

    visited = set()
    counter = 0
    open_heap = []
    heapq.heappush(open_heap, (cost_of_travel(start), counter, start))
    in_open = {start}

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current not in in_open:
            continue
        in_open.discard(current)
        visited.add(current)

        if current == target:
            # backtrack
            path = []
            node = current
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()
            return path[1:]  # drop start tile

        cur_dfs = dist_from_start[current]
        # Expand neighbours (original sorts by distance-to-target; heap makes
        # explicit order immaterial for correctness).
        for nb in board.neighbours(current):
            tentative_dfs = cur_dfs + 1
            if nb not in dist_from_start:
                # First discovery.
                if not board.may_be_traversable_in(nb, tentative_dfs):
                    visited.add(nb)
                    continue
                parent[nb] = current
                dist_from_start[nb] = tentative_dfs
                heapq.heappush(open_heap, (cost_of_travel(nb), counter := counter + 1, nb))
                in_open.add(nb)
            else:
                if nb in visited:
                    continue
                if not board.may_be_traversable_in(nb, dist_from_start[nb]):
                    visited.add(nb)
                    continue
                if tentative_dfs < dist_from_start[nb]:
                    parent[nb] = current
                    dist_from_start[nb] = tentative_dfs
                    heapq.heappush(open_heap, (cost_of_travel(nb), counter := counter + 1, nb))
                    in_open.add(nb)
    return None


# ---------------------------------------------------------------------------
# Medusa decision logic (Medusa >> behave and its behaviour methods).
# `chosen` accumulates the chosen next tile; once set, tryBehavior short-circuits.
# ---------------------------------------------------------------------------
class Medusa:
    def __init__(self, board, turn):
        self.board = board
        self.snake = board.medusa
        self.turn = turn
        self.chosen = None                 # next tile (original coords) or None
        self.current_behavior = None
        self.bubble_size = 3

    # --- accessors mirroring the Snake/Medusa protocol ---------------------
    @property
    def head(self):
        return self.snake.head

    @property
    def tail(self):
        return self.snake.tail

    @property
    def length(self):
        return self.snake.length

    @property
    def health(self):
        return self.snake.health

    def distance_to(self, tile):
        hx, hy = self.head
        return battlesnake_distance(tile[0] - hx, tile[1] - hy)

    def neighbours(self):
        # Snake >> neighbours : head-tile neighbours sorted by descending
        # safeSpace size (bigger safe space first).
        nbs = list(self.board.neighbours(self.head))
        nbs.sort(key=lambda t: len(self.board.safe_space(t)), reverse=True)
        return nbs

    def traversable_tiles(self):
        return [t for t in self.neighbours()
                if self.board.content_is_traversable(t)]

    def empty_tiles(self):
        return [t for t in self.neighbours() if self.board.is_empty(t)]

    def possible_tiles(self):
        # Medusa >> possibleTiles : traversable neighbours, else empty neighbours.
        pt = self.traversable_tiles()
        if not pt:
            pt = self.empty_tiles()
        return pt

    def enemy_snakes(self):
        return [s for s in self.board.snakes if s is not self.snake]

    # Medusa >> findPathTo: only accept a path whose first step is a
    # possible tile.
    def find_path_to(self, target):
        path = find_path(self.board, self.head, target)
        if path is None:
            return None
        if not path:
            return []
        if path[0] in self.possible_tiles():
            return path
        return None

    # Snake >> findRewardPaths / Medusa >> findRewardPaths
    def find_reward_paths(self):
        # Snake >> findRewardPaths, but since `self` is a Medusa the path
        # lookup dispatches to Medusa >> findPathTo:, which only accepts a
        # path whose first step is one of my possible tiles.
        paths = []
        for reward in self.board.food:
            p = self.find_path_to(reward)
            if p is not None and p:
                paths.append((reward, p))
        paths.sort(key=lambda rp: len(rp[1]))
        # Medusa filters out risky reward paths.
        answer = list(paths)
        enemies = self.enemy_snakes()
        for reward, epath in paths:
            if len(self.board.safe_space(reward)) <= self.length:
                if (reward, epath) in answer:
                    answer.remove((reward, epath))
                continue
            for enemy in enemies:
                enemy_path = find_path(self.board, enemy.head, reward)
                if enemy_path is not None and len(enemy_path) <= len(epath):
                    if (reward, epath) in answer:
                        answer.remove((reward, epath))
                    break
        return answer

    def find_path_to_reward_food(self):
        for reward, path in self.find_reward_paths():
            # Only Food exists in v1; all rewards qualify.
            return (reward, path)
        return None

    # ---- behaviours -------------------------------------------------------
    def move_to(self, tile):
        # Medusa >> moveTo: -- if the requested tile is not one of my possible
        # tiles, fall back to any possible tile (or, if none, any neighbour).
        options = self.possible_tiles()
        move_to = tile if tile in options else None
        if not options:
            options = self.board.neighbours(self.head)
        if move_to is None:
            move_to = options[0] if options else None
        self.chosen = move_to

    def try_behavior(self, fn):
        if self.current_behavior is not None:
            return
        fn()

    def closest_corner(self):
        corners = self.board.corner_tiles()
        return min(corners, key=lambda c: self.distance_to(c))

    def farthest_corner(self):
        corners = self.board.corner_tiles()
        return max(corners, key=lambda c: self.distance_to(c))

    def farthest_edge(self):
        corner = self.farthest_corner()
        hx, hy = self.head
        cx, cy = corner
        w = abs(cx - hx)
        h = abs(cy - hy)
        # farthestEdge: width>=height -> (corner x, self y) else (self x, corner y)
        if w >= h:
            return (cx, hy)
        return (hx, cy)

    def board_centre(self):
        b = self.board
        return (round(b.width / 2), round(b.height / 2))

    # findFood
    def find_food(self):
        if self.health > 50:
            return
        rp = self.find_path_to_reward_food()
        if rp is None:
            return
        food, path = rp
        if len(self.board.traversable_tiles_within_distance(food, self.length)) < self.length:
            return
        if not path:
            return
        tile = path[0]
        if tile not in self.possible_tiles():
            return
        self.current_behavior = "findFood"
        self.move_to(tile)

    # findGold - no gold in v1, always a no-op (health<20 or no coins -> return)
    def find_gold(self):
        return

    # goToClosestCorner
    def go_to_closest_corner(self):
        path = self.find_path_to(self.closest_corner())
        if path is None or not path:
            return
        self.current_behavior = "goToClosestCorner"
        self.move_to(path[0])

    # findSafestQuadrant
    def find_safest_quadrant(self):
        tiles = self._safest_quadrant_for()
        if not tiles:
            return
        b = self.board
        center = (round(b.width / 2 - 1), round(b.height / 2 - 1))
        tiles = sorted(tiles, key=lambda t: battlesnake_distance(
            t[0] - center[0], t[1] - center[1]))
        target = None
        for t in tiles:
            if battlesnake_distance(t[0] - center[0], t[1] - center[1]) >= 4:
                target = t
                break
        if target is None:
            return
        path = self.find_path_to(target)
        if path is None or not path:
            return
        tile = path[0]
        if tile not in self.traversable_tiles():
            return
        if len(self.board.safe_space(tile)) < self.length:
            return
        self.current_behavior = "findSafestQuadrant"
        self.move_to(tile)

    def _safest_quadrant_for(self):
        # Board >> safestQuadrantFor: aSnake
        b = self.board
        my_safe = self.board.safe_space(self.head)
        quads = self._quadrants()
        result = []
        for q in quads:
            trav = [t for t in q if b.content_is_traversable(t)]
            filtered = [t for t in trav if t in my_safe]
            result.append(filtered)
        result.sort(key=len, reverse=True)
        return result[0] if result else None

    def _quadrants(self):
        # Board >> quadrants
        b = self.board
        ext = (int((b.width / 2 - 1) // 1) if (b.width / 2 - 1) >= 0
               else -(-(b.width / 2 - 1) // 1),
               )
        # extent := floor(width/2 - 1) @ floor(height/2 - 1)
        import math
        ex = math.floor(b.width / 2 - 1)
        ey = math.floor(b.height / 2 - 1)
        corners = [
            (0, 0),
            (round(b.width / 2), 0),
            (0, round(b.height / 2)),
            (round(b.width / 2), round(b.height / 2)),
        ]
        quads = []
        for (ox, oy) in corners:
            cx = ox + ex
            cy = oy + ey
            tiles = self._tiles_in_rectangle(ox, oy, cx, cy)
            quads.append(tiles)
        return quads

    def _tiles_in_rectangle(self, x0, y0, x1, y1):
        b = self.board
        dx = x1 - x0
        dy = y1 - y0
        sx = _sign(dx) or 1
        sy = _sign(dy) or 1
        tiles = []
        x = x0
        while True:
            y = y0
            while True:
                if b.in_bounds((x, y)):
                    tiles.append((x, y))
                if y == y1:
                    break
                y += sy
            if x == x1:
                break
            x += sx
        return tiles

    # chaseTail
    def chase_tail(self):
        path = self.find_path_to(self.tail)
        if path is None or not path:
            return
        tile = path[0]
        if tile not in self.possible_tiles():
            return
        if len(self.board.safe_space(tile)) < self.length:
            return
        self.current_behavior = "chaseTail"
        self.move_to(tile)

    # findSafestSpace
    def find_safest_space(self):
        options = [t for t in self.possible_tiles()
                   if self.board.content_is_traversable(t)]
        if not options:
            return
        self.current_behavior = "findSafestSpace"
        first = options[0]
        if len(options) == 1:
            self.move_to(first)
            return
        second = options[1]
        if len(self.board.safe_space(first)) > self.length:
            self.move_to(first)
            return
        if len(self.board.safe_space(first)) == len(self.board.safe_space(second)):
            two = self._sort_by_count_within_length([first, second])
            self.move_to(two[0])
            return
        self.move_to(first)

    def _sort_by_count_within_length(self, options):
        my_len = self.length
        return sorted(options, key=lambda t: len(
            self.board.traversable_tiles_within_distance(t, my_len)), reverse=True)

    # goToPerimeter
    def go_to_perimeter(self):
        edge = self.farthest_corner()
        if self.find_path_to(edge) is None:
            edge = self.farthest_edge()
        if self.find_path_to(edge) is None:
            edge = self.board_centre()
        path = self.find_path_to(edge)
        if path is None or not path:
            return
        self.current_behavior = "goToPerimeter"
        self.move_to(path[0])

    # avoidTraps
    def avoid_traps(self):
        options = self.possible_tiles()
        if len(options) <= 1:
            return
        risky = []
        for t in options:
            if len(self.board.safe_space(t)) > self.length:
                return  # a safe option exists; nothing to avoid
            risky.append(t)
        risky = [t for t in risky if self.board.is_empty(t)]
        if not risky:
            return
        self.current_behavior = "avoidTraps"
        self.move_to(risky[0])

    # randomMove (last resort)
    def random_move(self):
        self.current_behavior = "randomMove"
        empties = self.empty_tiles()
        if not empties:
            self.current_behavior = "trapped"
            nbs = self.board.neighbours(self.head)
            self.move_to(nbs[0] if nbs else None)
            return
        self.move_to(empties[0])

    # Medusa >> behave
    def behave(self):
        if self.turn <= 5:
            self.try_behavior(self.find_food)
            self.try_behavior(self.go_to_closest_corner)
        else:
            self.try_behavior(self.find_gold)
            self.try_behavior(self.find_food)
        self.try_behavior(self.find_safest_quadrant)
        self.try_behavior(self.chase_tail)
        self.try_behavior(self.find_safest_space)
        self.try_behavior(self.go_to_perimeter)
        self.try_behavior(self.avoid_traps)
        self.try_behavior(self.random_move)


# ---------------------------------------------------------------------------
# v1 API glue
# ---------------------------------------------------------------------------
def _flip_y(y, height):
    """Convert between v1 (bottom-left, y-up) and original (top-left, y-down)."""
    return height - 1 - y


def _build_board(game_state):
    board_in = game_state["board"]
    width = board_in["width"]
    height = board_in["height"]
    food = [(f["x"], _flip_y(f["y"], height)) for f in board_in.get("food", [])]

    snakes = []
    for s in board_in.get("snakes", []):
        body = s.get("body", [])
        if not body:
            continue
        segs = [(p["x"], _flip_y(p["y"], height)) for p in body]
        snakes.append({
            "id": s["id"],
            "name": s.get("name", ""),
            "health": s.get("health", 100),
            "_segments": segs,
        })
    my_id = game_state["you"]["id"]
    return Board(width, height, food, snakes, my_id), height


def _tile_to_move(head, tile, height):
    """Given original-coord head and chosen tile, produce a v1 move name."""
    if tile is None:
        return None
    dx = tile[0] - head[0]
    dy = tile[1] - head[1]
    # Normalise to unit step in case the chosen tile is not adjacent.
    if dx != 0 and dy != 0:
        # prefer the dominant axis
        if abs(dx) >= abs(dy):
            dy = 0
        else:
            dx = 0
    ux, uy = _sign(dx), _sign(dy)
    name = DIRECTIONS.get((ux, uy))
    return name


def _fallback_move(game_state):
    """Safe last-resort move that stays in bounds and off snake bodies
    (tails are enterable). Works directly in v1 coordinates."""
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    # Occupied cells (exclude every snake's tail tip, which will vacate).
    occupied = set()
    for s in board.get("snakes", []):
        b = s.get("body", [])
        for i, p in enumerate(b):
            if i == len(b) - 1:
                continue  # tail enterable
            occupied.add((p["x"], p["y"]))

    candidates = [
        ("up", (hx, hy + 1)),
        ("down", (hx, hy - 1)),
        ("left", (hx - 1, hy)),
        ("right", (hx + 1, hy)),
    ]
    for name, (nx, ny) in candidates:
        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
            return name
    # In bounds even if into a body.
    for name, (nx, ny) in candidates:
        if 0 <= nx < w and 0 <= ny < h:
            return name
    return "up"


def _move_is_safe(game_state, name):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]
    delta = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}[name]
    nx, ny = hx + delta[0], hy + delta[1]
    if not (0 <= nx < w and 0 <= ny < h):
        return False
    for s in board.get("snakes", []):
        b = s.get("body", [])
        for i, p in enumerate(b):
            if i == len(b) - 1:
                continue
            if (p["x"], p["y"]) == (nx, ny):
                return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def info():
    return {
        "apiversion": "1",
        "author": "JerryKott",
        "color": "#CFB53B",   # WormHole color (Medusa)
        "head": "tongue",
        "tail": "curled",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        board, height = _build_board(game_state)
        if board.medusa is None:
            return {"move": _fallback_move(game_state)}
        turn = game_state.get("turn", 0)
        medusa = Medusa(board, turn)
        medusa.behave()
        name = _tile_to_move(medusa.head, medusa.chosen, height)
        if name is None or not _move_is_safe(game_state, name):
            name = _fallback_move(game_state)
        return {"move": name}
    except Exception:
        try:
            return {"move": _fallback_move(game_state)}
        except Exception:
            return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
