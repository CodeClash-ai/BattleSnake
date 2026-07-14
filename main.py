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

def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        
        my_id = game_state["you"]["id"]
        my_body = game_state["you"]["body"]
        my_length = len(my_body)
        head_seg = my_body[0]
        head = (head_seg["x"], head_seg["y"])

        # Determine possible next steps
        possible_moves = {
            "up": (head[0], head[1] + 1),
            "down": (head[0], head[1] - 1),
            "left": (head[0] - 1, head[1]),
            "right": (head[0] + 1, head[1])
        }

        # 1. Avoid out of bounds
        safe_moves = {}
        for d, pos in possible_moves.items():
            if 0 <= pos[0] < width and 0 <= pos[1] < height:
                safe_moves[d] = pos

        # 2. Avoid obstacle collisions (own body and other snakes)
        # Note: A snake's tail segment will move out of the way on this turn, UNLESS they consumed food on the previous turn.
        # However, to be absolutely safe, let's treat the entire body as an obstacle except maybe the tail if we want to be fancy.
        # But for now, let's just avoid all segments to be extremely robust.
        obstacle_positions = set()
        for s in board["snakes"]:
            for seg in s["body"]:
                obstacle_positions.add((seg["x"], seg["y"]))

        # Filter out safe moves that collide with obstacles
        non_colliding_moves = {}
        for d, pos in safe_moves.items():
            if pos not in obstacle_positions:
                non_colliding_moves[d] = pos

        # 3. Head-to-Head Collision Avoidance:
        # If an adjacent cell is next to an opponent's head, they could move there.
        # We should only allow it if we are strictly longer than that opponent.
        # If we are shorter or equal, we should avoid moving to any cell adjacent to their head.
        dangerous_head_moves = set()
        for s in board["snakes"]:
            if s["id"] == my_id:
                continue
            opp_head = (s["head"]["x"], s["head"]["y"])
            opp_length = len(s["body"])
            
            # If opponent is longer or equal to us, their potential next moves are dangerous
            if opp_length >= my_length:
                for opp_d in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                    dangerous_head_moves.add((opp_head[0] + opp_d[0], opp_head[1] + opp_d[1]))

        # Filter out dangerous head-to-head moves
        smart_moves = {}
        for d, pos in non_colliding_moves.items():
            if pos not in dangerous_head_moves:
                smart_moves[d] = pos

        # Fallback logic:
        # Best: smart_moves (no collisions, no disadvantageous head-to-heads)
        # Second best: non_colliding_moves (no standard collisions, but possible risk of head-to-head)
        # Third best: safe_moves (only avoid walls, might crash into bodies)
        # Last resort: just go up
        choices = smart_moves if smart_moves else (non_colliding_moves if non_colliding_moves else safe_moves)
        if not choices:
            return {"move": "up"}

        # 4. Flood fill to avoid dead ends/traps:
        # We evaluate each choice by performing a BFS/flood-fill to count how many reachable cells exist from that move.
        # This helps avoid tunneling into a dead-end pocket.
        def get_reachable_area(start_pos):
            queue = [start_pos]
            visited = {start_pos}
            count = 0
            while queue:
                curr = queue.pop(0)
                count += 1
                if count > 30:  # Cap the BFS to keep it fast
                    break
                for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                    nx, ny = curr[0] + dx, curr[1] + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if (nx, ny) not in obstacle_positions and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
            return count

        # Find food target
        food = board.get("food", [])
        if food:
            closest_food = min(food, key=lambda f: _manhattan(head, (f["x"], f["y"])))
            target = (closest_food["x"], closest_food["y"])
        else:
            target = (width // 2, height // 2)

        # We will rank moves first by reachable area (avoiding traps), then by distance to target.
        # Specifically: group choices by whether they have enough space (e.g., space >= my_length),
        # or just maximize space if all have less.
        move_scores = []
        for d, pos in choices.items():
            space = get_reachable_area(pos)
            dist = _manhattan(pos, target)
            move_scores.append((d, space, dist))

        # Sort moves:
        # 1. Primary key: Whether they have sufficient space (e.g., >= min(my_length, 15)). If yes, they are equal.
        # 2. Secondary key: Manhattan distance to target (closer is better)
        # 3. Tertiary key: Actual space (more is better, as a tie-breaker or fallback if space is insufficient)
        min_space_needed = min(my_length, 15)
        
        def rank_move(item):
            d, space, dist = item
            has_enough_space = 1 if space >= min_space_needed else 0
            # We want: has_enough_space (descending -> -has_enough_space),
            # dist (ascending), space (descending -> -space)
            return (-has_enough_space, dist, -space)

        move_scores.sort(key=rank_move)
        best_move = move_scores[0][0]

        return {"move": best_move}

    except Exception:
        return {"move": "up"}

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
