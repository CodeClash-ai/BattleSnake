"""
Port of woofers/battlesnake (Java) into CodeClash arena format.

Original: https://github.com/woofers/battlesnake  (Java)
Reproduced snake: the 2020 "Stay Home and Code" veteran-division snake
(botname WALTER), which is the code living on the default branch of the repo.

Strategy (from README + Snake.java / Board.java):
  - Mode selection (Snake.mode):
        HUNGRY_STATE if health <= 50
        ATTACK_STATE if length > longest other snake
        else HUNGRY_STATE
  - HUNGRY: goToFood -> goToAttack -> goToTail -> fallback
    ATTACK: goToAttack -> goToFood -> goToTail -> fallback
  - Pathing is a BFS flood-fill returning the first (shortest) initial move
    that reaches a destination, rejecting moves that dump us into a region
    smaller than max(4, floor(len/2)) (Board.findPath / regionSize).
  - Grid tiles: bodies are WALL, own/other tails are TAIL (enterable),
    squares adjacent to longer-or-equal enemy heads become FAKE_WALL
    (enterable but avoided when possible). Region sizes computed via
    flood-fill with FUDGE_FACTOR=2 filling ahead of enemy heads.

Coordinate remap: the original Java (2018/2019 API) used a top-left origin
where UP = y-1. The current v1 API uses a bottom-left origin (up = y+1).
The internal search geometry is direction-symmetric, so we define adjacency
directly in v1 coordinates and map final directions consistently.
"""

from collections import deque

# ---- tile constants -------------------------------------------------------
EMPTY = 0
WALL = 1
FOOD = 2
FAKE_WALL = 3
TAIL = 4
HEAD = 5

FUDGE_FACTOR = 2
IGNORE_SIZE = 4
HUNGER_ZONE = 50

# v1 directions: up=y+1, down=y-1, left=x-1, right=x+1
DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
FALLBACK = "left"


def info():
    return {
        "apiversion": "1",
        "author": "woofers",
        "color": "#6b4226",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


# ---------------------------------------------------------------------------
class Board:
    def __init__(self, game_state):
        b = game_state["board"]
        self.width = b["width"]
        self.height = b["height"]
        self.food = [(f["x"], f["y"]) for f in b["food"]]
        self.you = game_state["you"]
        self.you_id = self.you["id"]
        # keep only alive snakes (v1 already prunes dead, but guard anyway)
        self.snakes = [s for s in b["snakes"] if s.get("health", 0) >= 0
                       and s.get("body")]
        self.grid = [[EMPTY] * self.height for _ in range(self.width)]
        self.regions = None
        self._build_grid()
        self._fill_regions()

    # -- helpers ------------------------------------------------------------
    def exists(self, p):
        x, y = p
        return 0 <= x < self.width and 0 <= y < self.height

    @staticmethod
    def _body(s):
        return [(c["x"], c["y"]) for c in s["body"]]

    @staticmethod
    def just_ate(s):
        return s.get("health", 0) == 100

    def _length(self, s):
        return len(s["body"])

    def _you_length(self):
        return len(self.you["body"])

    def longest_other(self):
        mx = None
        for s in self.snakes:
            if s["id"] == self.you_id:
                continue
            if mx is None or self._length(s) > mx:
                mx = self._length(s)
        return mx  # None if no other snakes

    def you_longer_than(self, s):
        return self._you_length() > self._length(s)

    def adjacent(self, p):
        x, y = p
        return {name: (x + dx, y + dy) for name, (dx, dy) in DIRS.items()}

    # -- grid ---------------------------------------------------------------
    def _build_grid(self):
        for fx, fy in self.food:
            if self.exists((fx, fy)):
                self.grid[fx][fy] = FOOD

        for s in self.snakes:
            body = self._body(s)
            head = body[0]
            n = len(body)
            for i, (x, y) in enumerate(body):
                if not self.exists((x, y)):
                    continue
                if i == n - 1 and n > 1 and not self.just_ate(s):
                    self.grid[x][y] = TAIL
                else:
                    self.grid[x][y] = WALL

            if self.exists(head):
                if s["id"] == self.you_id:
                    self.grid[head[0]][head[1]] = HEAD
                else:
                    self.grid[head[0]][head[1]] = HEAD
                    # mark danger squares around enemy heads we don't beat
                    if not self.you_longer_than(s):
                        for p in self.adjacent(head).values():
                            if self.exists(p):
                                px, py = p
                                if self.grid[px][py] in (EMPTY, FOOD):
                                    self.grid[px][py] = FAKE_WALL

    def is_food(self, p):
        if not self.exists(p):
            return False
        return self.grid[p[0]][p[1]] == FOOD

    def is_dangerous(self, p):
        if not self.exists(p):
            return False
        return self.grid[p[0]][p[1]] in (FAKE_WALL, TAIL)

    def is_filled(self, p, grid=None):
        # out of bounds counts as filled
        if not self.exists(p):
            return True
        g = grid if grid is not None else self.grid
        return g[p[0]][p[1]] not in (EMPTY, FOOD, FAKE_WALL, TAIL)

    def movable(self, p, exclude_danger):
        if self.is_filled(p):
            return False
        if exclude_danger and self.is_dangerous(p):
            return False
        return True

    # -- regions ------------------------------------------------------------
    def _fill_regions(self):
        self.regions = [[None] * self.height for _ in range(self.width)]
        for x in range(self.width):
            for y in range(self.height):
                if self.is_filled((x, y)):
                    self.regions[x][y] = 0
        # fill ahead of enemy heads (FUDGE_FACTOR)
        for s in self.snakes:
            if s["id"] == self.you_id or self._length(s) <= 1:
                continue
            body = self._body(s)
            head = body[0]
            neck = body[1]
            dx = head[0] - neck[0]
            dy = head[1] - neck[1]
            for i in range(1, FUDGE_FACTOR + 1):
                p = (head[0] + dx * i, head[1] + dy * i)
                if self.exists(p):
                    self.regions[p[0]][p[1]] = 0

        for x in range(self.width):
            for y in range(self.height):
                if self.regions[x][y] is not None:
                    continue
                region = self._flood_region((x, y))
                size = len(region)
                for (rx, ry) in region:
                    self.regions[rx][ry] = size

    def _flood_region(self, start):
        # connected empty-ish region (excludes danger, same as findPath fill)
        seen = set()
        q = deque([start])
        seen.add(start)
        out = []
        while q:
            cur = q.popleft()
            out.append(cur)
            for nxt in self.adjacent(cur).values():
                if nxt in seen:
                    continue
                if self.movable(nxt, True):
                    seen.add(nxt)
                    q.append(nxt)
        return out

    def region_size(self, p):
        if not self.exists(p):
            return 0
        v = self.regions[p[0]][p[1]]
        return v if v is not None else 0

    # -- pathfinding (BFS flood-fill) --------------------------------------
    def find_path(self, destinations, start, check_box=True):
        dests = [d for d in destinations if d != start]
        if not dests:
            return None
        dest_set = set(dests)
        small_region = max(IGNORE_SIZE, self._you_length() // 2)

        # BFS; each node carries its initial move direction
        seen = {start}
        # queue entries: (point, initial_move_name)
        q = deque()
        # seed with start (no initial move yet)
        q.append((start, None))
        while q:
            cur, initial = q.popleft()
            if initial is not None and cur in dest_set:
                # region check
                if check_box:
                    dx, dy = DIRS[initial]
                    new_point = (start[0] + dx, start[1] + dy)
                    if self.region_size(new_point) <= small_region:
                        # reject this move: keep searching for another path
                        # (mirrors Java returning false in shouldExit)
                        continue
                return initial
            for name, nxt in self.adjacent(cur).items():
                if nxt in seen:
                    continue
                if not self.movable(nxt, True):
                    continue
                seen.add(nxt)
                q.append((nxt, initial if initial is not None else name))
        return None

    # -- high level moves ---------------------------------------------------
    def go_to_food(self, head):
        return self.find_path(list(self.food), head)

    def find_heads(self):
        heads = []
        for s in self.snakes:
            if s["id"] == self.you_id:
                continue
            body = self._body(s)
            heads.extend(self.adjacent(body[0]).values())
            heads.append(body[0])
        return heads

    def go_to_attack(self, head):
        return self.find_path(self.find_heads(), head)

    def go_to_tail(self, head):
        body = self._body(self.you)
        for i in range(len(body) - 1, 0, -1):
            move = self.find_path(list(self.adjacent(body[i]).values()),
                                  head, check_box=False)
            if move is not None:
                return move
        return None

    def go_to_fallback(self, head):
        moves = []
        for name, p in self.adjacent(head).items():
            if self.movable(p, False):
                moves.append((name, p))
        if not moves:
            return FALLBACK
        for name, p in moves:
            if self.is_food(p):
                return name
        return moves[0][0]

    # -- entry --------------------------------------------------------------
    def decide(self):
        head = (self.you["head"]["x"], self.you["head"]["y"])
        health = self.you.get("health", 100)
        longest = self.longest_other()

        if health <= HUNGER_ZONE:
            hungry = True
        elif longest is None or self._you_length() > longest:
            hungry = False  # ATTACK
        else:
            hungry = True

        move = None
        if hungry:
            move = self.go_to_food(head)
            if move is None:
                move = self.go_to_attack(head)
            if move is None:
                move = self.go_to_tail(head)
        else:
            move = self.go_to_attack(head)
            if move is None:
                move = self.go_to_food(head)
            if move is None:
                move = self.go_to_tail(head)

        if move is None:
            move = self.go_to_fallback(head)
        return move


def _safe_fallback(game_state):
    """Absolute last resort: any in-bounds, non-body move (tails enterable)."""
    try:
        you = game_state["you"]
        b = game_state["board"]
        w, h = b["width"], b["height"]
        head = (you["head"]["x"], you["head"]["y"])
        # occupied non-tail body cells
        occupied = set()
        for s in b["snakes"]:
            body = [(c["x"], c["y"]) for c in s["body"]]
            n = len(body)
            for i, cell in enumerate(body):
                if i == n - 1 and n > 1 and s.get("health", 0) != 100:
                    continue  # tail is enterable
                occupied.add(cell)
        for name, (dx, dy) in DIRS.items():
            nx, ny = head[0] + dx, head[1] + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in occupied:
                return name
    except Exception:
        pass
    return FALLBACK


def move(game_state):
    try:
        board = Board(game_state)
        result = board.decide()
        if result not in DIRS:
            result = _safe_fallback(game_state)
        return {"move": result}
    except Exception:
        return {"move": _safe_fallback(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
