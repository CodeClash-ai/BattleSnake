
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

# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing
from collections import deque

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


# start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME START")


# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")

def get_next_move_coord(head: dict, move: str) -> dict:
    """Returns the coordinates for a given move."""
    moves = {
        "up": {"x": head["x"], "y": head["y"] + 1},
        "down": {"x": head["x"], "y": head["y"] - 1},
        "left": {"x": head["x"] - 1, "y": head["y"]},
        "right": {"x": head["x"] + 1, "y": head["y"]},
    }
    return moves.get(move, head)

def is_coord_safe(coord: dict, board_width: int, board_height: int, obstacles: set) -> bool:
    """Checks if a given coordinate is safe."""
    x, y = coord['x'], coord['y']
    if not (0 <= x < board_width and 0 <= y < board_height):
        return False
    if (x, y) in obstacles:
        return False
    return True

def get_obstacles(game_state: typing.Dict, for_flood_fill: bool = False, coord_to_ignore: dict = None) -> set:
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
def is_tail_safe(start_coord: dict, game_state: typing.Dict) -> bool:
    """Checks if the snake's tail can reach its head after a move."""
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    my_head = game_state['you']['body'][0]
    obstacles = get_obstacles(game_state, for_flood_fill=True, coord_to_ignore=my_head)
    
    q = deque([start_coord])
    visited = { (start_coord['x'], start_coord['y']) }

    while q:
        curr = q.popleft()
        if curr['x'] == my_head['x'] and curr['y'] == my_head['y']:
            return True

        for move in ["up", "down", "left", "right"]:
            next_coord = get_next_move_coord(curr, move)
            if (next_coord['x'], next_coord['y']) not in visited and is_coord_safe(next_coord, board_width, board_height, obstacles):
                visited.add((next_coord['x'], next_coord['y']))
                q.append(next_coord)
    return False

def flood_fill(start_coord: dict, game_state: typing.Dict, my_head: dict) -> int:
    """Calculates the number of reachable safe squares from a starting coordinate."""
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    obstacles = get_obstacles(game_state, for_flood_fill=True, coord_to_ignore=my_head)
    
    if not is_coord_safe(start_coord, board_width, board_height, obstacles):
        return 0

    q = deque([start_coord])
    visited = { (start_coord['x'], start_coord['y']) }
    count = 0
    
    while q:
        curr = q.popleft()
        count += 1

        for move in ["up", "down", "left", "right"]:
            next_coord = get_next_move_coord(curr, move)
            if (next_coord['x'], next_coord['y']) not in visited and is_coord_safe(next_coord, board_width, board_height, obstacles):
                visited.add((next_coord['x'], next_coord['y']))
                q.append(next_coord)
    
    return count

def is_safe_from_head_collision(next_coord: dict, game_state: typing.Dict) -> bool:
    """Checks if a coordinate is at risk of a head-to-head collision."""
    my_len = len(game_state["you"]["body"])
    for snake in game_state["board"]["snakes"]:
        if snake["id"] == game_state["you"]["id"]:
            continue
        opp_head = snake["body"][0]
        opp_len = len(snake["body"])
        if my_len <= opp_len:
            # Check opponent's possible moves
            for opp_move in ["up", "down", "left", "right"]:
                opp_next_coord = get_next_move_coord(opp_head, opp_move)
                if opp_next_coord["x"] == next_coord["x"] and opp_next_coord["y"] == next_coord["y"]:
                    print(f"HEAD-TO-HEAD RISK at {next_coord} with snake {snake['id']}")
                    return False
    return True

def is_move_safe_for_opponent(snake: dict, next_coord: dict, game_state: typing.Dict) -> bool:
    """Checks if a move is safe for a given opponent snake."""
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    
    # We need a fresh obstacle set for this check
    obstacles = set()
    for s in game_state['board']['snakes']:
        for i, body_part in enumerate(s['body']):
            # The opponent's own tail is not an obstacle for their next move
            if i == len(s['body']) - 1:
                continue
            obstacles.add((body_part['x'], body_part['y']))

    # 1. Check for body and wall collisions
    if not is_coord_safe(next_coord, board_width, board_height, obstacles):
        return False

    # 2. Check for head-to-head collisions from the opponent's perspective
    opp_len = len(snake["body"])
    for other_snake in game_state["board"]["snakes"]:
        if other_snake["id"] == snake["id"]:
            continue
        
        other_head = other_snake["body"][0]
        other_len = len(other_snake["body"])
        
        if opp_len <= other_len:
            # Check other snake's possible moves
            for other_move in ["up", "down", "left", "right"]:
                other_next_coord = get_next_move_coord(other_head, other_move)
                if other_next_coord["x"] == next_coord["x"] and other_next_coord["y"] == next_coord["y"]:
                    return False
    
    return True

def move(game_state: typing.Dict) -> typing.Dict:
    next_move = "up"  # Default move
    my_head = game_state["you"]["body"][0]
    my_neck = game_state["you"]["body"][1]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    obstacles = get_obstacles(game_state)

    possible_moves = ["up", "down", "left", "right"]

    if my_neck["x"] < my_head["x"]: possible_moves.remove("left")
    elif my_neck["x"] > my_head["x"]: possible_moves.remove("right")
    elif my_neck["y"] < my_head["y"]: possible_moves.remove("down")
    elif my_neck["y"] > my_head["y"]: possible_moves.remove("up")
    
    safe_moves = []
    spatially_safe_moves = []
    for move in possible_moves:
        next_coord = get_next_move_coord(my_head, move)
        if is_coord_safe(next_coord, board_width, board_height, obstacles):
            spatially_safe_moves.append(move)

    if not spatially_safe_moves:
        print(f"MOVE {game_state['turn']}: Trapped! No spatially safe moves. Moving down.")
        return {"move": "down"}
    
    # Now, find moves that are also safe from head-to-head collisions
    head_safe_moves = []
    for move in spatially_safe_moves:
        next_coord = get_next_move_coord(my_head, move)
        if is_safe_from_head_collision(next_coord, game_state):
            head_safe_moves.append(move)

    safe_moves = []
    if head_safe_moves:
        safe_moves = head_safe_moves
    else:
        print(f"MOVE {game_state['turn']}: No head-safe moves, considering all spatially safe moves as risky.")
        safe_moves = spatially_safe_moves

    safe_moves_with_area = []
    for move in safe_moves:
        next_coord = get_next_move_coord(my_head, move)
        area = flood_fill(next_coord, game_state, my_head)
        safe_moves_with_area.append((move, area))

    # Choose the move with the most available space
    if safe_moves_with_area:
        safe_moves_with_area.sort(key=lambda x: x[1], reverse=True)
    if safe_moves_with_area:
        next_move = safe_moves_with_area[0][0]
# Tail safety check to prevent self-trapping
    tail_safe_moves = []
    for move, area in safe_moves_with_area:
        next_coord = get_next_move_coord(my_head, move)
        # Create a hypothetical next game state
        hypothetical_body = [next_coord] + game_state['you']['body'][:-1]
        hypothetical_game_state = game_state.copy()
        hypothetical_game_state['you'] = game_state['you'].copy()
        hypothetical_game_state['you']['body'] = hypothetical_body
        hypothetical_game_state['you']['head'] = next_coord

        # Check if the tail can still reach the new head
        if is_tail_safe(hypothetical_body[-1], hypothetical_game_state):
            tail_safe_moves.append((move, area))

    if tail_safe_moves:
        print(f"Found {len(tail_safe_moves)} tail-safe moves.")
        safe_moves_with_area = tail_safe_moves
        next_move = safe_moves_with_area[0][0]

    # Aggressive mode
    attack_move = None
    my_len = len(game_state["you"]["body"])

    # Cut-off move logic
    potential_cutoff_moves = {}
    
    # Find all possible cut-off moves
    for move_option, area in safe_moves_with_area:
        next_coord = get_next_move_coord(my_head, move_option)
        for snake in game_state["board"]["snakes"]:
            if snake["id"] != game_state["you"]["id"] and my_len > len(snake["body"]):
                opp_head = snake["body"][0]
                
                # Predict opponent's possible moves
                opp_possible_moves = ["up", "down", "left", "right"]
                if len(snake["body"]) > 1:
                    opp_neck = snake["body"][1]
                    if opp_neck["x"] < opp_head["x"]: opp_possible_moves.remove("left")
                    elif opp_neck["x"] > opp_head["x"]: opp_possible_moves.remove("right")
                    elif opp_neck["y"] < opp_head["y"]: opp_possible_moves.remove("down")
                    elif opp_neck["y"] > opp_head["y"]: opp_possible_moves.remove("up")

                for opp_move in opp_possible_moves:
                    opp_next_coord = get_next_move_coord(opp_head, opp_move)
                    # Check if our move intercepts one of their potential moves
                    if next_coord['x'] == opp_next_coord['x'] and next_coord['y'] == opp_next_coord['y']:
                         # Make sure the opponent's move would be "safe" for them, otherwise it's not a real path
                        if is_move_safe_for_opponent(snake, opp_next_coord, game_state):
                            if move_option not in potential_cutoff_moves:
                                potential_cutoff_moves[move_option] = []
                            potential_cutoff_moves[move_option].append(snake['id'])

    # Choose the best cut-off move. The one that cuts off the most snakes,
    # and as a tie-breaker, the one that gives us more space.
    # `safe_moves_with_area` is already sorted by area.
    if potential_cutoff_moves:
        best_cutoff_move = None
        max_cutoff_count = 0
        for move_option, area in safe_moves_with_area:
            if move_option in potential_cutoff_moves:
                cutoff_count = len(potential_cutoff_moves[move_option])
                if cutoff_count > max_cutoff_count:
                    max_cutoff_count = cutoff_count
                    best_cutoff_move = move_option
        if best_cutoff_move:
            attack_move = best_cutoff_move
            print(f"Found cut-off move {attack_move}, cutting off {max_cutoff_count} snake(s)")


    if attack_move:
        next_move = attack_move
    else:
        # Fallback to original adjacent-based aggressive mode
        for move_option, area in safe_moves_with_area:
            next_coord = get_next_move_coord(my_head, move_option)
            for snake in game_state["board"]["snakes"]:
                if snake["id"] != game_state["you"]["id"] and my_len > len(snake["body"]):
                    opp_head = snake["body"][0]
                    if abs(next_coord['x'] - opp_head['x']) + abs(next_coord['y'] - opp_head['y']) == 1:
                        print(f"Found adjacent attack move {move_option} towards snake {snake['id']}")
                        attack_move = move_option
                        break 
            if attack_move:
                break
        
        if attack_move:
            next_move = attack_move
        else:
            # Determine if we are the longest snake
            my_len = len(game_state["you"]["body"])
            is_longest_snake = True
            for snake in game_state["board"]["snakes"]:
                if snake["id"] != game_state["you"]["id"]:
                    if len(snake["body"]) >= my_len:
                        is_longest_snake = False
                        break
    
            # Food-seeking logic, only if not attacking
            my_health = game_state['you']['health']
            food = game_state['board']['food']
            
            if food and (my_health < 80 or is_longest_snake):
                closest_food = min(food, key=lambda f: abs(my_head['x'] - f['x']) + abs(my_head['y'] - f['y']))
                distance_to_food = abs(my_head['x'] - closest_food['x']) + abs(my_head['y'] - closest_food['y'])

                # Only chase food if it's reasonably close, or if we are very hungry
                if distance_to_food < 7 or my_health < 25:
                    preferred_moves = []
                    if closest_food['x'] < my_head['x'] and 'left' in safe_moves: preferred_moves.append('left')
                    if closest_food['x'] > my_head['x'] and 'right' in safe_moves: preferred_moves.append('right')
                    if closest_food['y'] < my_head['y'] and 'down' in safe_moves: preferred_moves.append('down')
                    if closest_food['y'] > my_head['y'] and 'up' in safe_moves: preferred_moves.append('up')
                    
                    if preferred_moves:
                        best_food_move = preferred_moves[0]
                        max_area = -1
                        for p_move in preferred_moves:
                            for move, area in safe_moves_with_area:
                                if p_move == move and area > max_area:
                                    max_area = area
                                    best_food_move = p_move
                        next_move = best_food_move

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}

if __name__ == "__main__":
    from server import run_server
    run_server({"info": info, "start": start, "move": move, "end": end})
