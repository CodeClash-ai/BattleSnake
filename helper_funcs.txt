def find_shortest_path(start_coord: dict, end_coord: dict, game_state: typing.Dict) -> typing.Optional[list]:
    """Finds the shortest path between two coordinates using BFS."""
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    # Use obstacles for pathfinding, but our own head isn't an obstacle for the starting point
    obstacles = get_obstacles(game_state, for_flood_fill=True, coord_to_ignore=start_coord)

    q = deque([[start_coord]])
    visited = {(start_coord['x'], start_coord['y'])}

    end_tuple = (end_coord['x'], end_coord['y'])

    while q:
        path = q.popleft()
        curr = path[-1]
        
        if (curr['x'], curr['y']) == end_tuple:
            return path

        for move in ["up", "down", "left", "right"]:
            next_coord = get_next_move_coord(curr, move)
            if (next_coord['x'], next_coord['y']) not in visited and is_coord_safe(next_coord, board_width, board_height, obstacles):
                visited.add((next_coord['x'], next_coord['y']))
                new_path = list(path)
                new_path.append(next_coord)
                q.append(new_path)
    return None


def get_best_food_move(game_state: typing.Dict, safe_moves_with_area: list) -> typing.Optional[str]:
    """Finds the best food to chase and returns the move towards it."""
    my_head = game_state["you"]["body"][0]
    food_list = game_state["board"]["food"]
    
    best_food_info = {
        "path_len": float('inf'),
        "move": None,
        "area": -1,
        "score": -1
    }
    
    safe_moves = [m for m, a in safe_moves_with_area]
    # Don't bother if there are no safe moves to begin with
    if not safe_moves:
        return None

    for food in food_list:
        path = find_shortest_path(my_head, food, game_state)
        if path and len(path) > 1:
            path_len = len(path) - 1 # Number of moves
            first_move_coord = path[1]

            move_str = None
            if first_move_coord['x'] < my_head['x']: move_str = 'left'
            elif first_move_coord['x'] > my_head['x']: move_str = 'right'
            elif first_move_coord['y'] < my_head['y']: move_str = 'down'
            elif first_move_coord['y'] > my_head['y']: move_str = 'up'

            if move_str and move_str in safe_moves:
                move_area = 0
                for move, area in safe_moves_with_area:
                    if move == move_str:
                        move_area = area
                        break

                # Score: prioritize larger areas, penalize longer paths.
                # Add a small epsilon to avoid division by zero.
                score = move_area / (path_len + 0.1)

                if score > best_food_info["score"]:
                    best_food_info["score"] = score
                    best_food_info["path_len"] = path_len
                    best_food_info["move"] = move_str
                    best_food_info["area"] = move_area
    
    # Only return a move if we found a viable food target
    if best_food_info["move"]:
        print(f"Best food move: {best_food_info['move']} (path len: {best_food_info['path_len']}, area: {best_food_info['area']}, score: {best_food_info['score']:.2f})")
        return best_food_info["move"]
    
    return None
