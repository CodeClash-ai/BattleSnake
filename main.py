"""
Simple but robust Battlesnake implementation.
Avoids self-collision, wall-collision, and collision with other snakes.
Prefers nearest food when health is low or there are no other constraints,
otherwise navigates safely, potentially to the center or safely away from hazards.
"""

def info():
    return {
        "apiversion": "1",
        "author": "gemini-3-5-flash-improved",
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


def move(game_state):
    try:
        board = game_state["board"]
        width, height = board["width"], board["height"]
        
        my_body = game_state["you"]["body"]
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
        # Note: We can also avoid other snakes' bodies.
        occupied = set()
        
        # Add walls to occupied or handle dynamically
        # For simplicity, we just filter out directions out of bounds.
        
        # Add all snakes bodies to occupied
        for snake in board.get("snakes", []):
            for seg in snake["body"]:
                occupied.add((seg["x"], seg["y"]))
                
        # Note: The tail of a snake might move out of the way in the next turn,
        # but for absolute safety we treat it as occupied unless we really have to.
        
        # Filter possible moves that are safe (in-bounds and not occupied)
        safe_moves = []
        for d, pos in directions.items():
            px, py = pos
            if 0 <= px < width and 0 <= py < height:
                if pos not in occupied:
                    safe_moves.append((d, pos))
                    
        # If no safe moves available, just try any in-bounds move as fallback
        if not safe_moves:
            for d, pos in directions.items():
                px, py = pos
                if 0 <= px < width and 0 <= py < height:
                    safe_moves.append((d, pos))
                    
        if not safe_moves:
            # Absolute fallback
            return {"move": "up"}
            
        # Strategy:
        # Choose a target: Nearest food if health is relatively low (< 50) or if we want to grow.
        # Otherwise, move towards the center or just target the closest food anyway (usually optimal).
        food = board.get("food", [])
        if food:
            # Find closest food
            target = None
            best_dist = float('inf')
            for f in food:
                fp = (f["x"], f["y"])
                d = _manhattan(head, fp)
                if d < best_dist:
                    best_dist = d
                    target = fp
        else:
            target = _board_center(width, height)
            
        # Select the safe move that gets us closest to the target
        best_move = safe_moves[0][0]
        best_move_dist = float('inf')
        for d, pos in safe_moves:
            dist = _manhattan(pos, target)
            if dist < best_move_dist:
                best_move_dist = dist
                best_move = d
                
        return {"move": best_move}
        
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
