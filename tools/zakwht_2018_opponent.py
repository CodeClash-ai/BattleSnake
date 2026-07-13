"""
Port of zakwht/battlesnake-2018 (Java, 2018) to the Battlesnake v1 API.

Original strategy (ca.casualt.battlesnake.game.Board / SmartSnake):
  - Build a grid marking snake bodies as walls, food as food.
  - If we are NOT longer than an enemy snake, mark the 4 cells adjacent to
    that enemy's head as walls too (avoid losing/tying head-to-head).
  - Choose a mode:
        health <= 50           -> HUNGRY
        longer than all others -> ATTACK
        otherwise              -> HUNGRY (Java falls through to HUNGRY)
  - Move priority by mode (each a BFS returning the FIRST step of the
    shortest path to any goal cell):
        HUNGRY: goToFood -> goToAttack -> goToTail
        ATTACK: goToAttack -> goToFood -> goToTail
  - goToFood:   BFS to nearest food cell.
  - goToAttack: BFS to any enemy head or a cell adjacent to an enemy head.
  - goToTail:   BFS to a cell adjacent to one of our own body segments,
                scanning from tail inward.
  - Fallback when no path found: Move.left (unconditionally).
"""
from collections import deque
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def info():
    return {"apiversion": "1", "author": "zakwht", "color": "#f2c55c", "head": "default", "tail": "default"}


def start(game_state): return None

def end(game_state): return None

_DIRS = [("up", 0, 1), ("down", 0, -1), ("left", -1, 0), ("right", 1, 0)]


def _adjacent(x, y):
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def move(game_state):
    try:
        return {"move": _decide(game_state)}
    except Exception:
        return {"move": "left"}


def _decide(game_state):
    board = game_state["board"]
    w = board["width"]; h = board["height"]
    you = game_state["you"]
    my_body = [(p["x"], p["y"]) for p in you["body"]]
    head = my_body[0]
    my_len = you.get("length", len(my_body))
    my_health = you.get("health", 100)
    snakes = board["snakes"]
    food = [(f["x"], f["y"]) for f in board["food"]]

    blocked = set(); enemy_heads = []; longest_other = None
    my_id = you["id"]
    for snake in snakes:
        body = [(p["x"], p["y"]) for p in snake["body"]]
        for seg in body:
            blocked.add(seg)
        sid = snake["id"]; s_len = snake.get("length", len(body))
        if sid == my_id:
            continue
        if longest_other is None or s_len > longest_other:
            longest_other = s_len
        h_pt = body[0]
        enemy_heads.append(h_pt)
        if not (my_len > s_len):
            for ax, ay in _adjacent(*h_pt):
                if _in_bounds(ax, ay, w, h):
                    blocked.add((ax, ay))

    def is_filled(x, y):
        return (not _in_bounds(x, y, w, h)) or ((x, y) in blocked)

    mode = "HUNGRY"
    if my_health > 50 and longest_other is not None and my_len > longest_other:
        mode = "ATTACK"

    def find_path(goals):
        goal_set = set(g for g in goals if g != head and _in_bounds(g[0], g[1], w, h))
        if not goal_set:
            return None
        visited = {head}; queue = deque()
        for name, dx, dy in _DIRS:
            nx, ny = head[0] + dx, head[1] + dy
            if is_filled(nx, ny) or (nx, ny) in visited:
                continue
            visited.add((nx, ny)); queue.append(((nx, ny), name))
        while queue:
            (px, py), initial = queue.popleft()
            if (px, py) in goal_set:
                return initial
            for name, dx, dy in _DIRS:
                nx, ny = px + dx, py + dy
                if is_filled(nx, ny) or (nx, ny) in visited:
                    continue
                visited.add((nx, ny)); queue.append(((nx, ny), initial))
        return None

    def go_to_food(): return find_path(food)
    def go_to_attack():
        goals = []
        for hp in enemy_heads:
            goals.extend(_adjacent(*hp)); goals.append(hp)
        return find_path(goals)
    def go_to_tail():
        for i in range(len(my_body) - 1, 0, -1):
            m = find_path(_adjacent(*my_body[i]))
            if m is not None: return m
        return None

    chosen = None
    if mode == "ATTACK":
        chosen = go_to_attack() or go_to_food() or go_to_tail()
    else:
        chosen = go_to_food() or go_to_attack() or go_to_tail()
    return chosen or "left"


if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
