"""
Simple but highly effective BattleSnake bot.
Features:
1. Avoids collisions with walls, self-body, and other snakes' bodies.
2. If multiple safe moves exist:
   - Evaluates each safe move for future space (simple flood-fill/accessibility heuristic or check of immediate neighbors).
   - Targets food when health is low or we want to grow, but prefers the NEAREST food instead of the FARTHEST food!
   - Prefers to avoid moving into a space where an opponent's larger head could move (head-to-head collision avoidance).
"""

def info():
    return {
        "apiversion": "1",
        "author": "gemini-3-5-flash",
        "color": "#00ffcc",
        "head": "beluga",
        "tail": "bolt",
    }


def start(game_state):
    pass


def end(game_state):
    pass


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _board_center(width, height):
    center_x = (width // 2 if width % 2 == 0 else (width + 1) // 2) - 1
    center_y = (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1
    return (center_x, center_y)


def _flood_fill(start, width, height, obstacles):
    """Simple BFS to count reachable squares from start position."""
    queue = [start]
    visited = {start}
    count = 0
    while queue:
        curr = queue.pop(0)
        count += 1
        cx, cy = curr
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                np = (nx, ny)
                if np not in obstacles and np not in visited:
                    visited.add(np)
                    queue.append(np)
    return count


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        
        you = game_state["you"]
        my_id = you["id"]
        my_head_seg = you["body"][0]
        my_head = (my_head_seg["x"], my_head_seg["y"])
        my_length = you["length"]
        my_health = you["health"]
        
        # Build set of obstacles (all snake body segments, except their tails if they are not growing,
        # but to be extremely safe, we treat all body segments as solid obstacles).
        obstacles = set()
        for snake in board["snakes"]:
            # Standard rule: tail moves unless they ate. If we want to be safe, just avoid all parts.
            for seg in snake["body"]:
                obstacles.add((seg["x"], seg["y"]))
                
        # Directions
        directions = {
            "left": (-1, 0),
            "right": (1, 0),
            "down": (0, -1),
            "up": (0, 1)
        }
        
        # Check moves
        possible_moves = []
        for d, (dx, dy) in directions.items():
            nx, ny = my_head[0] + dx, my_head[1] + dy
            # Check boundaries
            if 0 <= nx < width and 0 <= ny < height:
                np = (nx, ny)
                # Check obstacles
                if np not in obstacles:
                    possible_moves.append((d, np))
                    
        if not possible_moves:
            # Doom, just go up
            return {"move": "up"}
            
        # Avoid head-to-head collisions with larger/equal snakes if possible
        dangerous_squares = set()
        for snake in board["snakes"]:
            if snake["id"] == my_id:
                continue
            opp_head = snake["body"][0]
            opp_head_pos = (opp_head["x"], opp_head["y"])
            # If opponent is larger or equal in length, their potential next moves are dangerous
            if snake["length"] >= my_length:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ox, oy = opp_head_pos[0] + dx, opp_head_pos[1] + dy
                    if 0 <= ox < width and 0 <= oy < height:
                        dangerous_squares.add((ox, oy))
                        
        # Filter possible moves that do not lead to dangerous head-to-head squares
        safe_moves = [(d, np) for d, np in possible_moves if np not in dangerous_squares]
        if not safe_moves:
            # If all standard moves lead to danger, just fall back to standard possible moves
            safe_moves = possible_moves
            
        # Target evaluation
        food = board.get("food", [])
        if food:
            # Find NEAREST food (correcting the original's farthest food bug!)
            target_food = None
            min_dist = 9999
            for f in food:
                fp = (f["x"], f["y"])
                dist = _manhattan(my_head, fp)
                if dist < min_dist:
                    min_dist = dist
                    target_food = fp
            target = target_food
        else:
            target = _board_center(width, height)
            
        # Score each safe move
        best_move = safe_moves[0][0]
        best_score = -999999
        
        for d, np in safe_moves:
            # 1. Flood fill score (extremely important to not get trapped)
            space = _flood_fill(np, width, height, obstacles)
            
            # 2. Distance to target score (closer is better, so negative distance)
            dist = _manhattan(np, target)
            
            # Weighted score: heavily prioritize having enough space, then move towards target
            # Each square of space is worth a lot (e.g., 100 points).
            # Max possible space is ~121 on an 11x11 board.
            score = (space * 1000) - dist
            
            # Slight bonus for avoiding head-to-head squares even in fallback scenarios
            if np in dangerous_squares:
                score -= 500
                
            if score > best_score:
                best_score = score
                best_move = d
                
        return {"move": best_move}
        
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
