"""BombasticBob - a faithful Python port of coreyja/battlesnake-rs bombastic_bob.

Strategy: pick a RANDOM "reasonable" move. A move is reasonable if it does not
go off the board, does not enter any snake's body, and does not step into a
hazard cell that would kill the snake. If no reasonable move exists, fall back
to any random move that does not immediately reverse into our own neck.
This reproduces `random_reasonable_move_for_each_snake` from
battlesnake-game-types (wire_representation), restricted to our snake.
"""

import random

# Move order matching Rust Move::all() == [Up, Down, Left, Right]
MOVES = [
    ("up", (0, 1)),
    ("down", (0, -1)),
    ("left", (-1, 0)),
    ("right", (1, 0)),
]


def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#AA66CC",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def move(game_state):
    try:
        return {"move": _choose(game_state)}
    except Exception:
        return {"move": "right"}


def _choose(game_state):
    board = game_state["board"]
    width = board["width"]
    height = board["height"]
    me = game_state["you"]
    head = me["head"]
    hx, hy = head["x"], head["y"]

    is_wrapped = game_state.get("game", {}).get("ruleset", {}).get("name") == "wrapped"

    # Collect every occupied body cell across all snakes.
    body_cells = set()
    for s in board["snakes"]:
        for seg in s["body"]:
            body_cells.add((seg["x"], seg["y"]))

    hazard_cells = set((h["x"], h["y"]) for h in board.get("hazards", []))
    hazard_damage = (
        game_state.get("game", {})
        .get("ruleset", {})
        .get("settings", {})
        .get("hazardDamagePerTurn", 14)
    )
    health = me["health"]

    reasonable = []
    for name, (dx, dy) in MOVES:
        nx, ny = hx + dx, hy + dy
        if is_wrapped:
            nx %= width
            ny %= height

        off_board = nx < 0 or nx >= width or ny < 0 or ny >= height
        in_body = (nx, ny) in body_cells
        deadly_hazard = (nx, ny) in hazard_cells and hazard_damage >= health

        if not (off_board or in_body or deadly_hazard):
            reasonable.append(name)

    if reasonable:
        return random.choice(reasonable)

    # Fallback: any move that does not reverse into our own neck (body[1]).
    body = me["body"]
    neck = body[1] if len(body) > 1 else None
    fallback = []
    for name, (dx, dy) in MOVES:
        nx, ny = hx + dx, hy + dy
        if neck is not None and nx == neck["x"] and ny == neck["y"]:
            continue
        fallback.append(name)

    if fallback:
        return random.choice(fallback)

    return "right"


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
