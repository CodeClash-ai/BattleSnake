import json
from main import flood_fill_size

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "turn" in data:
                turns.append(data)

t = next(turn for turn in turns if turn["turn"] == 142)
board = t["board"]
width, height = board["width"], board["height"]
my_snake = next(s for s in board["snakes"] if s["name"] == "gemini-3-5-flash")
my_body = my_snake["body"]
my_length = len(my_body)
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

print("Head:", head)
for d, pos in directions.items():
    if 0 <= pos[0] < width and 0 <= pos[1] < height:
        is_occ = pos in occupied
        room = flood_fill_size(pos, occupied, width, height, max_depth=15)
        print(f"{d} to {pos}: occupied={is_occ}, room_size={room}")
