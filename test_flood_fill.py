def get_safe_moves(game_state):
    board = game_state["board"]
    width, height = board["width"], board["height"]
    my_body = game_state["you"]["body"]
    head = (my_body[0]["x"], my_body[0]["y"])
    
    directions = {
        "up": (head[0], head[1] + 1),
        "down": (head[0], head[1] - 1),
        "left": (head[0] - 1, head[1]),
        "right": (head[0] + 1, head[1])
    }
    
    occupied = set()
    for snake in board.get("snakes", []):
        # The tail of a snake will move on the next step UNLESS they just ate.
        # But for safety, let's treat body as occupied.
        # Note: we can ignore the tail if the snake did not eat, but treating as occupied is safer.
        # Let's keep it simple:
        for seg in snake["body"][:-1]:
            occupied.add((seg["x"], seg["y"]))
        # Keep tail occupied if health is 100 (just ate) or length is < 3 or it ate food in previous turn?
        # Actually, let's just include the whole body to be safe, except the very tail if we want to be fancy.
        # Let's include the whole body for now.
        for seg in snake["body"]:
            occupied.add((seg["x"], seg["y"]))

    safe_moves = []
    for d, pos in directions.items():
        px, py = pos
        if 0 <= px < width and 0 <= py < height:
            if pos not in occupied:
                # Basic head-to-head danger check:
                # If an opponent snake's head is 1 step away from `pos` and they are longer than us or equal length,
                # it's a dangerous cell.
                is_dangerous = False
                for snake in board.get("snakes", []):
                    if snake["id"] == game_state["you"]["id"]:
                        continue
                    opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                    opp_len = len(snake["body"])
                    my_len = len(my_body)
                    if abs(pos[0] - opp_head[0]) + abs(pos[1] - opp_head[1]) == 1:
                        if opp_len >= my_len:
                            is_dangerous = True
                            break
                safe_moves.append((d, pos, is_dangerous))
    return safe_moves

def flood_fill_size(start, occupied, width, height):
    # Counts reachable cells from start
    if start in occupied:
        return 0
    visited = set([start])
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
