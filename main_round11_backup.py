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


def get_next_position(head: typing.Dict, move: str) -> typing.Dict:
    """Calculate the next position given a head position and move direction."""
    x, y = head["x"], head["y"]
    if move == "up":
        y += 1
    elif move == "down":
        y -= 1
    elif move == "left":
        x -= 1
    elif move == "right":
        x += 1
    return {"x": x, "y": y}


def is_out_of_bounds(pos: typing.Dict, board_width: int, board_height: int) -> bool:
    """Check if a position is out of bounds."""
    return pos["x"] < 0 or pos["x"] >= board_width or pos["y"] < 0 or pos["y"] >= board_height


def is_collision_with_snake(pos: typing.Dict, snake_body: typing.List[typing.Dict], exclude_tail: bool = False) -> bool:
    """Check if a position collides with a snake body."""
    body_to_check = snake_body[:-1] if exclude_tail else snake_body
    return any(pos["x"] == segment["x"] and pos["y"] == segment["y"] for segment in body_to_check)


def manhattan_distance(pos1: typing.Dict, pos2: typing.Dict) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1["x"] - pos2["x"]) + abs(pos1["y"] - pos2["y"])


def get_possible_moves(head: typing.Dict) -> typing.List[typing.Dict]:
    """Get all possible next positions from a head position."""
    return [
        get_next_position(head, "up"),
        get_next_position(head, "down"),
        get_next_position(head, "left"),
        get_next_position(head, "right")
    ]


def flood_fill_count(start_pos: typing.Dict, game_state: typing.Dict, max_depth: int = 20) -> int:
    """
    Perform limited flood fill from start_pos to count reachable spaces.
    Limited to max_depth to avoid performance issues.
    Returns the number of reachable empty spaces.
    """
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    
    # Create a set of occupied positions
    occupied = set()
    
    # Add all snake bodies (excluding tails that will move)
    for snake in game_state['board']['snakes']:
        for i, segment in enumerate(snake['body']):
            # Exclude tail since it will move away
            if i < len(snake['body']) - 1:
                occupied.add((segment['x'], segment['y']))
    
    # BFS to count reachable spaces
    visited = set()
    queue = deque([(start_pos, 0)])  # (position, depth)
    visited.add((start_pos['x'], start_pos['y']))
    count = 1
    
    while queue:
        pos, depth = queue.popleft()
        
        # Stop expanding if we've reached max depth
        if depth >= max_depth:
            continue
        
        # Check all four directions
        for move in ["up", "down", "left", "right"]:
            next_pos = get_next_position(pos, move)
            next_tuple = (next_pos['x'], next_pos['y'])
            
            # Skip if out of bounds, occupied, or already visited
            if is_out_of_bounds(next_pos, board_width, board_height):
                continue
            if next_tuple in occupied:
                continue
            if next_tuple in visited:
                continue
            
            visited.add(next_tuple)
            queue.append((next_pos, depth + 1))
            count += 1
    
    return count


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data
def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"
    my_length = game_state["you"]["length"]
    my_health = game_state["you"]["health"]

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    # Step 1 - Prevent your Battlesnake from moving out of bounds
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    
    for move_dir in ["up", "down", "left", "right"]:
        next_pos = get_next_position(my_head, move_dir)
        if is_out_of_bounds(next_pos, board_width, board_height):
            is_move_safe[move_dir] = False

    # Step 2 - Prevent your Battlesnake from colliding with itself
    my_body = game_state['you']['body']
    
    for move_dir in ["up", "down", "left", "right"]:
        next_pos = get_next_position(my_head, move_dir)
        # Exclude tail since it will move away (unless we just ate food)
        if is_collision_with_snake(next_pos, my_body, exclude_tail=True):
            is_move_safe[move_dir] = False

    # Step 3 - Prevent your Battlesnake from colliding with other Battlesnakes
    opponents = game_state['board']['snakes']
    
    for move_dir in ["up", "down", "left", "right"]:
        next_pos = get_next_position(my_head, move_dir)
        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue  # Skip ourselves
            # Check collision with opponent body (exclude tail)
            if is_collision_with_snake(next_pos, opponent["body"], exclude_tail=True):
                is_move_safe[move_dir] = False
            
            # Avoid head-to-head collisions with larger or equal snakes
            opponent_head = opponent["body"][0]
            opponent_length = opponent["length"]
            
            # Check if opponent could move to a position adjacent to our next position
            opponent_possible_moves = get_possible_moves(opponent_head)
            for opp_next_pos in opponent_possible_moves:
                if opp_next_pos["x"] == next_pos["x"] and opp_next_pos["y"] == next_pos["y"]:
                    # Opponent could move to the same position
                    if opponent_length >= my_length:
                        # We would lose or tie, avoid this move
                        is_move_safe[move_dir] = False

    # Are there any safe moves left?
    safe_moves = []
    for move_dir, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move_dir)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    # Step 4 - Calculate space available for each move
    move_space = {}
    for move_dir in safe_moves:
        next_pos = get_next_position(my_head, move_dir)
        space = flood_fill_count(next_pos, game_state, max_depth=20)
        move_space[move_dir] = space

    # Filter out moves with very little space (less than half our length)
    # This prevents getting trapped in tight spaces
    min_space = max(my_length // 2, 5)
    spacious_moves = [move_dir for move_dir in safe_moves if move_space[move_dir] >= min_space]
    
    # If all moves lead to tight spaces, keep all safe moves
    if len(spacious_moves) == 0:
        spacious_moves = safe_moves

    # Step 5 - Move towards food with health awareness
    food = game_state['board']['food']
    
    # Determine if we're in urgent need of food
    is_hungry = my_health < 30
    is_very_hungry = my_health < 15
    
    if len(food) > 0:
        # Find the closest food
        closest_food = min(food, key=lambda f: manhattan_distance(my_head, f))
        
        # Score each spacious move based on distance to food and available space
        move_scores = {}
        for move_dir in spacious_moves:
            next_pos = get_next_position(my_head, move_dir)
            distance = manhattan_distance(next_pos, closest_food)
            space = move_space[move_dir]
            
            # Adjust scoring based on health
            if is_very_hungry:
                # When very hungry, prioritize food heavily
                move_scores[move_dir] = -distance * 10 + (space * 0.01)
            elif is_hungry:
                # When hungry, prioritize food more
                move_scores[move_dir] = -distance * 2 + (space * 0.01)
            else:
                # Normal: prioritize food, but space is important too
                move_scores[move_dir] = -distance + (space * 0.01)
        
        # Choose the move with the best score
        next_move = max(move_scores, key=move_scores.get)
    else:
        # No food available, choose the move with the most space
        next_move = max(spacious_moves, key=lambda m: move_space[m])

    print(f"MOVE {game_state['turn']}: {next_move} (health: {my_health}, space: {move_space[next_move]})")
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({"info": info, "start": start, "move": move, "end": end})
