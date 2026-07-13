import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""CodeClash port of ccSnake2018 / ccsnake (2018 Battlesnake competition).

Original: https://github.com/ccSnake2018/ccsnake  (Python 2.7, bottle, OLD API).

Original strategy (app/main.py):
  * Build a grid; mark all snake bodies (every segment except the last) as
    danger (board==1 / secure==0).
  * Re-open the tail cell that will vacate next turn -- unless the last two
    real body segments are stacked (just ate) or the head's next moves land on
    food (about to grow). (get_open_coordinates)
  * Mark the next-step cells of any enemy whose length >= mine as danger
    (avoid losing head-to-head collisions).
  * Compute a "secure_level" grid (0..5) via a recursive up-to-5-round forecast
    (next_move_forcast/next_new_body_list): every snake head advances to its
    legal next cells each round; a cell first reached at round R gets its
    security clamped down to R (sooner => more dangerous).  My OWN snake's
    projected HEAD does not lower security (self_head guard), but every
    snake's projected trailing BODY does.  A reached cell is further collapsed
    by how many walls surround it: 4 walls => 0; 3 walls => 1 (only if R>1);
    2 walls => 2 (only if R>2); 1 wall => 3 (only if R>3).
  * From the legal (non-danger, in-bounds) directions, move toward the closest
    food by squared-Euclidean distance (ties -> later food wins), preferring
    moves onto cells whose security level is >= the reference cell's.

The original used the 2018 API (top-left origin, y increases DOWNWARD) and
stored coordinates internally SWAPPED as [row, col] = [orig_y, orig_x], with
'up' == row-1.  This port reproduces the strategy in the CURRENT v1 API
(bottom-left origin, y-up, head = body[0]) and never crashes / never makes an
illegal move.
"""


def info():
    # Original start() returned color '#ff9999', head_type 'tongue',
    # tail_type 'pixel'.
    return {
        "apiversion": "1",
        "author": "ccSnake2018",
        "color": "#ff9999",
        "head": "tongue",
        "tail": "pixel",
    }


def start(game_state):
    return {}


def end(game_state):
    return {}


# ---------------------------------------------------------------------------
# Helpers (v1 coordinates: (0,0) bottom-left, up=y+1, down=y-1, left=x-1,
# right=x+1, head = body[0]).
# ---------------------------------------------------------------------------

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _sq_dist(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2


def _neighbors(x, y, w, h):
    """In-bounds neighbor cells with their direction name."""
    out = []
    for name, (dx, dy) in DIRS.items():
        nx, ny = x + dx, y + dy
        if _in_bounds(nx, ny, w, h):
            out.append((name, nx, ny))
    return out


def _count_walls(x, y, danger, w, h):
    """count_amount_walls(): orthogonal neighbors that are danger.

    The original only counted the up/down pair when the cell was strictly
    interior vertically (0 < y < h-1) and the left/right pair when strictly
    interior horizontally (0 < x < w-1); out-of-bounds edges were NOT counted
    as walls, only board==1 (danger) cells were.  Reproduced faithfully.
    """
    count = 0
    if 0 < y < h - 1:
        if (x, y + 1) in danger:
            count += 1
        if (x, y - 1) in danger:
            count += 1
    if 0 < x < w - 1:
        if (x + 1, y) in danger:
            count += 1
        if (x - 1, y) in danger:
            count += 1
    return count


def _legal_next(x, y, danger, w, h):
    """direction_options(): in-bounds neighbors whose cell is not danger."""
    out = []
    for _name, nx, ny in _neighbors(x, y, w, h):
        if (nx, ny) not in danger:
            out.append((nx, ny))
    return out


def _build_danger(game_state):
    """set_walls(): occupied cells + head-clash cells of >= snakes, minus the
    tail cells that vacate next turn."""
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_len = you.get("length", len(you["body"]))
    my_id = you["id"]
    food = {(f["x"], f["y"]) for f in board.get("food", [])}

    danger = set()
    snakes = board.get("snakes", [])

    # 1. mark every segment except the last (tail follows the body)
    for snake in snakes:
        body = [(p["x"], p["y"]) for p in snake["body"]]
        if not body:
            continue
        for seg in body[:-1]:
            danger.add(seg)

    # 2. reopen the tail that will vacate next turn (get_open_coordinates):
    #    real body must have >= 2 segments, tail != pre-tail (not stacked),
    #    and none of the head's next cells are on food.
    reopen = set()
    for snake in snakes:
        body = [(p["x"], p["y"]) for p in snake["body"]]
        if len(body) < 2:
            continue
        tail = body[-1]
        pre_tail = body[-2]
        if tail == pre_tail:
            continue
        hx, hy = body[0]
        about_to_eat = any(
            (hx + dx, hy + dy) in food for (dx, dy) in DIRS.values()
        )
        if not about_to_eat:
            reopen.add(tail)
    danger -= reopen

    # 3. block next-step cells of enemies at least as long as me.
    for snake in snakes:
        if snake["id"] == my_id:
            continue
        s_len = snake.get("length", len(snake["body"]))
        if s_len >= my_len:
            ex, ey = snake["body"][0]["x"], snake["body"][0]["y"]
            for nx, ny in _legal_next(ex, ey, danger, w, h):
                danger.add((nx, ny))

    return danger


def _mark(secure, x, y, rnd, danger, w, h):
    """next_new_body_list() per-cell clamp + wall tiering."""
    if secure[x][y] > rnd:
        secure[x][y] = rnd
        walls = _count_walls(x, y, danger, w, h)
        if walls == 4:
            secure[x][y] = 0
        elif walls == 3:
            if rnd > 1:
                secure[x][y] = 1
        elif walls == 2:
            if rnd > 2:
                secure[x][y] = 2
        elif walls == 1:
            if rnd > 3:
                secure[x][y] = 3


def _forecast(bodies, rnd, secure, danger, w, h):
    """next_move_forcast(): recursive up-to-5-round reach forecast.

    `bodies` is a list of (segments, is_me) where segments is a list of (x,y)
    with head first.  Each snake's head advances to every legal next cell;
    the head cell lowers security only for non-self snakes; trailing body
    cells always lower security.  Recurses to round 5.
    """
    next_bodies = []
    for segments, is_me in bodies:
        if not segments:
            continue
        head = segments[0]
        for nx, ny in _legal_next(head[0], head[1], danger, w, h):
            # build the shifted body: new head, then old body shifted by one,
            # keeping the original tail (mirrors next_new_body_list).
            new_body = [(nx, ny)]
            # mark head (self-head exempt)
            if not is_me:
                _mark(secure, nx, ny, rnd, danger, w, h)
            # trailing body: original segments[0 .. len-2] shifted in, marked
            for idx in range(1, len(segments) - 1):
                sx, sy = segments[idx - 1]
                new_body.append((sx, sy))
                _mark(secure, sx, sy, rnd, danger, w, h)
            new_body.append(segments[-1])
            next_bodies.append((new_body, is_me))

    if rnd != 5:
        _forecast(next_bodies, rnd + 1, secure, danger, w, h)


def _secure_levels(game_state, danger):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    my_id = you["id"]

    secure = [[5 for _ in range(h)] for _ in range(w)]

    # set_walls also stamped every occupied body segment (except tail) to 0.
    for snake in board.get("snakes", []):
        body = [(p["x"], p["y"]) for p in snake["body"]]
        for (sx, sy) in body[:-1]:
            secure[sx][sy] = 0

    # forcast_list: me first, then enemies (health>0).
    bodies = []
    my_body = [(p["x"], p["y"]) for p in you["body"]]
    bodies.append((my_body, True))
    for snake in board.get("snakes", []):
        if snake["id"] == my_id:
            continue
        if snake.get("health", 1) == 0:
            continue
        seg = [(p["x"], p["y"]) for p in snake["body"]]
        bodies.append((seg, False))

    _forecast(bodies, 1, secure, danger, w, h)
    return secure


def _choose(game_state):
    board = game_state["board"]
    w, h = board["width"], board["height"]
    you = game_state["you"]
    head = you["body"][0]
    hx, hy = head["x"], head["y"]

    danger = _build_danger(game_state)
    secure = _secure_levels(game_state, danger)

    # legal moves: in-bounds and not danger (direction_options)
    options = []
    for name, nx, ny in _neighbors(hx, hy, w, h):
        if (nx, ny) not in danger:
            options.append((name, nx, ny))

    # fallback ordering if no "safe" options: any in-bounds non-body cell
    # (tails enterable), then any in-bounds cell at all.
    if not options:
        bodies = set()
        for snake in board.get("snakes", []):
            for p in snake["body"][:-1]:
                bodies.add((p["x"], p["y"]))
        for name, nx, ny in _neighbors(hx, hy, w, h):
            if (nx, ny) not in bodies:
                options.append((name, nx, ny))
    if not options:
        options = _neighbors(hx, hy, w, h)
    if not options:
        return "up"

    # closest food (squared euclidean); ties -> later food wins (original <=).
    foods = [(f["x"], f["y"]) for f in board.get("food", [])]
    if foods:
        best_food = foods[0]
        best_fd = _sq_dist(hx, hy, best_food[0], best_food[1])
        for fx, fy in foods:
            d = _sq_dist(hx, hy, fx, fy)
            if d <= best_fd:
                best_food = (fx, fy)
                best_fd = d
        fx, fy = best_food
    else:
        fx, fy = w // 2, h // 2

    # prefer higher security level, then shorter distance to food.
    def key(opt):
        _name, nx, ny = opt
        return (-secure[nx][ny], _sq_dist(nx, ny, fx, fy))

    options.sort(key=key)
    return options[0][0]


def move(game_state):
    try:
        return {"move": _choose(game_state)}
    except Exception:
        try:
            board = game_state["board"]
            w, h = board["width"], board["height"]
            you = game_state["you"]
            head = you["body"][0]
            hx, hy = head["x"], head["y"]
            bodies = set()
            for snake in board.get("snakes", []):
                for p in snake["body"][:-1]:
                    bodies.add((p["x"], p["y"]))
            for name, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h) and (nx, ny) not in bodies:
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
