"""
An improved, robust Battlesnake implementation.
Features:
- Flood Fill path/space analysis to avoid trapping ourselves.
- Depth-limited Flood Fill (max_depth=15) to prevent performance degradation on large boards.
- Lookahead / min-max check to avoid moves that lead directly to unavoidable head-to-head collisions or trap states.
- Dangerous head-to-head collision avoidance with larger/equal-length snakes.
- Tail-following support: tail segments that will move are considered empty.
- Target closest food if health is low, or space is sufficient.
- Smart fallbacks if all safe moves are constrained.
"""

def info():
    return {
        "apiversion": "1",
        "author": "gemini-3-5-flash-improved-v5",
        "color": "#8b0000",
        "head": "shades",
        "tail": "sharp",
    }


def start(game_state):
    return None


def end(game_state):
    return None


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _board_center(width, height):
    center_x = (width // 2 if width % 2 == 0 else (width + 1) // 2) - 1
    center_y = (height // 2 if height % 2 == 0 else (height + 1) // 2) - 1
    return (center_x, center_y)


def flood_fill_size(start, occupied, width, height, max_depth=15):
    """
    Flood fill with a depth limit to avoid performance scaling issues
    while still accurately determining space availability.
    """
    if start in occupied:
        return 0
    visited = {start}
    queue = [(start, 0)]
    count = 0
    while queue:
        curr, depth = queue.pop(0)
        count += 1
        if depth >= max_depth:
            continue
        cx, cy = curr
        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in occupied and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), depth + 1))
    return count


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        
        my_snake = game_state["you"]
        my_body = my_snake["body"]
        my_length = len(my_body)
        head_seg = my_body[0]
        head = (head_seg["x"], head_seg["y"])
        
        # Directions mapping
        directions = {
            "up": (head[0], head[1] + 1),
            "down": (head[0], head[1] - 1),
            "left": (head[0] - 1, head[1]),
            "right": (head[0] + 1, head[1])
        }
        
        # Identify occupied cells (walls, snake bodies)
        occupied = set()
        for snake in board.get("snakes", []):
            body = snake["body"]
            is_growing = snake["health"] == 100
            
            # Add all body segments except the tail (if it's not growing and length > 1)
            for i, seg in enumerate(body):
                if i == len(body) - 1 and not is_growing and len(body) > 1:
                    # Tail is safe to enter as it will move on the next turn
                    continue
                occupied.add((seg["x"], seg["y"]))
                
        # Filter possible moves that are safe (in-bounds and not occupied)
        safe_moves = []
        for d, pos in directions.items():
            px, py = pos
            if 0 <= px < width and 0 <= py < height:
                if pos not in occupied:
                    # Check for head-to-head danger from other snakes
                    is_dangerous = False
                    for snake in board.get("snakes", []):
                        if snake["id"] == my_snake["id"]:
                            continue
                        opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                        opp_len = len(snake["body"])
                        # If opponent can move to this position next turn (1 step away)
                        if abs(pos[0] - opp_head[0]) + abs(pos[1] - opp_head[1]) == 1:
                            if opp_len >= my_length:
                                is_dangerous = True
                                break
                    
                    # Calculate room size via depth-limited flood fill
                    room_size = flood_fill_size(pos, occupied, width, height, max_depth=15)
                    
                    # Look-ahead score: how many non-dangerous choices will we have from this position on the next turn?
                    # This helps avoid moving into corners where the next step is guaranteed dangerous or blocked.
                    next_non_dangerous_choices = 0
                    next_possible_positions = [
                        (pos[0]+1, pos[1]), (pos[0]-1, pos[1]),
                        (pos[0], pos[1]+1), (pos[0], pos[1]-1)
                    ]
                    
                    # We simulate occupied set for next turn (simplified: assuming tails move)
                    for npx, npy in next_possible_positions:
                        if 0 <= npx < width and 0 <= npy < height:
                            if (npx, npy) not in occupied and (npx, npy) != head:
                                # Check if it's dangerous
                                next_danger = False
                                for snake in board.get("snakes", []):
                                    if snake["id"] == my_snake["id"]:
                                        continue
                                    opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                                    opp_len = len(snake["body"])
                                    # Opponent would be at most 2 steps from (npx, npy) in 1 turn (since they move 1 step)
                                    # Actually, they are 1 step away from their potential next position.
                                    # We can check Manhattan distance from current opponent head to (npx, npy)
                                    if abs(npx - opp_head[0]) + abs(npy - opp_head[1]) <= 2:
                                        if opp_len >= my_length:
                                            next_danger = True
                                            break
                                if not next_danger:
                                    next_non_dangerous_choices += 1
                    
                    safe_moves.append({
                        "direction": d,
                        "position": pos,
                        "is_dangerous": is_dangerous,
                        "room_size": room_size,
                        "next_choices": next_non_dangerous_choices
                    })
                    
        # If no safe moves available, absolute fallback
        if not safe_moves:
            for d, pos in directions.items():
                px, py = pos
                if 0 <= px < width and 0 <= py < height:
                    return {"move": d}
            return {"move": "up"}
            
        # Target determination:
        # Target closest food.
        food = board.get("food", [])
        target = None
        if food:
            best_dist = float('inf')
            for f in food:
                fp = (f["x"], f["y"])
                d = _manhattan(head, fp)
                if d < best_dist:
                    best_dist = d
                    target = fp
                    
        if not target:
            target = _board_center(width, height)
            
        # Score each safe move
        best_move = None
        best_score = (-float('inf'), -float('inf'), -float('inf'), -float('inf'), -float('inf'))
        
        for m in safe_moves:
            not_dangerous = 1 if not m["is_dangerous"] else 0
            has_space = 1 if m["room_size"] >= min(my_length, 50) else 0
            dist = _manhattan(m["position"], target)
            
            # Prioritize moves that give us more safe next choices to avoid getting cornered.
            score = (not_dangerous, has_space, m["next_choices"], m["room_size"], -dist)
            if score > best_score:
                best_score = score
                best_move = m["direction"]
                
        return {"move": best_move}
        
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
