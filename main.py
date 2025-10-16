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

def get_obstacles(game_state: typing.Dict, for_flood_fill: bool = False) -> set:
    """Returns a set of all obstacle coordinates."""
    obstacles = set()
    my_id = game_state['you']['id']
    
    for snake in game_state['board']['snakes']:
        for i, body_part in enumerate(snake['body']):
            # For our snake, if not for flood fill, the tail is not an obstacle for the next move
            if not for_flood_fill and snake['id'] == my_id and i == len(snake['body']) - 1:
                continue
            obstacles.add((body_part['x'], body_part['y']))
            
    return obstacles

def flood_fill(start_coord: dict, game_state: typing.Dict) -> int:
    """Calculates the number of reachable safe squares from a starting coordinate."""
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    obstacles = get_obstacles(game_state, for_flood_fill=True)
    
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

def move(game_state: typing.Dict) -> typing.Dict:
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

    safe_moves_with_area = []
    for move_option in possible_moves:
        next_coord = get_next_move_coord(my_head, move_option)
        if is_coord_safe(next_coord, board_width, board_height, obstacles):
            area = flood_fill(next_coord, game_state)
            safe_moves_with_area.append((move_option, area))

    if not safe_moves_with_area:
        print(f"MOVE {game_state['turn']}: No safe moves! Moving down.")
        return {"move": "down"}

    safe_moves_with_area.sort(key=lambda x: x[1], reverse=True)
    safe_moves = [move for move, area in safe_moves_with_area]
    next_move = safe_moves[0]

    my_health = game_state['you']['health']
    food = game_state['board']['food']
    
    if food and my_health < 50:
        closest_food = min(food, key=lambda f: abs(my_head['x'] - f['x']) + abs(my_head['y'] - f['y']))
        
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
