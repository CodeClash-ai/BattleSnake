"""
Faithful port of pambrose/battlesnake-examples -> SimpleSnake (Kotlin) into
CodeClash v1.

Original: io/battlesnake/examples/kotlin/SimpleSnake.kt (uses the
battlesnake-quickstart "io.battlesnake.core" framework, which speaks the raw
BattleSnake v1 API JSON directly -- board width/height, body/food x,y, and the
standard y-up / bottom-left coordinate system where "up" = y+1, "down" = y-1).

Original strategy (reproduced exactly):

    fun moveTo(request, position): MoveResponse =
        when {
            head.x > position.x -> LEFT
            head.x < position.x -> RIGHT
            head.y > position.y -> DOWN
            else                -> UP
        }

    fun nearestFood(head, foodList): Food =
        foodList.maxByOrNull { head - it.position }!!   // Position.minus == Manhattan
                                                        // -> picks the FARTHEST food

    if (isFoodAvailable)
        moveTo(head, nearestFood(head, foodList).position)
    else
        moveTo(head, boardCenter)

Faithfulness notes:
  - Position.minus is Manhattan distance; maxByOrNull selects the largest, i.e.
    the *farthest* food (a genuine quirk of the original -- preserved).
  - moveTo returns exactly ONE move by strict priority: x fully dominates y.
    If x differs, y is never consulted. The final "else -> UP" also covers the
    fully-aligned (head == target) case.
  - The original has NO collision / out-of-bounds avoidance at all; it blindly
    returns the moveTo direction. We do not add any. The only wrapper is the
    arena-required try/except legal fallback.
"""


def info():
    # DescribeResponse("me", "#ff00ff", "beluga", "bolt")
    return {
        "apiversion": "1",
        "author": "me",
        "color": "#ff00ff",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    # Position.minus: abs(dx) + abs(dy)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _board_center(width, height):
    # Board.center: ((w even ? w/2 : (w+1)/2) - 1, same for height)
    center_x = (width // 2 if width % 2 == 0 else (width + 1) // 2) - 1
    center_y = (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1
    return (center_x, center_y)


def _move_to(head, target):
    """Exact reproduction of SimpleSnake.moveTo (y-up API)."""
    hx, hy = head
    tx, ty = target
    if hx > tx:
        return "left"
    if hx < tx:
        return "right"
    if hy > ty:
        return "down"
    return "up"


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        head_seg = game_state["you"]["body"][0]
        head = (head_seg["x"], head_seg["y"])

        food = board.get("food", [])
        if food:
            # nearestFood: maxByOrNull(Manhattan) -> farthest food.
            # Kotlin maxByOrNull keeps the FIRST element attaining the max.
            target = None
            best = -1
            for f in food:
                fp = (f["x"], f["y"])
                d = _manhattan(head, fp)
                if d > best:
                    best = d
                    target = fp
        else:
            target = _board_center(width, height)

        return {"move": _move_to(head, target)}
    except Exception:
        # Arena-required legal fallback (original has none).
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
