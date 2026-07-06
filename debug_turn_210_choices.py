import json
from main import move, flood_fill_size

filepath = "/logs/rounds/1/sim_210.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    turn_num = t.get("turn")
    if turn_num is not None and 228 <= turn_num <= 234:
        # Find snake
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        game_state = {
            "game": t["game"],
            "turn": turn_num,
            "board": t["board"],
            "you": my_snake
        }
        
        # Calculate moves manually
        board = t["board"]
        width, height = board["width"], board["height"]
        head = (my_snake["head"]["x"], my_snake["head"]["y"])
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
                
        choices = []
        for d, pos in directions.items():
            if 0 <= pos[0] < width and 0 <= pos[1] < height:
                if pos not in occupied:
                    room = flood_fill_size(pos, occupied, width, height)
                    choices.append(f"{d} (room: {room})")
        print(f"Turn {turn_num}: head {head}, choices: {', '.join(choices)}, bot chose: {move(game_state)}")
