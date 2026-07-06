"""
An improved, robust Battlesnake implementation.
Features:
- Flood Fill path/space analysis to avoid trapping ourselves.
- Dangerous head-to-head collision avoidance with larger/equal-length snakes.
- Tail-following support: tail segments that will move are considered empty.
- Target closest food if health is low, or space is sufficient.
- Smart fallbacks if all safe moves are constrained.
"""

def info():
    return {
        "apiversion": "1",
        "author": "gemini-3-5-flash-improved-v3",
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


def flood_fill_size(start, occupied, width, height):
    if start in occupied:
        return 0
    visited = {start}
    queue = [start]
    count = 0
    while queue:
        curr = queue.pop(0)
        count += 1
        cx, cy = curr
        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in occupied and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
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
        # Note: A snake's tail segment is safe to enter if the snake is not growing.
        # A snake grows if its health is at 100 (which means it just ate) AND its length is > 1.
        # To be safe, if a snake's length is > 1, and its health is < 100, we can treat its tail segment as empty.
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
                    
                    # Calculate room size via flood fill
                    room_size = flood_fill_size(pos, occupied, width, height)
                    
                    safe_moves.append({
                        "direction": d,
                        "position": pos,
                        "is_dangerous": is_dangerous,
                        "room_size": room_size
                    })
                    
        # If no safe moves available, absolute fallback
        if not safe_moves:
            # Let's try to move in-bounds to anything that doesn't instantly kill us if possible, or just in-bounds
            for d, pos in directions.items():
                px, py = pos
                if 0 <= px < width and 0 <= py < height:
                    return {"move": d}
            return {"move": "up"}
            
        # Prioritize moves:
        # 1. Prefer non-dangerous moves
        # 2. Prefer moves that leave enough room for our entire body (room_size >= my_length)
        # 3. Choose the move that gets us closest to the target (food or center)
        
        # Target determination:
        # If health is low (< 40) or we are not the longest snake, target food.
        # Otherwise, we can still target food or the center of the board to control space.
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
        best_score = (-float('inf'), -float('inf'), -float('inf'), -float('inf')) # (not_dangerous, has_space, room_size, -distance)
        
        for m in safe_moves:
            not_dangerous = 1 if not m["is_dangerous"] else 0
            # Check if we have enough room to not get trapped.
            # Ideally we want room_size >= my_length, but even if not, more room is better.
            has_space = 1 if m["room_size"] >= my_length else 0
            
            dist = _manhattan(m["position"], target)
            
            score = (not_dangerous, has_space, m["room_size"], -dist)
            if score > best_score:
                best_score = score
                best_move = m["direction"]
                
        return {"move": best_move}
        
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
