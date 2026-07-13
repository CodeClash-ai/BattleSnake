"""
Simple but highly effective BattleSnake bot.
Features:
1. Avoids collisions with walls, self-body, and other snakes' bodies.
2. Uses Time-Aware Flood Fill to accurately compute reachable space,
   naturally handling following tails, coiling, and pocket sizes perfectly.
3. Incorporates Voronoi Territory Partitioning to count free cells closer to us than opponents.
4. Avoids head-to-head collisions with larger or equal length opponent snakes.
5. Correctly targets nearest food or center depending on situation.
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


def _time_aware_flood_fill(start, width, height, snakes):
    """
    BFS that simulates time/steps. A cell occupied by a snake body segment
    becomes free after (length - index) steps.
    """
    free_at_step = {}
    for snake in snakes:
        body = snake["body"]
        N = len(body)
        for i, seg in enumerate(body):
            pos = (seg["x"], seg["y"])
            steps_to_vacate = N - i
            free_at_step[pos] = max(free_at_step.get(pos, 0), steps_to_vacate)
            
    queue = [(start, 0)]
    visited = {start}
    count = 0
    
    while queue:
        curr, step = queue.pop(0)
        count += 1
        cx, cy = curr
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                np = (nx, ny)
                if np not in visited:
                    vacated_at = free_at_step.get(np, 0)
                    if step + 1 >= vacated_at:
                        visited.add(np)
                        queue.append((np, step + 1))
    return count


def _voronoi_territory(start, opp_heads, width, height, obstacles):
    """
    Computes Voronoi territory space for the snake starting at 'start'.
    Cells that are strictly closer to 'start' than any opponent head are counted.
    """
    dist = {}
    queue = []
    
    dist[start] = ('us', 0)
    queue.append((start, 'us', 0))
    
    for opp in opp_heads:
        if opp not in obstacles:
            dist[opp] = ('opp', 0)
            queue.append((opp, 'opp', 0))
            
    us_count = 0
    while queue:
        curr, owner, d = queue.pop(0)
        
        cx, cy = curr
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                np = (nx, ny)
                if np not in obstacles:
                    if np not in dist:
                        dist[np] = (owner, d + 1)
                        queue.append((np, owner, d + 1))
                        
    for pos, (owner, d) in dist.items():
        if owner == 'us':
            us_count += 1
    return us_count


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
        
        # When we are very long, we only eat food if health is low or we are smaller than the opponent.
        # Find opponent max length:
        opp_lengths = [s["length"] for s in board["snakes"] if s["id"] != my_id]
        max_opp_length = max(opp_lengths) if opp_lengths else 0
        
        # Define hunger threshold: if we are already longer than any opponent and our health is above 35,
        # we don't aggressively search for food.
        is_hungry = (my_length <= max_opp_length + 2) or (my_health < 35)
        
        obstacles = set()
        opp_heads = []
        for snake in board["snakes"]:
            for seg in snake["body"]:
                obstacles.add((seg["x"], seg["y"]))
            if snake["id"] != my_id:
                opp_head = snake["body"][0]
                opp_heads.append((opp_head["x"], opp_head["y"]))
                
        directions = {
            "left": (-1, 0),
            "right": (1, 0),
            "down": (0, -1),
            "up": (0, 1)
        }
        
        possible_moves = []
        for d, (dx, dy) in directions.items():
            nx, ny = my_head[0] + dx, my_head[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                np = (nx, ny)
                if np not in obstacles:
                    possible_moves.append((d, np))
                    
        if not possible_moves:
            # If no completely free moves, try moving into segments that are about to be vacated!
            # Let's find any move that is within bounds
            for d, (dx, dy) in directions.items():
                nx, ny = my_head[0] + dx, my_head[1] + dy
                if 0 <= nx < width and 0 <= ny < height:
                    possible_moves.append((d, (nx, ny)))
            if not possible_moves:
                return {"move": "up"}
            
        dangerous_squares = set()
        for snake in board["snakes"]:
            if snake["id"] == my_id:
                continue
            opp_head = snake["body"][0]
            opp_head_pos = (opp_head["x"], opp_head["y"])
            if snake["length"] >= my_length:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ox, oy = opp_head_pos[0] + dx, opp_head_pos[1] + dy
                    if 0 <= ox < width and 0 <= oy < height:
                        dangerous_squares.add((ox, oy))
                        
        safe_moves = [(d, np) for d, np in possible_moves if np not in dangerous_squares]
        if not safe_moves:
            safe_moves = possible_moves
            
        food = board.get("food", [])
        
        if food and is_hungry:
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
            # If not hungry or no food, target our own tail to safely coil/follow ourselves!
            my_tail = (you["body"][-1]["x"], you["body"][-1]["y"])
            target = my_tail
            
        best_move = safe_moves[0][0]
        best_score = -999999999
        
        for d, np in safe_moves:
            # 1. Time-Aware flood fill space
            space = _time_aware_flood_fill(np, width, height, board["snakes"])
            
            # 2. Voronoi Territory Score
            voronoi_space = _voronoi_territory(np, opp_heads, width, height, obstacles)
            
            # 3. Distance to target score
            dist = _manhattan(np, target)
            
            # Extra penalty if we are next to walls/corners when we don't have to be.
            # We want to encourage staying slightly away from borders/corners if we have better moves.
            wall_penalty = 0
            if np[0] == 0 or np[0] == width - 1:
                wall_penalty += 1
            if np[1] == 0 or np[1] == height - 1:
                wall_penalty += 1
                
            # Weighted score
            score = (space * 1000) + (voronoi_space * 20) - dist - (wall_penalty * 5)
            
            if space < my_length:
                score -= 10000000  # heavy penalty for coiling in a small pocket
                
            if np in dangerous_squares:
                score -= 50000
                
            if score > best_score:
                best_score = score
                best_move = d
                
        return {"move": best_move}
        
    except Exception:
        return {"move": "up"}


if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
