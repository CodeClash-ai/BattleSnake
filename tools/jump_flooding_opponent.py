import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Port of `jump_flooding_snake` from coreyja/battlesnake-rs
# Owner: coreyja  Botname: jump-flooding
# FIDELITY: faithful scoring (manhattan-distance Voronoi), approximate lookahead.
#
# Original (Rust) is a MinimaxSnake whose evaluation is the `jump-flooding`
# territory-control score:
#   * The 11x11 grid is seeded ONLY with the snake HEADS.
#   * Every cell is assigned to the snake whose head is nearest by MANHATTAN
#     distance.  Snake BODIES are NOT obstacles -- the partition is a pure
#     manhattan Voronoi over the whole board.
#   * Ties keep whichever owner was assigned first in the flood sweep (the
#     original never marks a cell "contested/unowned"; every cell has an owner).
#   * score = my_space / total_space, where total_space is the sum over ALL
#     snakes (i.e. essentially every reachable board cell).
#
# The original wraps this score inside a paranoid alpha-beta minimax run with
# iterative deepening until the move time-limit.  Reproducing a full minimax is
# out of scope for the arena's fast-response contract, so here we evaluate the
# same territory score at 1-ply (greedy over the score after our head moves).
# The *scoring* -- the distinctive part of this bot -- is reproduced faithfully:
# pure manhattan Voronoi, no body obstacles, ties resolved deterministically,
# every cell counted.

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    # Values from the original's about():
    #   apiversion "1", author coreyja, color #efae09,
    #   head "trans-rights-scarf", tail None (-> default).
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#efae09",
        "head": "trans-rights-scarf",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _territory_score(my_id, heads, w, h):
    """Manhattan-distance Voronoi over the whole board, matching the original
    `squares_per_snake`.  `heads` is a list of (snake_id, (x, y)) in a stable
    seeding order; ties are awarded to the head that appears earlier in that
    order (deterministic, mirroring the flood-sweep's "first owner wins" tie
    behaviour).  No obstacles.  Returns my_space / total_space."""
    if not heads:
        return 0.0

    my_space = 0
    total = 0
    for cx in range(w):
        for cy in range(h):
            best_id = None
            best_dist = None
            for sid, (hx, hy) in heads:
                d = abs(cx - hx) + abs(cy - hy)
                if best_dist is None or d < best_dist:
                    best_dist = d
                    best_id = sid
                # equal distance -> keep earlier (first-seeded) owner: no change
            if best_id is None:
                continue
            total += 1
            if best_id == my_id:
                my_space += 1

    if total == 0:
        return 0.0
    return my_space / total


def move(game_state):
    try:
        board = game_state["board"]
        w = board["width"]
        h = board["height"]
        snakes = board.get("snakes", [])
        you = game_state["you"]
        my_id = you["id"]
        my_body = you["body"]
        head = my_body[0]
        hx, hy = head["x"], head["y"]

        # Cells we must not step onto: all snake body segments except tails,
        # which vacate next turn (unless the snake just grew, i.e. the tail
        # overlaps the segment before it).  This is only a *legal-move* filter;
        # it does NOT affect the territory partition (the original ignores
        # bodies entirely when scoring).
        blocked = set()
        for s in snakes:
            b = s.get("body", [])
            n = len(b)
            for idx, seg in enumerate(b):
                cell = (seg["x"], seg["y"])
                if idx == n - 1 and n >= 2:
                    # tail: enterable unless it overlaps the pre-tail segment
                    if b[n - 2]["x"] == seg["x"] and b[n - 2]["y"] == seg["y"]:
                        blocked.add(cell)
                    # else leave enterable
                else:
                    blocked.add(cell)
        # Never step onto our own neck.
        if len(my_body) >= 2:
            blocked.add((my_body[1]["x"], my_body[1]["y"]))

        # Enemy heads stay where they are for the partition.
        enemy_heads = []
        for s in snakes:
            if s["id"] == my_id:
                continue
            b = s.get("body", [])
            if b:
                enemy_heads.append((s["id"], (b[0]["x"], b[0]["y"])))

        legal = []
        for name, (dx, dy) in DIRS.items():
            nx, ny = hx + dx, hy + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in blocked:
                continue
            legal.append((name, (nx, ny)))

        if not legal:
            for name, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h):
                    return {"move": name}
            return {"move": "up"}

        best_move = legal[0][0]
        best_score = float("-inf")
        for name, (nx, ny) in legal:
            # Our head is seeded FIRST (my_id owns ties), matching that our
            # snake is present in the grid; then enemy heads.
            heads = [(my_id, (nx, ny))] + enemy_heads
            score = _territory_score(my_id, heads, w, h)
            if score > best_score:
                best_score = score
                best_move = name

        return {"move": best_move}
    except Exception:
        try:
            board = game_state["board"]
            w = board["width"]
            h = board["height"]
            you = game_state["you"]
            head = you["body"][0]
            hx, hy = head["x"], head["y"]
            occupied = set()
            for s in board.get("snakes", []):
                for seg in s.get("body", []):
                    occupied.add((seg["x"], seg["y"]))
            for name, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h) and (nx, ny) not in occupied:
                    return {"move": name}
            for name, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h):
                    return {"move": name}
        except Exception:
            pass
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
