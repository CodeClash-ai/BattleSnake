import json
from main import flood_fill_size

filepath = "/logs/rounds/1/sim_210.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    turn_num = t.get("turn")
    if turn_num == 228:
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        board = t["board"]
        width, height = board["width"], board["height"]
        head = (my_snake["head"]["x"], my_snake["head"]["y"])
        directions = {
            "up": (head[0], head[1] + 1),
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
                
        for d, pos in directions.items():
            room = flood_fill_size(pos, occupied, width, height)
            print(f"Pos: {pos} ({d}), room size: {room}, enough room (>= 32): {room >= 32}")
