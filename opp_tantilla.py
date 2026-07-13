"""
Port of MorganConrad/tantilla (JavaScript, node/micro) to a self-contained
Python main.py against the current Battlesnake v1 API.

Original strategy (faithful):
  1. Enumerate 4 possible moves from the head.
  2. Eliminate moves that are off-board, hit our own body, hit another snake's
     body (an enemy's *tail* square is enterable), or land on a square
     threatened by a larger-or-equal enemy snake head.
     - If fewer than 2 moves survive, take the survivor, else an "emergency"
       move that ignores the threat filter.
  3. Choose a strategy:
     - health < reallyHungry (20): head to closest food, weighted by
       degrees-of-freedom around the food: score = (dist+1)/(1+dof), low best.
     - health < somewhatHungry (40): (TBD in original) -> chaseYourTail.
     - otherwise: chaseYourTail -> score = avoidFood * distToTail / (1+dof),
       low best, where avoidFood=2 on food else 1.
  4. Among tied-best moves, pick index = turn % len.

Coordinate remap: the original API is y-down (up=y-1, down=y+1). The v1 API is
y-up (up=y+1, down=y-1). The neighbor *geometry* is orientation independent, so
only the direction *labels* must match v1. possibleMoves() below uses v1 labels.
"""

# ---- config.js ----
CONFIG = {
    "color": "#00FFAA",
    "name": "Tantilla",
    "reallyHungry": 20,
    "somewhatHungry": 40,
}

ENEMY_CHARS = "abcdefghijklmnopqrstuvwxyz"


def same_points(p1, p2):
    return p1["x"] == p2["x"] and p1["y"] == p2["y"]


def city_blocks(p1, p2):
    return abs(p1["x"] - p2["x"]) + abs(p1["y"] - p2["y"])


def snake_head(snake):
    return snake["body"][0]


def snake_tail(snake):
    return snake["body"][-1]


def possible_moves(p):
    # v1 semantics: up=y+1, down=y-1, left=x-1, right=x+1
    return [
        {"dir": "right", "x": p["x"] + 1, "y": p["y"], "score": 0.0},
        {"dir": "left",  "x": p["x"] - 1, "y": p["y"], "score": 0.0},
        {"dir": "up",    "x": p["x"], "y": p["y"] + 1, "score": 0.0},
        {"dir": "down",  "x": p["x"], "y": p["y"] - 1, "score": 0.0},
    ]


class Board:
    def __init__(self, data):
        self.ur_data = data
        self.ur_board = data["board"]
        self.you = data["you"]
        self.grid = self._create_grid()

    # grid[x][y]: ' ' empty, 'a'-'z' enemy snake, 'F' food, 'M' me
    def _create_grid(self):
        w = self.ur_board["width"]
        h = self.ur_board["height"]
        grid = [[" "] * h for _ in range(w)]

        for enemy, snake in enumerate(self.ur_board["snakes"]):
            ch = ENEMY_CHARS[enemy] if enemy < len(ENEMY_CHARS) else "z"
            for p in snake["body"]:
                if 0 <= p["x"] < w and 0 <= p["y"] < h:
                    grid[p["x"]][p["y"]] = ch

        for p in self.you["body"]:  # overwrites the snake char for me
            if 0 <= p["x"] < w and 0 <= p["y"] < h:
                grid[p["x"]][p["y"]] = "M"

        for p in self.ur_board["food"]:
            if 0 <= p["x"] < w and 0 <= p["y"] < h:
                grid[p["x"]][p["y"]] = "F"

        return grid

    def is_on_board(self, p):
        return (0 <= p["x"] < self.ur_board["width"] and
                0 <= p["y"] < self.ur_board["height"])

    def _cell(self, p):
        return self.grid[p["x"]][p["y"]]

    def is_empty(self, p):
        return self._cell(p) == " "

    def is_food(self, p):
        return self._cell(p) == "F"

    def is_me(self, p):
        return self._cell(p) == "M"

    def hostile_snake_at(self, p):
        # returns the enemy snake occupying p, unless p is that snake's tail
        c = self._cell(p)
        n = ord(c[0]) - ord("a")
        if 0 <= n < 26 and n < len(self.ur_board["snakes"]):
            hostile = self.ur_board["snakes"][n]
            if same_points(p, snake_tail(hostile)):
                return None
            return hostile
        return None

    def degrees_of_freedom(self, p):
        # how many "safe" (empty or food) neighbors are on-board (0-4)
        on_board = [m for m in possible_moves(p) if self.is_on_board(m)]
        empties = sum(1 for m in on_board if self.is_empty(m))
        food = sum(1 for m in on_board if self.is_food(m))
        return empties + food

    def distance_from_center(self, p):
        center = {"x": self.ur_board["width"] / 2,
                  "y": self.ur_board["height"] / 2}
        return city_blocks(p, center)

    def enemy_snakes(self, bigger=False, smaller=False):
        my_id = self.you["id"]
        my_len = len(self.you["body"])
        enemies = [s for s in self.ur_board["snakes"] if s["id"] != my_id]
        if bigger:
            enemies = [s for s in enemies if len(s["body"]) >= my_len]
        elif smaller:
            enemies = [s for s in enemies if len(s["body"]) < my_len]
        return enemies

    def threatened_points(self, bigger=False, smaller=False):
        threatened = []
        for snake in self.enemy_snakes(bigger=bigger, smaller=smaller):
            threatened.extend(possible_moves(snake_head(snake)))
        return threatened


def add_distances(from_point, to_points, key="distance"):
    for p in to_points:
        p[key] = city_blocks(from_point, p)
    return to_points


def contains_point(points, point):
    return any(same_points(p, point) for p in points)


def sort_and_trim(possibles, key="score"):
    possibles.sort(key=lambda p: p[key])
    best = possibles[0][key]
    return [p for p in possibles if p[key] == best]


def really_hungry(possibles, board):
    for p in possibles:
        foods = add_distances(p, [dict(f) for f in board.ur_board["food"]])
        for f in foods:
            dof = 1.0 + board.degrees_of_freedom(f)
            f["score"] = (f["distance"] + 1) / dof
        if foods:
            foods.sort(key=lambda a: a["score"])
            p["score"] = foods[0]["score"]
        else:
            p["score"] = 0.0
    return sort_and_trim(possibles)


def chase_your_tail(possibles, board):
    tail = snake_tail(board.you)
    for p in possibles:
        distance_to_tail = city_blocks(tail, p) + 1
        dof = 1.0 + board.degrees_of_freedom(p)
        avoid_food = 2 if board.is_food(p) else 1
        like_the_center = 1
        p["score"] = like_the_center * avoid_food * distance_to_tail / dof
    return sort_and_trim(possibles)


def somewhat_hungry(possibles, board):
    return chase_your_tail(possibles, board)


def calculate_move(inputs):
    board = Board(inputs)
    threatened = board.threatened_points(bigger=True)

    moves = possible_moves(inputs["you"]["body"][0])
    moves = [p for p in moves if board.is_on_board(p)]
    moves = [p for p in moves if not board.is_me(p)]
    moves = [p for p in moves if not board.hostile_snake_at(p)]

    emergency = moves[0] if moves else None
    moves = [p for p in moves if not contains_point(threatened, p)]

    if len(moves) < 2:
        if moves:
            return moves[0]
        if emergency is not None:
            return emergency
        # fully trapped: return a legal-ish fallback
        return {"dir": "up"}

    health = inputs["you"]["health"]
    if health < CONFIG["reallyHungry"]:
        moves = really_hungry(moves, board)
    elif health < CONFIG["somewhatHungry"]:
        moves = somewhat_hungry(moves, board)
    else:
        moves = chase_your_tail(moves, board)

    idx = inputs["turn"] % len(moves)
    return moves[idx]


# ---- v1 API handlers ----

def info():
    return {
        "apiversion": "1",
        "author": "MorganConrad",
        "color": CONFIG["color"],
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def move(game_state):
    try:
        chosen = calculate_move(game_state)
        return {"move": chosen["dir"]}
    except Exception:
        # Robust fallback: any in-bounds move not into a snake body (tails ok).
        try:
            you = game_state["you"]
            head = you["body"][0]
            board = game_state["board"]
            w, h = board["width"], board["height"]
            blocked = set()
            for s in board["snakes"]:
                body = s["body"]
                for i, seg in enumerate(body):
                    if i == len(body) - 1:  # tail is enterable
                        continue
                    blocked.add((seg["x"], seg["y"]))
            cands = [
                ("up", head["x"], head["y"] + 1),
                ("down", head["x"], head["y"] - 1),
                ("left", head["x"] - 1, head["y"]),
                ("right", head["x"] + 1, head["y"]),
            ]
            for d, x, y in cands:
                if 0 <= x < w and 0 <= y < h and (x, y) not in blocked:
                    return {"move": d}
            for d, x, y in cands:
                if 0 <= x < w and 0 <= y < h:
                    return {"move": d}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
