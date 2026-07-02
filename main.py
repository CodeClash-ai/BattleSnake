# Port of `jump_flooding_snake` from coreyja/battlesnake-rs
# Owner: coreyja  Botname: jump-flooding
# FIDELITY: approximate
#
# Original is a MinimaxSnake whose scoring function is jump-flooding territory
# control: each board cell is assigned to the nearest snake head (Voronoi
# partition by manhattan distance, ties/contested -> unowned), and the score is
# my_space / total_owned_space.  We reproduce the *scoring* faithfully using a
# multi-source BFS flood-fill (a standard stand-in for jump-flooding that yields
# the same nearest-head partition), and pick the legal move that maximizes it.
# We approximate the minimax lookahead with a 1-ply greedy over that score.

from collections import deque

DIRS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}


def info():
    return {
        "apiversion": "1",
        "author": "coreyja",
        "color": "#efae09",
        "head": "default",
        "tail": "default",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h


def _blocked_cells(snakes, keep_tails_enterable=True):
    """Set of (x,y) occupied by snake bodies. Tails are enterable (a moving
    snake vacates its tail) unless the snake just ate (health full / body has
    duplicated tail)."""
    blocked = set()
    for s in snakes:
        body = s.get("body", [])
        if not body:
            continue
        n = len(body)
        for idx, seg in enumerate(body):
            cell = (seg["x"], seg["y"])
            if keep_tails_enterable and idx == n - 1:
                # Tail vacates next turn unless it overlaps the segment before
                # it (snake grew / just ate) -> then it stays.
                if n >= 2 and body[n - 2]["x"] == seg["x"] and body[n - 2]["y"] == seg["y"]:
                    blocked.add(cell)
                # else: leave tail enterable
            else:
                blocked.add(cell)
    return blocked


def _territory_score(my_id, heads, obstacles, w, h):
    """Multi-source BFS from every snake head simultaneously; each free cell is
    owned by whichever head reaches it first (equal distance -> contested,
    unowned). Returns my_space / total_owned_space."""
    # owner[(x,y)] = snake id, dist[(x,y)] = bfs distance
    owner = {}
    dist = {}
    q = deque()
    for sid, (hx, hy) in heads:
        if not _in_bounds(hx, hy, w, h):
            continue
        pos = (hx, hy)
        if pos in obstacles:
            continue
        if pos in dist:
            # two heads on same cell -> contested
            owner[pos] = None
        else:
            dist[pos] = 0
            owner[pos] = sid
            q.append(pos)

    while q:
        x, y = q.popleft()
        d = dist[(x, y)]
        cur_owner = owner[(x, y)]
        for dx, dy in DIRS.values():
            nx, ny = x + dx, y + dy
            if not _in_bounds(nx, ny, w, h):
                continue
            npos = (nx, ny)
            if npos in obstacles:
                continue
            nd = d + 1
            if npos not in dist:
                dist[npos] = nd
                owner[npos] = cur_owner
                q.append(npos)
            elif dist[npos] == nd and owner[npos] != cur_owner:
                # reached at equal distance by different owner -> contested
                owner[npos] = None

    counts = {}
    for o in owner.values():
        if o is None:
            continue
        counts[o] = counts.get(o, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return 0.0
    my_space = counts.get(my_id, 0)
    return my_space / total


def move(game_state):
    try:
        board = game_state["board"]
        w = board["width"]
        h = board["height"]
        snakes = board.get("snakes", [])
        you = game_state["you"]
        my_id = you["id"]
        head = you["body"][0]
        hx, hy = head["x"], head["y"]

        blocked = _blocked_cells(snakes, keep_tails_enterable=True)
        # Never step onto our own neck.
        my_body = you.get("body", [])
        if len(my_body) >= 2:
            blocked.add((my_body[1]["x"], my_body[1]["y"]))

        # Enemy heads (for the territory partition we place our head at the
        # candidate cell and keep enemy heads where they are).
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
            # No safe move; still must return in-bounds if possible.
            for name, (dx, dy) in DIRS.items():
                nx, ny = hx + dx, hy + dy
                if _in_bounds(nx, ny, w, h):
                    return {"move": name}
            return {"move": "up"}

        # Obstacles for the flood-fill: all snake bodies except the very cells
        # that heads occupy (heads are the flood sources).
        base_obstacles = set()
        for s in snakes:
            b = s.get("body", [])
            for idx, seg in enumerate(b):
                if idx == 0:
                    continue  # heads are sources, not obstacles
                base_obstacles.add((seg["x"], seg["y"]))

        best_move = legal[0][0]
        best_score = float("-inf")
        for name, (nx, ny) in legal:
            heads = [(my_id, (nx, ny))] + enemy_heads
            obstacles = set(base_obstacles)
            # our old head cell becomes body (obstacle); new head is a source.
            obstacles.add((hx, hy))
            obstacles.discard((nx, ny))
            score = _territory_score(my_id, heads, obstacles, w, h)
            if score > best_score:
                best_score = score
                best_move = name

        return {"move": best_move}
    except Exception:
        # Robust fallback: any in-bounds, non-body move.
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
