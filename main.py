"""
Battlesnake bot for CodeClash.

Strategy overview:
  1. Compute the set of "safe" moves from the current head position:
     - stay in bounds
     - don't collide with any snake body (accounting for tails that will
       move away next turn unless that snake just ate food this turn, in
       which case its tail stays put)
     - avoid moving head-to-head into an equal-or-longer opposing snake
  2. Among safe moves, use flood-fill (BFS) to estimate the amount of open
     space reachable after each candidate move. Heavily penalize moves that
     lead into small/trapped pockets (less than our own body length) since
     that usually means death a few turns later.
  3. Score each safe move combining:
     - reachable space (avoid getting trapped)
     - distance to nearest food (prefer closer food, weighted by our health
       - low health means food is more urgent)
     - a bonus for moves that could set up a favorable head-to-head
       (moving toward a strictly shorter snake's head region is fine, but we
       never deliberately move adjacent to a longer snake's head)
     - a small centrality bonus to avoid hugging walls/corners early on
  4. If no safe moves exist (we're doomed), fall back to the move that
     maximizes flood-fill space, ignoring snake-collision safety, as a last
     resort (better than an immediate certain-death direction if there's any
     difference at all).
"""

import random

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
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
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _in_bounds(pt, width, height):
    return 0 <= pt[0] < width and 0 <= pt[1] < height


def _occupied_cells(board, you_id):
    """Return dict cell -> info about occupancy for collision checks.

    We build:
      blocked: set of cells that are always unsafe to move into (bodies
               excluding tails that will vacate)
      snake_lengths: dict id -> length
      heads: dict id -> (x,y)
    """
    blocked = set()
    tails_that_move = set()
    heads = {}
    lengths = {}
    for snake in board["snakes"]:
        body = snake["body"]
        lengths[snake["id"]] = len(body)
        heads[snake["id"]] = (body[0]["x"], body[0]["y"])
        # Determine if this snake ate food last turn (tail didn't move).
        # Heuristic: if last two body segments are identical (stacked),
        # that indicates growth just happened (common battlesnake engine
        # behavior for the turn right after eating).
        ate_last_turn = False
        if len(body) >= 2:
            last = body[-1]
            second_last = body[-2]
            if last["x"] == second_last["x"] and last["y"] == second_last["y"]:
                ate_last_turn = True

        for i, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            is_tail = i == len(body) - 1
            if is_tail and not ate_last_turn:
                # tail will move away next turn -> safe-ish, don't block
                tails_that_move.add(cell)
            else:
                blocked.add(cell)

    # Remove tail cells from blocked only if they aren't also occupied by
    # another body segment (defensive; sets already prevent duplicates from
    # counting twice but overlapping snakes could still be an issue).
    return blocked, heads, lengths


def _flood_fill_size(start, blocked, width, height, cap):
    """BFS to count reachable empty cells from `start`, stopping early once
    `cap` cells have been found (cap is usually our own length, we only need
    to know if we have at least that much space)."""
    if start in blocked:
        return 0
    seen = {start}
    frontier = [start]
    count = 1
    while frontier and count < cap:
        nxt = []
        for cell in frontier:
            for dx, dy in DIRS.values():
                npt = (cell[0] + dx, cell[1] + dy)
                if npt in seen:
                    continue
                if not _in_bounds(npt, width, height):
                    continue
                if npt in blocked:
                    continue
                seen.add(npt)
                count += 1
                nxt.append(npt)
                if count >= cap:
                    break
            if count >= cap:
                break
        frontier = nxt
    return count


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        you = game_state["you"]
        head = (you["body"][0]["x"], you["body"][0]["y"])
        my_id = you["id"]
        my_len = len(you["body"])
        health = you.get("health", 100)

        food = board.get("food", [])

        blocked, heads, lengths = _occupied_cells(board, my_id)

        candidates = []
        for name, (dx, dy) in DIRS.items():
            npt = (head[0] + dx, head[1] + dy)
            if not _in_bounds(npt, width, height):
                continue
            if npt in blocked:
                continue

            # Head-to-head risk check: if an opposing head could also move
            # onto npt next turn and that snake is >= our length, treat as
            # dangerous (skip unless no alternative).
            danger_h2h = False
            for sid, hpos in heads.items():
                if sid == my_id:
                    continue
                if _manhattan(hpos, npt) == 1:
                    # opponent could move into npt too
                    if lengths.get(sid, 0) >= my_len:
                        danger_h2h = True
                        break

            candidates.append((name, npt, danger_h2h))

        if not candidates:
            # No in-bounds / non-body moves at all. Just try anything that
            # keeps us in bounds, ignoring body blocks (already dead anyway).
            for name, (dx, dy) in DIRS.items():
                npt = (head[0] + dx, head[1] + dy)
                if _in_bounds(npt, width, height):
                    return {"move": name}
            return {"move": "up"}

        safe_candidates = [c for c in candidates if not c[2]]
        pool = safe_candidates if safe_candidates else candidates

        # Score each candidate.
        best_name = None
        best_score = None
        cap = max(my_len + 2, 8)

        for name, npt, danger_h2h in pool:
            space = _flood_fill_size(npt, blocked, width, height, cap)

            score = 0.0
            # Space safety: heavily penalize tight spaces relative to our
            # length (getting trapped = death).
            if space < my_len:
                score -= 1000.0 * (my_len - space)
            score += min(space, cap) * 2.0

            # Food attraction.
            if food:
                dists = [_manhattan(npt, (f["x"], f["y"])) for f in food]
                nearest = min(dists)
                # Weight food urgency higher when health is low.
                urgency = 1.0
                if health <= 40:
                    urgency = 3.0
                elif health <= 70:
                    urgency = 1.5
                score += urgency * (20.0 / (nearest + 1))
            else:
                cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
                score -= 0.1 * _manhattan(npt, (cx, cy))

            # Slight preference against hugging edges (more escape routes).
            edge_dist = min(npt[0], width - 1 - npt[0], npt[1], height - 1 - npt[1])
            score += 0.3 * edge_dist

            if danger_h2h:
                score -= 500.0

            # Tiny randomness to break ties unpredictably.
            score += random.uniform(0, 0.01)

            if best_score is None or score > best_score:
                best_score = score
                best_name = name

        return {"move": best_name}
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
