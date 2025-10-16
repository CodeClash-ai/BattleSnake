def get_obstacles(game_state: typing.Dict, for_flood_fill: bool = False) -> set:
    """Returns a set of all obstacle coordinates."""
    obstacles = set()
    my_id = game_state['you']['id']
    food_coords = { (food['x'], food['y']) for food in game_state['board']['food'] }

    for snake in game_state['board']['snakes']:
        # Add the entire body of the snake to obstacles
        for part in snake['body']:
            obstacles.add((part['x'], part['y']))
        
        # If it's an opponent snake and it did not just eat, its tail is not an obstacle.
        if snake['id'] != my_id:
            if len(snake['body']) > 1:
                head = snake['body'][0]
                if (head['x'], head['y']) not in food_coords:
                    tail = snake['body'][-1]
                    obstacles.discard((tail['x'], tail['y']))
    
    # For our own snake, the tail is never an obstacle for the next move unless we're doing flood_fill.
    if not for_flood_fill and len(game_state['you']['body']) > 1:
        my_tail = game_state['you']['body'][-1]
        obstacles.discard((my_tail['x'], my_tail['y']))
            
    return obstacles

