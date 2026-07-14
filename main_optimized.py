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
        my_tail = (my_body[-1]["x"], my_body[-1]["y"])

        # Create quick lookup of my body segment indices to avoid repeated index lookups
        my_body_indices = {}
        for idx, seg in enumerate(my_body):
            pt = (seg["x"], seg["y"])
            if pt not in my_body_indices:
                my_body_indices[pt] = idx

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
        obstacle_positions = set()
        for s in board["snakes"]:
            body_segs = s["body"]
            is_growing = (s["health"] == 100) # Simple approximation of growth
            # If growing, the tail remains in place. Otherwise, the last segment will move.
            active_body = body_segs if is_growing else body_segs[:-1]
            for seg in active_body:
                obstacle_positions.add((seg["x"], seg["y"]))

        # Filter out safe moves that collide with obstacles
        non_colliding_moves = {}
        for d, pos in safe_moves.items():
            if pos not in obstacle_positions:
                non_colliding_moves[d] = pos

        # 3. Head-to-Head Collision Avoidance:
        dangerous_head_moves = set()
        for s in board["snakes"]:
            if s["id"] == my_id:
                continue
            opp_head = (s["head"]["x"], s["head"]["y"])
            opp_length = len(s["body"])
            
            # If opponent is longer or equal to us, their potential next moves are dangerous
            if opp_length >= my_length:
                for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                    dangerous_head_moves.add((opp_head[0] + dx, opp_head[1] + dy))

        # Filter out dangerous head-to-head moves
        smart_moves = {}
        for d, pos in non_colliding_moves.items():
            if pos not in dangerous_head_moves:
                smart_moves[d] = pos

        # Fallback logic
        choices = smart_moves if smart_moves else (non_colliding_moves if non_colliding_moves else safe_moves)
        if not choices:
            return {"move": "up"}

        # 4. Flood fill & tail path checking:
        # We evaluate each choice by performing a BFS/flood-fill to count how many reachable cells exist from that move.
        def analyze_move(start_pos):
            queue = [start_pos]
            visited = {start_pos}
            count = 0
            can_reach_tail = False
            
            while queue:
                curr = queue.pop(0)
                count += 1
                
                # Check if we can reach our tail (which represents safety/looping potential)
                if curr == my_tail:
                    can_reach_tail = True
                
                # Performance limit: limit maximum nodes explored during BFS to avoid 500ms timeout.
                # Since Battlesnake board is usually 11x11 = 121 cells, 120 count is almost the whole board.
                # But when queue length is very large, or when checked frequently, we can bound it.
                # Since we do this for up to 4 moves, we should limit to e.g. 100.
                if count > 100:
                    if can_reach_tail:
                        break
                
                curr_x, curr_y = curr
                for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        n_cell = (nx, ny)
                        is_own_body_part_vacated = False
                        if n_cell in obstacle_positions:
                            # Use precomputed dictionary for O(1) body index lookup!
                            idx = my_body_indices.get(n_cell)
                            if idx is not None:
                                if my_length - idx <= len(visited):
                                    is_own_body_part_vacated = True

                        if n_cell == my_tail or is_own_body_part_vacated or (n_cell not in obstacle_positions and n_cell not in visited):
                            visited.add(n_cell)
                            queue.append(n_cell)
                            
            return count, can_reach_tail

        # Find food target
        food = board.get("food", [])
        if food:
            closest_food = min(food, key=lambda f: _manhattan(head, (f["x"], f["y"])))
            target = (closest_food["x"], closest_food["y"])
        else:
            target = (width // 2, height // 2)

        # We will rank moves first by safety (reachable area & tail reachability), then by distance to target.
        move_scores = []
        for d, pos in choices.items():
            space, can_reach_tail = analyze_move(pos)
            dist = _manhattan(pos, target)
            move_scores.append((d, space, can_reach_tail, dist))

        # Sort moves:
        min_space_needed = my_length
        
        def rank_move(item):
            d, space, can_reach_tail, dist = item
            # We prefer:
            # 1. Moves with enough space AND can reach tail
            # 2. Moves with enough space but cannot reach tail
            # 3. Moves with insufficient space but can reach tail
            # 4. Moves with insufficient space and cannot reach tail
            if space >= min_space_needed:
                if can_reach_tail:
                    return (0, dist, -space)
                else:
                    return (1, dist, -space)
            else:
                if can_reach_tail:
                    return (2, -space, dist)
                else:
                    return (3, -space, dist)

        move_scores.sort(key=rank_move)
        best_move = move_scores[0][0]

        return {"move": best_move}

    except Exception:
        return {"move": "up"}

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
