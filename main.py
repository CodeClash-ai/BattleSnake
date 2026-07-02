# -*- coding: utf-8 -*-
# Port of TheApX "The Very Hungry Caterpillar" (battlesnake-hungry, C++)
# to CodeClash Battlesnake v1 API, pure stdlib Python.
#
# Faithful reimplementation of the original strategy:
#   - Pre-compute a board matrix (1-D array indexed y*W+x).
#   - Mark all snake body cells EXCEPT tails as "snake body" (unreachable).
#   - Multi-source BFS from every food to compute distance-to-closest-food
#     for every reachable cell.
#   - Compare all 4 moves (order: Left, Right, Up, Down) starting from an
#     "Unknown" best, using the same rule priority as MoveComparator::IsBetter:
#       1. Never step on own neck (if length >= 2).
#       2. Never go out of bounds.
#       3. Never step on a snake body.
#       4. Prefer a move from which food is reachable over one that isn't.
#       5. Among reachable, prefer the move closer to food.
#       6. Otherwise keep the previously found best (prefer old).

from collections import deque

# Special matrix values, chosen so they compare with real step counts.
MATRIX_SNAKE_BODY = 10 ** 18          # furthest from any food; avoid if possible
MATRIX_UNINITIALIZED = 10 ** 18 - 1   # no path from food; worse than any food

# Coord system: (0,0) bottom-left. up=y+1, down=y-1, left=x-1, right=x+1.
_DIRS = {
    "left": (-1, 0),
    "right": (1, 0),
    "up": (0, 1),
    "down": (0, -1),
}
# Original tries moves in this order: Left, Right, Up, Down.
_MOVE_ORDER = ["left", "right", "up", "down"]


def info():
    return {
        "apiversion": "1",
        "author": "TheApX",
        "color": "#2e8244",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


class MoveComparator:
    def __init__(self, board, you):
        self.width = int(board["width"])
        self.height = int(board["height"])
        self.snakes = board.get("snakes", []) or []
        self.food = board.get("food", []) or []
        self.you = you

        head = you["body"][0]
        self.head = (int(head["x"]), int(head["y"]))
        self.length = int(you.get("length", len(you["body"])))

        # Pre-computed next points per move.
        self.move_points = {}
        for m, (dx, dy) in _DIRS.items():
            self.move_points[m] = (self.head[0] + dx, self.head[1] + dy)

        # neck = second body segment (if any)
        self.neck = None
        if len(you["body"]) >= 2:
            n = you["body"][1]
            self.neck = (int(n["x"]), int(n["y"]))

        self._init_board_matrix()

    def _idx(self, x, y):
        return y * self.width + x

    def _steps(self, p):
        return self.matrix[self._idx(p[0], p[1])]

    def _is_out_of_bounds(self, p):
        x, y = p
        return x < 0 or y < 0 or x >= self.width or y >= self.height

    def _init_board_matrix(self):
        self.matrix = [MATRIX_UNINITIALIZED] * (self.width * self.height)
        self._mark_snake_bodies()
        self._compute_steps_from_food()

    def _mark_snake_bodies(self):
        # Mark all body cells except the tail (which moves next turn, so it's
        # enterable). Mirrors the original prev/next iteration: it marks every
        # segment except the last one.
        for snake in self.snakes:
            body = snake.get("body", []) or []
            for i in range(len(body) - 1):  # skip the tail (last element)
                seg = body[i]
                x, y = int(seg["x"]), int(seg["y"])
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.matrix[self._idx(x, y)] = MATRIX_SNAKE_BODY

    def _compute_steps_from_food(self):
        bfs = deque()
        for f in self.food:
            fx, fy = int(f["x"]), int(f["y"])
            if not (0 <= fx < self.width and 0 <= fy < self.height):
                continue
            # Food sitting on a marked body cell: still treat as distance 0
            # source (matches original which sets steps(food)=0 unconditionally).
            self.matrix[self._idx(fx, fy)] = 0
            bfs.append((fx, fy))

        while bfs:
            cx, cy = bfs.popleft()
            cur_steps = self.matrix[self._idx(cx, cy)]
            for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if self._is_out_of_bounds((nx, ny)):
                    continue
                v = self.matrix[self._idx(nx, ny)]
                if v == MATRIX_SNAKE_BODY:
                    continue
                if v != MATRIX_UNINITIALIZED:
                    continue  # already has a (lower) distance
                self.matrix[self._idx(nx, ny)] = cur_steps + 1
                bfs.append((nx, ny))

    def is_better(self, move, best):
        # move / best are direction strings or None (== "Unknown").
        if move is None:
            return False
        if best is None:
            return True

        mp = self.move_points[move]
        bp = self.move_points[best]

        # Don't break your neck.
        if self.length >= 2 and self.neck is not None:
            if mp == self.neck:
                return False
            if bp == self.neck:
                return True

        # Out of bounds.
        if self._is_out_of_bounds(mp):
            return False
        if self._is_out_of_bounds(bp):
            return True

        ms = self._steps(mp)
        bs = self._steps(bp)

        # Snake body.
        if ms == MATRIX_SNAKE_BODY:
            return False
        if bs == MATRIX_SNAKE_BODY:
            return True

        # Prefer where food is reachable.
        if ms == MATRIX_UNINITIALIZED and bs != MATRIX_UNINITIALIZED:
            return False
        if ms != MATRIX_UNINITIALIZED and bs == MATRIX_UNINITIALIZED:
            return True

        # Both reachable: prefer closer to food.
        if ms != MATRIX_UNINITIALIZED and bs != MATRIX_UNINITIALIZED:
            if ms < bs:
                return True
            if ms > bs:
                return False

        # Equally good: keep old best.
        return False


def _fallback_move(game_state):
    # Guarantee an in-bounds move that doesn't hit a snake body (tails ok).
    try:
        board = game_state["board"]
        you = game_state["you"]
        w = int(board["width"])
        h = int(board["height"])
        head = you["body"][0]
        hx, hy = int(head["x"]), int(head["y"])

        blocked = set()
        for snake in board.get("snakes", []) or []:
            body = snake.get("body", []) or []
            for i in range(len(body) - 1):  # tails enterable
                seg = body[i]
                blocked.add((int(seg["x"]), int(seg["y"])))

        for m in _MOVE_ORDER:
            dx, dy = _DIRS[m]
            nx, ny = hx + dx, hy + dy
            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                continue
            if (nx, ny) in blocked:
                continue
            return m
    except Exception:
        pass
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        you = game_state["you"]
        comparator = MoveComparator(board, you)

        best = None  # "Unknown"
        for m in _MOVE_ORDER:
            if comparator.is_better(m, best):
                best = m

        if best is None:
            best = _fallback_move(game_state)
        return {"move": best}
    except Exception:
        return {"move": _fallback_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
