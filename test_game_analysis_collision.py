import json
from main import move

# Let's create a simulated game_state for Turn 16 of sim_111
game_state = {
    "game": {"id": "test"},
    "turn": 16,
    "board": {
        "height": 11,
        "width": 11,
        "snakes": [
            {
                "id": "crystal",
                "name": "nbw_nbw-crystal",
                "health": 84,
                "body": [{"x": 1, "y": 1}, {"x": 2, "y": 1}, {"x": 3, "y": 1}],
                "head": {"x": 1, "y": 1},
                "length": 3
            },
            {
                "id": "gemini",
                "name": "gemini-3-5-flash",
                "health": 84,
                "body": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}],
                "head": {"x": 0, "y": 0},
                "length": 3
            }
        ],
        "food": [{"x": 8, "y": 10}, {"x": 10, "y": 2}, {"x": 5, "y": 5}],
        "hazards": []
    },
    "you": {
        "id": "gemini",
        "name": "gemini-3-5-flash",
        "health": 84,
        "body": [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}],
        "head": {"x": 0, "y": 0},
        "length": 3
    }
}

print(move(game_state))

# Detailed inspect of what happened inside move
board = game_state["board"]
width, height = board["width"], board["height"]
my_snake = game_state["you"]
my_body = my_snake["body"]
my_length = len(my_body)
head_seg = my_body[0]
head = (head_seg["x"], head_seg["y"])

directions = {
    "up": (head[0], head[1] + 1),
    "down": (head[0], head[1] - 1),
    "left": (head[0] - 1, head[1]),
    "right": (head[0] + 1, head[1])
}

occupied = set()
for snake in board.get("snakes", []):
    body = snake["body"]
    is_growing = snake["health"] == 100
    for i, seg in enumerate(body):
        if i == len(body) - 1 and not is_growing and len(body) > 1:
            continue
        occupied.add((seg["x"], seg["y"]))

print("occupied:", occupied)

safe_moves = []
for d, pos in directions.items():
    px, py = pos
    if 0 <= px < width and 0 <= py < height:
        if pos not in occupied:
            is_dangerous = False
            for snake in board.get("snakes", []):
                if snake["id"] == my_snake["id"]:
                    continue
                opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                opp_len = len(snake["body"])
                if abs(pos[0] - opp_head[0]) + abs(pos[1] - opp_head[1]) == 1:
                    if opp_len >= my_length:
                        is_dangerous = True
                        break
            
            from main import flood_fill_size
            room_size = flood_fill_size(pos, occupied, width, height, max_depth=15)
            safe_moves.append({
                "direction": d,
                "position": pos,
                "is_dangerous": is_dangerous,
                "room_size": room_size
            })

print("safe_moves:")
for m in safe_moves:
    print(m)
