"""Sisiutl - an aggressive Battlesnake, ported from MorganConrad/Sisiutl (JS).

Original strategy (from README + index.js/Board.js):
 1. Don't go outside the ring or hit other snake bodies (including yourself)
 2. If health is low (<20), go get food
 3. Otherwise, look for smaller competitors to attack
 4. If no smaller competitors, go eat food
 5. If moving towards a snake/food looks unsafe, move in a "safe" direction

The original uses the OLD Battlesnake API with a top-left origin (y increases
downward: up=y-1, down=y+1). This port remaps everything to the CURRENT v1 API
with a bottom-left origin (up=y+1, down=y-1) while preserving the strategy.
"""

DIRECTIONS = ['up', 'right', 'down', 'left']


def info():
    return {
        "apiversion": "1",
        "author": "MorganConrad",
        "color": "#269272",
        "head": "regular",
        "tail": "regular",
    }


def start(game_state):
    return {}


def end(game_state):
    return {}


# ---- geometry helpers (from Board.js) ----

def city_blocks_between(p1, p2):
    return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])


def possible_moves(p):
    # v1 API: bottom-left origin. up=y+1, down=y-1, left=x-1, right=x+1.
    return {
        "up":    {"dir": "up",    "x": p["x"],     "y": p["y"] + 1, "ok": True},
        "right": {"dir": "right", "x": p["x"] + 1, "y": p["y"],     "ok": True},
        "down":  {"dir": "down",  "x": p["x"],     "y": p["y"] - 1, "ok": True},
        "left":  {"dir": "left",  "x": p["x"] - 1, "y": p["y"],     "ok": True},
    }


class Board:
    def __init__(self, game_state):
        self.board = game_state["board"]
        self.you = game_state["you"]
        self.width = self.board["width"]
        self.height = self.board["height"]
        # grid[x][y]: ' ' empty, 'S' other snake body, 'M' my body, 'F' food
        self.grid = self._create_grid()

    def _create_grid(self):
        grid = [[' ' for _ in range(self.height)] for _ in range(self.width)]
        for snake in self.board.get("snakes", []):
            for pt in snake.get("body", []):
                if 0 <= pt["x"] < self.width and 0 <= pt["y"] < self.height:
                    grid[pt["x"]][pt["y"]] = 'S'
        for pt in self.you.get("body", []):
            if 0 <= pt["x"] < self.width and 0 <= pt["y"] < self.height:
                grid[pt["x"]][pt["y"]] = 'M'
        for pt in self.board.get("food", []):
            if 0 <= pt["x"] < self.width and 0 <= pt["y"] < self.height:
                grid[pt["x"]][pt["y"]] = 'F'
        return grid

    def is_on_board(self, p):
        return 0 <= p["x"] < self.width and 0 <= p["y"] < self.height

    def can_move_to(self, p):
        # faithful: only empty (' ') or food ('F') cells are enterable
        c = self.grid[p["x"]][p["y"]]
        return c == ' ' or c == 'F'

    def find_food(self, p):
        food = list(self.board.get("food", []))
        if len(food) > 1:
            food.sort(key=lambda f: city_blocks_between(p, f))
        return food

    def edible_snakes(self, p):
        my_length = len(self.you["body"])
        edibles = []
        for snake in self.board.get("snakes", []):
            # faithful: any snake strictly shorter than us (self excluded since
            # its length equals ours, never strictly less)
            if len(snake.get("body", [])) < my_length:
                edibles.append(snake)
        if len(edibles) > 1:
            edibles.sort(key=lambda s: city_blocks_between(p, s["body"][0]))
        return edibles

    def guess_snakes_next_position(self, snake):
        # simplistic: extrapolate head from head-neck delta
        body = snake["body"]
        head = body[0]
        seg1 = body[1] if len(body) > 1 else body[0]
        dx = head["x"] - seg1["x"]
        dy = head["y"] - seg1["y"]
        return {"x": head["x"] + dx, "y": head["y"] + dy}

    def best_routes(self, frm, to):
        # Prefer axis with larger absolute delta. Remapped to v1 (up=y+1).
        directions = []
        dx = to["x"] - frm["x"]
        dy = to["y"] - frm["y"]
        if abs(dx) >= abs(dy):  # horizontal preferred
            directions.append("right" if dx > 0 else "left")
            if dy:
                directions.append("up" if dy > 0 else "down")
        else:  # vertical preferred
            directions.append("up" if dy > 0 else "down")
            if dx:
                directions.append("right" if dx > 0 else "left")
        return directions


def try_to_kill(board, my_head, moves):
    for snake in board.edible_snakes(my_head):
        guess = board.guess_snakes_next_position(snake)
        for r in board.best_routes(my_head, guess):
            if moves[r]["ok"]:
                return moves[r]
    return None


def try_to_eat(board, my_head, moves):
    for f in board.find_food(my_head):
        for r in board.best_routes(my_head, f):
            if moves[r]["ok"]:
                return moves[r]
    return None


def first_available_move(moves):
    for d in DIRECTIONS:
        if moves[d]["ok"]:
            return moves[d]
    return None


def _emergency_move(game_state):
    """Last-resort: any in-bounds move not into a snake body (tails enterable)."""
    try:
        you = game_state["you"]
        board = game_state["board"]
        w, h = board["width"], board["height"]
        head = you["body"][0]
        # occupied cells; tails are enterable (drop last segment of each snake)
        occupied = set()
        for snake in board.get("snakes", []):
            body = snake.get("body", [])
            for i, pt in enumerate(body):
                if i == len(body) - 1:
                    continue  # tail vacates
                occupied.add((pt["x"], pt["y"]))
        cand = possible_moves(head)
        for d in DIRECTIONS:
            m = cand[d]
            if 0 <= m["x"] < w and 0 <= m["y"] < h and (m["x"], m["y"]) not in occupied:
                return d
    except Exception:
        pass
    return "up"


def move(game_state):
    try:
        my_head = game_state["you"]["body"][0]
        board = Board(game_state)

        moves = possible_moves(my_head)
        for d in DIRECTIONS:
            m = moves[d]
            m["ok"] = board.is_on_board(m) and board.can_move_to(m)

        chosen = None

        # if low health, look for food first
        if game_state["you"]["health"] < 20:
            chosen = try_to_eat(board, my_head, moves)

        # otherwise, attack!
        if not chosen:
            chosen = try_to_kill(board, my_head, moves)

        # no good attacking moves, let's eat
        if not chosen:
            chosen = try_to_eat(board, my_head, moves)

        # no good eating moves, just make a "safe" move
        if not chosen:
            chosen = first_available_move(moves)

        if chosen:
            return {"move": chosen["dir"]}

        # we are in bad shape: use robust emergency fallback
        return {"move": _emergency_move(game_state)}
    except Exception:
        return {"move": _emergency_move(game_state)}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
