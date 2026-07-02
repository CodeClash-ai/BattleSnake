"""Cornelius the Corn Snake -- Python port of ChaelCodes/CorneliusCodes (Rust).

Faithful reimplementation of the original scoring logic against Battlesnake v1 API.
"""

DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info():
    return {
        "apiversion": "1",
        "author": "ChaelCodes",
        "color": "#c88b4c",
        "head": "bendr",
        "tail": "round-bum",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _neighbors(spot):
    x, y = spot
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def _spot_has_food(spot, food):
    return spot in food


def _spot_has_hazards(spot, hazards):
    return spot in hazards


def _spot_has_snake(spot, snake_cells):
    # In the original, all snake parts (head + full body) are obstacles.
    return spot in snake_cells


def _in_bounds(spot, width, height):
    x, y = spot
    return 0 <= x < width and 0 <= y < height


def _valid_move(spot, width, height, snake_cells):
    if not _in_bounds(spot, width, height):
        return False
    if _spot_has_snake(spot, snake_cells):
        return False
    return True


def _spot_might_have_snake(spot, snakes, me):
    """A spot is dangerous if an equal-or-larger opponent head is adjacent."""
    for snake in snakes:
        if snake["id"] != me["id"] and snake.get("length", len(snake["body"])) >= me_length(me):
            head = (snake["head"]["x"], snake["head"]["y"])
            if spot in _neighbors(head):
                return True
    return False


def me_length(me):
    return me.get("length", len(me["body"]))


def _remaining_space(spot, width, height, snake_cells, length):
    """Flood-fill capped at the snake's length, matching check_spot_for_space."""
    available = []
    stack = [spot]
    seen = set()
    # Emulate the recursive expansion: only expand from valid cells.
    while stack:
        if len(available) >= length:
            break
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        if cur in available:
            continue
        if _valid_move(cur, width, height, snake_cells):
            available.append(cur)
            for nb in [(cur[0] + 1, cur[1]), (cur[0] - 1, cur[1]),
                       (cur[0], cur[1] + 1), (cur[0], cur[1] - 1)]:
                if _valid_move(nb, width, height, snake_cells) and nb not in seen:
                    stack.append(nb)
    return len(available)


def _spot_modifier(spot, width, height, food, hazards, snakes, snake_cells, me):
    modifier = 0
    if _spot_might_have_snake(spot, snakes, me):
        modifier -= 80
    if _spot_has_food(spot, food):
        modifier += 75
    elif _spot_has_hazards(spot, hazards):
        leftover_health = me["health"] - 14
        modifier -= 100 - leftover_health
    spaces = _remaining_space(spot, width, height, snake_cells, me_length(me))
    if spaces >= me_length(me):
        modifier += 50
    else:
        modifier -= 80 - spaces
    return modifier


def _value_of_move(spot, width, height, food, hazards, snakes, snake_cells, me):
    if _spot_has_snake(spot, snake_cells):
        base = -99  # Bite someone else before you bite the dust!
    elif not _valid_move(spot, width, height, snake_cells):
        base = -100
    else:
        x, y = spot
        if y == 0 or x == 0:
            base = 60  # superstitious of the zero edges
        else:
            base = 100
    return base + _spot_modifier(spot, width, height, food, hazards, snakes, snake_cells, me)


def move(game_state):
    try:
        board = game_state["board"]
        me = game_state["you"]
        width = board["width"]
        height = board["height"]
        food = set((f["x"], f["y"]) for f in board.get("food", []))
        hazards = set((h["x"], h["y"]) for h in board.get("hazards", []))
        snakes = board.get("snakes", [])

        # All snake parts are obstacles (head + body), matching spot_has_snake.
        snake_cells = set()
        for s in snakes:
            snake_cells.add((s["head"]["x"], s["head"]["y"]))
            for part in s["body"]:
                snake_cells.add((part["x"], part["y"]))

        head = (me["head"]["x"], me["head"]["y"])

        scored = {}
        for d, (dx, dy) in DIRS.items():
            spot = (head[0] + dx, head[1] + dy)
            scored[d] = _value_of_move(
                spot, width, height, food, hazards, snakes, snake_cells, me
            )

        best = max(scored, key=lambda k: scored[k])

        # Safety net: if the best pick still walks into a wall or a snake body
        # (tails are enterable), prefer any strictly-safe move.
        def is_safe(d):
            dx, dy = DIRS[d]
            spot = (head[0] + dx, head[1] + dy)
            if not _in_bounds(spot, width, height):
                return False
            # Tails are enterable: a body cell that is the last segment of a
            # snake (and not about to grow) will move away.
            return spot not in _occupied_next(snakes, me)

        if not is_safe(best):
            safe = [d for d in DIRS if is_safe(d)]
            if safe:
                best = max(safe, key=lambda k: scored[k])

        return {"move": best}
    except Exception:
        return {"move": "up"}


def _occupied_next(snakes, me):
    """Cells that will still be occupied next turn (tails vacate unless the
    snake just ate). Conservative: keep tail blocked if health==100."""
    occupied = set()
    for s in snakes:
        body = s["body"]
        head = (s["head"]["x"], s["head"]["y"])
        occupied.add(head)
        for i, part in enumerate(body):
            cell = (part["x"], part["y"])
            # The tail (last segment) will move away unless the snake ate.
            if i == len(body) - 1:
                if s.get("health", 0) == 100:
                    occupied.add(cell)
                continue
            occupied.add(cell)
    return occupied


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
