"""A local "passive" stand-in opponent bot for testing purposes only.

Multiple previous README_agent.md sessions (search "passive stand-in" /
"opponent stays tiny/passive forever" earlier in README_agent.md) flagged
that self-play A/B testing is a poor proxy for validating fixes aimed at
the "dominant-length self-trap" failure class, because self-play mirrors
symmetric aggressive growth, whereas the REAL opponents that trigger this
failure class in actual match logs consistently stay short/tiny for
hundreds of turns while our own snake grows huge and eventually
self-traps.

This bot deliberately mimics that real-world pattern: it plays safe
(basic flood-fill-based self/wall avoidance, exactly like a competent but
simple bot) but ONLY eats food when its health is getting low (<=40),
otherwise actively avoids food and just wanders in open space. This
should stay short far longer than a normal food-seeking bot, giving a
much more representative local test harness for any future fix aimed at
the "our own snake overgrows and self-traps against a small/passive
opponent" problem, without needing to wait for a real round's results.

Usage (same server-launch pattern as tools/opponent_ref.py -- see
README_agent.md's many "Server-testing gotchas" notes for the reliable
setsid/nohup/disown pattern):

    setsid nohup env PORT=9999 python3 tools/passive_opponent.py \
        > /tmp/passive.log 2>&1 < /dev/null &
    disown -a
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import run_server

DIRS = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}


def info():
    return {"apiversion": "1", "author": "passive", "color": "#888888",
            "head": "sand-worm", "tail": "freckled"}


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(pt, width, height):
    return 0 <= pt[0] < width and 0 <= pt[1] < height


def _occupied(board, my_id):
    blocked = set()
    for s in board["snakes"]:
        body = s["body"]
        tail_will_vacate = True
        if s["id"] == my_id:
            tail_will_vacate = len(body) < 3 or body[-1] != body[-2]
        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if i == len(body) - 1 and tail_will_vacate:
                continue
            blocked.add(cell)
    return blocked


def _flood_fill(start, blocked, width, height, cap=200):
    if start in blocked:
        return 0
    seen = {start}
    frontier = [start]
    count = 0
    while frontier and count < cap:
        nxt = []
        for cell in frontier:
            count += 1
            for dx, dy in DIRS.values():
                npt = (cell[0] + dx, cell[1] + dy)
                if npt in seen:
                    continue
                if not _in_bounds(npt, width, height) or npt in blocked:
                    continue
                seen.add(npt)
                nxt.append(npt)
        frontier = nxt
    return count


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        you = game_state["you"]
        my_id = you["id"]
        head = (you["body"][0]["x"], you["body"][0]["y"])
        health = you.get("health", 100)
        food = [(f["x"], f["y"]) for f in board.get("food", [])]

        blocked = _occupied(board, my_id)
        # Basic head-to-head avoidance vs any opposing snake that's
        # equal-or-longer than us (avoids the "dies to an avoidable
        # collision after only 10-20 turns" issue found when this bot
        # was first added -- see README_agent.md for the investigation).
        my_len = len(you["body"])
        opp_heads = []
        for s in board["snakes"]:
            if s["id"] == my_id:
                continue
            if len(s["body"]) >= my_len:
                opp_heads.append((s["body"][0]["x"], s["body"][0]["y"]))

        candidates = []
        risky = []
        for name, (dx, dy) in DIRS.items():
            npt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(npt, width, height):
                continue
            if npt in blocked:
                continue
            if any(_manhattan(npt, oh) <= 1 for oh in opp_heads):
                risky.append((name, npt))
                continue
            candidates.append((name, npt))
        if not candidates:
            candidates = risky

        if not candidates:
            # doomed; just try any in-bounds direction
            for name, (dx, dy) in DIRS.items():
                npt = (head[0] + dx, head[1] + dy)
                if _in_bounds(npt, width, height):
                    return {"move": name}
            return {"move": "up"}

        scored = []
        for name, npt in candidates:
            space = _flood_fill(npt, blocked, width, height, cap=max(len(you["body"]) + 4, 30))
            score = space * 2.0
            if health <= 40 and food:
                nearest = min(_manhattan(npt, f) for f in food)
                score += 40.0 / (nearest + 1)
            elif food:
                # actively avoid food when not hungry: penalize landing on it
                nearest = min(_manhattan(npt, f) for f in food)
                if nearest == 0:
                    score -= 60.0
            scored.append((score, name))

        scored.sort(reverse=True)
        return {"move": scored[0][1]}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    run_server({"info": info, "start": start, "move": move, "end": end})
