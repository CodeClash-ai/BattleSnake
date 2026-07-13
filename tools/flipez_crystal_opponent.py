import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
"""Port of Flipez/battlesnake (Crystal, 2018) to Battlesnake v1 API.

Original strategy (faithful reimplementation):
  - look_around: the 4 orthogonal neighbors of the head.
  - is_free_point?: a point is free if in-bounds, not on any snake's body,
    and not on the predicted next point of any enemy whose length >= mine.
    Enemy prediction: enemy moves toward its own nearest food.
  - next_target: nearest food to me, UNLESS some enemy is closer to that food
    than I am -> then target the board center instead.
  - Choose the free neighbor closest (euclidean) to next_target; move there.

Coordinate remap: original used top-left origin (y-down). v1 uses bottom-left
(y-up). The neighbor-selection logic is coordinate-agnostic; only the direction
label depends on convention, so directions are labeled with v1 semantics
(up=y+1, down=y-1, left=x-1, right=x+1) so the snake physically moves toward
the chosen neighbor point.
"""

import math


def info():
    return {
        "apiversion": "1",
        "author": "Flipez",
        "color": "#FC5299",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return


def end(game_state):
    return


def distance(a, b):
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    return math.sqrt(dx * dx + dy * dy)


def look_around(head):
    return [
        {"x": head["x"] + 1, "y": head["y"]},
        {"x": head["x"] - 1, "y": head["y"]},
        {"x": head["x"], "y": head["y"] + 1},
        {"x": head["x"], "y": head["y"] - 1},
    ]


def nearest_food(head, foods):
    if not foods:
        return None
    return min(foods, key=lambda f: distance(f, head))


def next_move_label(head, point):
    # v1 semantics: up=y+1, down=y-1, left=x-1, right=x+1
    if head["x"] == point["x"]:
        return "up" if head["y"] < point["y"] else "down"
    else:
        return "right" if head["x"] < point["x"] else "left"


def next_point_toward(head, target):
    # Predict a snake's next head position: it moves one step toward target
    # (matches original next_move -> next_point pipeline for enemies).
    label = next_move_label(head, target)
    if label == "up":
        return {"x": head["x"], "y": head["y"] + 1}
    if label == "down":
        return {"x": head["x"], "y": head["y"] - 1}
    if label == "left":
        return {"x": head["x"] - 1, "y": head["y"]}
    return {"x": head["x"] + 1, "y": head["y"]}


def is_free_point(target, board, snakes, me, foods):
    w = board["width"]
    h = board["height"]

    if not (0 <= target["x"] <= w - 1):
        return False
    if not (0 <= target["y"] <= h - 1):
        return False

    occupied = []
    for s in snakes:
        occupied.extend(s["body"])

    # Predict enemy movement toward their nearest food (only if >= my length)
    my_len = me.get("length", len(me["body"]))
    for enemy in snakes:
        if enemy["id"] == me["id"]:
            continue
        e_len = enemy.get("length", len(enemy["body"]))
        if e_len >= my_len:
            e_head = enemy["body"][0]
            e_food = nearest_food(e_head, foods)
            if e_food is not None:
                occupied.append(next_point_toward(e_head, e_food))

    for p in occupied:
        if p["x"] == target["x"] and p["y"] == target["y"]:
            return False
    return True


def board_center(board):
    # Original: x range 1..width, center = list[size/2] (integer div).
    xs = list(range(1, board["width"] + 1))
    ys = list(range(1, board["height"] + 1))
    x_center = xs[len(xs) // 2]
    y_center = ys[len(ys) // 2]
    return {"x": x_center, "y": y_center}


def next_target(me, snakes, foods, board):
    head = me["body"][0]
    nf = nearest_food(head, foods)
    if nf is None:
        return board_center(board)

    my_dist = distance(head, nf)
    enemy_closer = False
    for s in snakes:
        if s["id"] == me["id"]:
            continue
        if my_dist > distance(s["body"][0], nf):
            enemy_closer = True
            break

    if enemy_closer:
        return board_center(board)
    return nf


def move(game_state):
    try:
        board = game_state["board"]
        me = game_state["you"]
        snakes = board["snakes"]
        foods = board.get("food", [])
        head = me["body"][0]

        candidates = look_around(head)
        free = [p for p in candidates if is_free_point(p, board, snakes, me, foods)]

        target = next_target(me, snakes, foods, board)

        if free:
            chosen = min(free, key=lambda p: distance(p, target))
            return {"move": next_move_label(head, chosen)}

        # Fallback: no "free" point per original filter. Pick any in-bounds
        # neighbor that does not hit a snake body (tails are enterable).
        w, h = board["width"], board["height"]
        bodies = []
        for s in snakes:
            b = s["body"]
            # tail is enterable unless the snake just ate (we can't be sure,
            # so treat tail as enterable per prompt guidance)
            bodies.extend(b[:-1] if len(b) > 1 else b)
        for p in candidates:
            if not (0 <= p["x"] <= w - 1 and 0 <= p["y"] <= h - 1):
                continue
            if any(bp["x"] == p["x"] and bp["y"] == p["y"] for bp in bodies):
                continue
            return {"move": next_move_label(head, p)}

        # Last resort: any in-bounds neighbor.
        for p in candidates:
            if 0 <= p["x"] <= w - 1 and 0 <= p["y"] <= h - 1:
                return {"move": next_move_label(head, p)}

        return {"move": "up"}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
