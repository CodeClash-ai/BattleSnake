"""Port of amphibious_arthur (coreyja/battlesnake-rs) to CodeClash v1 API.

Faithful reimplementation of battlesnake-rs/src/amphibious_arthur.rs.

Original `score(game_state, coor, times_to_recurse)`:
  const PREFERRED_HEALTH = 80
  - if position_is_snake_body(coor)                    -> 0
        (position_is_snake_body = ANY snake body cell, INCLUDING tail)
  - if !is_alive(you)  (health == 0)                   -> 0
  - current_score = PREFERRED_HEALTH - |health - PREFERRED_HEALTH|
        (health is read from the game state and is NEVER decremented by the
         recursion: move_to / opponent_sprawl only mutate snake bodies, so
         current_score is identical at every recursion depth)
  - if times_to_recurse == 0                           -> current_score
  - else current_score + (sum over neighbors(coor) of
        score(move_to_and_opponent_sprawl(coor), neighbor, recurse-1)) / 2

make_move: possible_moves(head) [in-bounds only, order Up,Down,Left,Right],
  pick max_by_key(score(game, coor, RECURSION_LIMIT)). Rust `max_by_key`
  returns the LAST element among ties. Default RECURSION_LIMIT = 5.
  No candidates -> "up" (stuck_response).

NOTE on move_to_and_opponent_sprawl: the original clones the game, moves your
head to `coor`, then (due to a filter on `s.id == self.you.id`) grows YOUR OWN
snake by appending a RANDOM neighbor of your head each recursion. This is
non-deterministic (rand::thread_rng) and cannot be reproduced bit-for-bit. We
therefore recurse over the *unmodified* board (health constant, bodies as
given), which matches the deterministic, health-driven core of the heuristic.
"""

PREFERRED_HEALTH = 80
RECURSION_LIMIT = 5  # original default (env RECURSION_LIMIT, else 5)

# Move::all() order in battlesnake-game-types: Up, Down, Left, Right.
DIRS = [
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
        "head": "trans-rights-scarf",
        "tail": "swirl",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _body_set(board):
    """position_is_snake_body: every cell of every snake body, tail INCLUDED."""
    occ = set()
    for s in board.get("snakes", []):
        for c in s.get("body", []):
            occ.add((c["x"], c["y"]))
    return occ


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _neighbors(x, y, w, h):
    """possible_moves(coor): in-bounds neighbors, order Up, Down, Left, Right."""
    out = []
    for _mv, (dx, dy) in DIRS:
        nx, ny = x + dx, y + dy
        if _in_bounds(nx, ny, w, h):
            out.append((nx, ny))
    return out


def _score(coor, health, occupied, w, h, times_to_recurse):
    """Faithful reimplementation of the Rust `score` function.

    health is passed through unchanged on recursion (matches original).
    """
    if coor in occupied:
        return 0
    if health == 0:  # !is_alive
        return 0

    current_score = PREFERRED_HEALTH - abs(health - PREFERRED_HEALTH)

    if times_to_recurse == 0:
        return current_score

    recursed_score = 0
    for nb in _neighbors(coor[0], coor[1], w, h):
        recursed_score += _score(
            nb, health, occupied, w, h, times_to_recurse - 1
        )

    return current_score + recursed_score // 2


def move(game_state):
    try:
        board = game_state["board"]
        w = board["width"]
        h = board["height"]
        you = game_state["you"]
        head = you["head"]
        hx, hy = head["x"], head["y"]
        health = you.get("health", PREFERRED_HEALTH)

        occupied = _body_set(board)

        # possible_moves(head): in-bounds neighbors, order Up, Down, Left, Right
        candidates = []
        for mv, (dx, dy) in DIRS:
            nx, ny = hx + dx, hy + dy
            if _in_bounds(nx, ny, w, h):
                candidates.append((mv, (nx, ny)))

        if not candidates:
            return {"move": "up"}  # stuck_response

        # max_by_key: on ties, Rust keeps the LAST element -> use >= so later
        # equal-scoring candidates overwrite earlier ones.
        best_mv = None
        best_score = None
        for mv, coor in candidates:
            s = _score(coor, health, occupied, w, h, RECURSION_LIMIT)
            if best_score is None or s >= best_score:
                best_score = s
                best_mv = mv

        return {"move": best_mv}
    except Exception:
        # robust fallback: any in-bounds, non-body move; else "up"
        try:
            board = game_state["board"]
            w = board["width"]
            h = board["height"]
            you = game_state["you"]
            hx, hy = you["head"]["x"], you["head"]["y"]
            occupied = _body_set(board)
            for mv, (dx, dy) in DIRS:
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h) and (nx, ny) not in occupied:
                    return {"move": mv}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
