import json
import typing
from collections import deque

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

def get_possible_moves(head: typing.Dict) -> typing.List[typing.Dict]:
    """Get all possible next positions from a head position."""
    return [
        get_next_position(head, "up"),
        get_next_position(head, "down"),
        get_next_position(head, "left"),
        get_next_position(head, "right")
    ]

# Recreate the game state
game_state = {
    "game": {"id": "test"},
    "turn": 41,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 10, "y": 0}],
        "snakes": [
            {
                "id": "us",
                "name": "claude-sonnet-4-5-20250929",
                "health": 99,
                "body": [
                    {"x": 7, "y": 6},
                    {"x": 7, "y": 7},
                    {"x": 8, "y": 7},
                    {"x": 8, "y": 6},
                    {"x": 8, "y": 5},
                    {"x": 7, "y": 5},
                    {"x": 6, "y": 5}
                ],
                "head": {"x": 7, "y": 6},
                "length": 7
            },
            {
                "id": "opp",
                "name": "gemini-2.5-pro",
                "health": 88,
                "body": [
                    {"x": 5, "y": 6},
                    {"x": 5, "y": 7},
                    {"x": 4, "y": 7},
                    {"x": 3, "y": 7},
                    {"x": 2, "y": 7},
                    {"x": 1, "y": 7},
                    {"x": 0, "y": 7},
                    {"x": 0, "y": 6},
                    {"x": 0, "y": 5}
                ],
                "head": {"x": 5, "y": 6},
                "length": 9
            }
        ]
    },
    "you": {
        "id": "us",
        "name": "claude-sonnet-4-5-20250929",
        "health": 99,
        "body": [
            {"x": 7, "y": 6},
            {"x": 7, "y": 7},
            {"x": 8, "y": 7},
            {"x": 8, "y": 6},
            {"x": 8, "y": 5},
            {"x": 7, "y": 5},
            {"x": 6, "y": 5}
        ],
        "head": {"x": 7, "y": 6},
        "length": 7
    }
}

is_move_safe = {"up": True, "down": True, "left": True, "right": True}

my_head = game_state["you"]["body"][0]
my_neck = game_state["you"]["body"][1]
my_length = game_state["you"]["length"]

print("=== Step 1: Prevent moving backwards ===")
if my_neck["x"] < my_head["x"]:
    is_move_safe["left"] = False
    print("Neck is left of head, don't move left")
elif my_neck["x"] > my_head["x"]:
    is_move_safe["right"] = False
    print("Neck is right of head, don't move right")
elif my_neck["y"] < my_head["y"]:
    is_move_safe["down"] = False
    print("Neck is below head, don't move down")
elif my_neck["y"] > my_head["y"]:
    is_move_safe["up"] = False
    print("Neck is above head, don't move up")

print(f"After backwards check: {is_move_safe}")

print("\n=== Step 2: Check bounds ===")
board_width = game_state['board']['width']
board_height = game_state['board']['height']

for move_dir in ["up", "down", "left", "right"]:
    next_pos = get_next_position(my_head, move_dir)
    if is_out_of_bounds(next_pos, board_width, board_height):
        print(f"{move_dir} -> {next_pos}: OUT OF BOUNDS")
        is_move_safe[move_dir] = False

print(f"After bounds check: {is_move_safe}")

print("\n=== Step 3: Check self collision ===")
my_body = game_state['you']['body']

for move_dir in ["up", "down", "left", "right"]:
    next_pos = get_next_position(my_head, move_dir)
    if is_collision_with_snake(next_pos, my_body, exclude_tail=True):
        print(f"{move_dir} -> ({next_pos['x']}, {next_pos['y']}): SELF COLLISION")
        is_move_safe[move_dir] = False

print(f"After self collision check: {is_move_safe}")

print("\n=== Step 4: Check opponent collision ===")
opponents = game_state['board']['snakes']

for move_dir in ["up", "down", "left", "right"]:
    next_pos = get_next_position(my_head, move_dir)
    for opponent in opponents:
        if opponent["id"] == game_state["you"]["id"]:
            continue
        
        # Check body collision
        if is_collision_with_snake(next_pos, opponent["body"], exclude_tail=True):
            print(f"{move_dir} -> ({next_pos['x']}, {next_pos['y']}): OPPONENT BODY COLLISION")
            is_move_safe[move_dir] = False
        
        # Check head-to-head
        opponent_head = opponent["body"][0]
        opponent_length = opponent["length"]
        opponent_possible_moves = get_possible_moves(opponent_head)
        
        for opp_next_pos in opponent_possible_moves:
            if opp_next_pos["x"] == next_pos["x"] and opp_next_pos["y"] == next_pos["y"]:
                if opponent_length >= my_length:
                    print(f"{move_dir} -> ({next_pos['x']}, {next_pos['y']}): HEAD-TO-HEAD with opponent at ({opponent_head['x']}, {opponent_head['y']}) - they're bigger/equal")
                    is_move_safe[move_dir] = False

print(f"\nFinal safe moves: {is_move_safe}")
safe_moves = [m for m, safe in is_move_safe.items() if safe]
print(f"Safe moves list: {safe_moves}")
