"""
Port of zacpez/scape-goat (Go Battlesnake) to CodeClash arena format.

The original uses the OLD Battlesnake API (top-left origin, y increases
downward). The CodeClash arena uses the CURRENT v1 API (bottom-left origin,
y increases upward). The strategy is reproduced faithfully; all direction /
coordinate reasoning is remapped from the original old-API semantics to v1.

Original strategy (snake/*.go, ComputeDirection):
  1. Build a set of directions to EXCLUDE:
       - directions that would move off the board edge (EdgeDirection)
       - the neck direction (NeckDirection)
       - the sentinel NONE
  2. choices = ALL_DIRECTIONS - excludeChoices
  3. For each remaining choice, PredictNextDirection produces "dumb" ideas:
       - if health <= HUNGER (75): FindFoodDirection(dir)  (odd axis-mixing
         food heuristic; returns the direction itself when a food matches,
         marking it "dumb", else NONE)
       - else: SimpleAvoidance(dir) (returns the direction when it would step
         onto ANY snake body cell, marking it "dumb", else NONE)
  4. dumbIdeas are then excluded, but the original re-diffs against the FULL
     ALL_DIRECTIONS set (choices = ALL_DIRECTIONS - dumbIdeas), so edge/neck
     directions get re-introduced -- reproduced faithfully below.
  5. If exactly one choice remains, take it; otherwise pick a
     time-nanosecond-modulo "random" choice.

A robustness safety net wraps the whole thing: if the reproduced choice is
illegal (out of bounds or into a snake body, tails excepted) we fall back to
any legal move, and never crash.
"""

import time
import random

# --- Direction semantics ---------------------------------------------------
# We reason internally in v1 coordinates (bottom-left origin, y up):
#   up = y+1, down = y-1, left = x-1, right = x+1
UP = "up"
RIGHT = "right"
DOWN = "down"
LEFT = "left"
NONE = "none"

# Original DirectionChoices order: UP, RIGHT, DOWN, LEFT, NONE
DIRECTION_CHOICES = [UP, RIGHT, DOWN, LEFT, NONE]

HUNGER = 75

_V1_DELTA = {UP: (0, 1), DOWN: (0, -1), LEFT: (-1, 0), RIGHT: (1, 0)}


def info():
    return {
        "apiversion": "1",
        "author": "zacpez",
        "color": "#69604D",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return


def end(game_state):
    return


# --- Helpers (ported, remapped to v1) --------------------------------------

def _difference(a, b):
    """Set difference A - B, preserving order of A (like Go Difference)."""
    bset = set(b)
    return [item for item in a if item not in bset]


def _edge_direction(head, width, height):
    """
    Original EdgeDirection (old API, y-down):
      X==0        -> exclude LEFT
      X==width-1  -> exclude RIGHT
      Y==0        -> exclude UP     (top edge in old API)
      Y==height-1 -> exclude DOWN   (bottom edge in old API)
    In v1 (y-up), the top edge is Y==height-1 and bottom is Y==0, so the
    directions that leave the board are:
      X==0        -> LEFT
      X==width-1  -> RIGHT
      Y==height-1 -> UP
      Y==0        -> DOWN
    (Same physical meaning: exclude moves that step off the board.)
    """
    edges = []
    if head["x"] == 0:
        edges.append(LEFT)
    if head["x"] == width - 1:
        edges.append(RIGHT)
    if head["y"] == height - 1:
        edges.append(UP)
    if head["y"] == 0:
        edges.append(DOWN)
    return edges


def _neck_direction(body):
    """
    Original NeckDirection (old API):
      dx = head.X - neck.X ; dy = head.Y - neck.Y
      dx>0 -> LEFT ; dx<0 -> RIGHT ; dy<0 -> DOWN ; else UP
    This returns the direction pointing back toward the neck (the reverse of
    travel), so the snake won't turn back on itself. In v1 the y axis flips,
    so we recompute the "back toward neck" direction in v1 coords directly.
    """
    if len(body) < 2:
        return UP
    head = body[0]
    neck = body[1]
    dx = head["x"] - neck["x"]
    dy = head["y"] - neck["y"]
    if dx > 0:
        return LEFT
    if dx < 0:
        return RIGHT
    if dy < 0:  # neck is above head in v1 -> back is UP
        return UP
    if dy > 0:  # neck is below head in v1 -> back is DOWN
        return DOWN
    return UP


def _find_food_direction(head, food, direction):
    """
    Original FindFoodDirection (old API axis-mixing heuristic), faithfully
    reproduced but with the y comparisons flipped for v1 y-up:

      old: DOWN & food.X > head.X -> DOWN     (v1: DOWN unchanged, X compare)
      old: UP   & food.X < head.X -> UP
      old: RIGHT& food.Y > head.Y -> RIGHT    (old y-down; v1 flips to <)
      old: LEFT & food.Y < head.Y -> LEFT     (old y-down; v1 flips to >)
    Returns `direction` when a food matches (marking it "dumb"), else NONE.
    """
    if not food:
        return NONE
    for f in food:
        if direction == DOWN and f["x"] > head["x"]:
            return DOWN
        if direction == UP and f["x"] < head["x"]:
            return UP
        if direction == RIGHT and f["y"] < head["y"]:
            return RIGHT
        if direction == LEFT and f["y"] > head["y"]:
            return LEFT
    return NONE


def _simple_avoidance(head, snakes, direction):
    """
    Original SimpleAvoidance: step one cell in `direction`; if that cell is on
    ANY snake body part, return `direction` (mark it dumb), else NONE.
    Remapped to v1 deltas.
    """
    dx, dy = _V1_DELTA.get(direction, (0, 0))
    nx = head["x"] + dx
    ny = head["y"] + dy
    for other in snakes:
        for part in other.get("body", []):
            if part["x"] == nx and part["y"] == ny:
                return direction
    return NONE


def _predict_next_direction(you, board, direction):
    head = you["body"][0]
    if you.get("health", 100) <= HUNGER:
        return _find_food_direction(head, board.get("food", []), direction)
    return _simple_avoidance(head, board.get("snakes", []), direction)


def _dumb_directions(you, board, directions):
    dumb = []
    for d in directions:
        dumb.append(_predict_next_direction(you, board, d))
    return dumb


def _simple_random_choice(max_choice):
    # Original: int(time.Now().UnixNano()) % maxChoice
    return int(time.time_ns()) % max_choice


def _compute_direction(you, board):
    body = you["body"]
    head = body[0]
    width = board["width"]
    height = board["height"]

    exclude = _edge_direction(head, width, height)
    exclude.append(_neck_direction(body))
    exclude.append(NONE)

    choices = _difference(DIRECTION_CHOICES, exclude)

    dumb = _dumb_directions(you, board, choices)
    # Faithful to original: re-diff against the FULL choice set (re-adds
    # edge/neck), then remove dumb ideas.
    choices = _difference(DIRECTION_CHOICES, dumb)

    count = len(choices)
    if count == 0:
        return NONE
    if count == 1:
        return choices[0]
    return choices[_simple_random_choice(count)]


# --- Robustness safety net -------------------------------------------------

def _legal_moves(you, board):
    """Return v1 directions that stay in bounds and don't hit a snake body
    (tails are enterable)."""
    head = you["body"][0]
    width = board["width"]
    height = board["height"]

    occupied = set()
    for snake in board.get("snakes", []):
        sbody = snake.get("body", [])
        n = len(sbody)
        for i, part in enumerate(sbody):
            # Tail cell (last) is enterable unless the snake just ate (then
            # tail won't move). We conservatively treat tails as enterable.
            if i == n - 1 and n > 1:
                continue
            occupied.add((part["x"], part["y"]))

    legal = []
    for d, (dx, dy) in _V1_DELTA.items():
        nx = head["x"] + dx
        ny = head["y"] + dy
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            continue
        if (nx, ny) in occupied:
            continue
        legal.append(d)
    return legal


def _is_legal(direction, you, board):
    if direction not in _V1_DELTA:
        return False
    return direction in _legal_moves(you, board)


def move(game_state):
    try:
        you = game_state["you"]
        board = game_state["board"]

        chosen = _compute_direction(you, board)

        if _is_legal(chosen, you, board):
            return {"move": chosen}

        # Safety net: pick any legal move, preferring the computed one's
        # legality above; otherwise avoid bodies and edges.
        legal = _legal_moves(you, board)
        if legal:
            return {"move": random.choice(legal)}

        # No legal move: at least stay in bounds if possible.
        head = you["body"][0]
        width = board["width"]
        height = board["height"]
        for d, (dx, dy) in _V1_DELTA.items():
            nx = head["x"] + dx
            ny = head["y"] + dy
            if 0 <= nx < width and 0 <= ny < height:
                return {"move": d}
        return {"move": "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
