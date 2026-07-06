import json
from main import flood_fill_size, _manhattan, _board_center

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "turn" in data:
                turns.append(data)

t = next(turn for turn in turns if turn["turn"] == 141)
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

food = board.get("food", [])
target = None
if food:
    best_dist = float('inf')
    for f in food:
        fp = (f["x"], f["y"])
        d = _manhattan(head, fp)
        if d < best_dist:
            best_dist = d
            target = fp
if not target:
    target = _board_center(width, height)

print("Food Target:", target)

for d, pos in directions.items():
    if 0 <= pos[0] < width and 0 <= pos[1] < height:
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

            room_size = flood_fill_size(pos, occupied, width, height, max_depth=15)
            
            # Look-ahead score
            next_non_dangerous_choices = 0
            next_possible_positions = [
                (pos[0]+1, pos[1]), (pos[0]-1, pos[1]),
                (pos[0], pos[1]+1), (pos[0], pos[1]-1)
            ]
            for npx, npy in next_possible_positions:
                if 0 <= npx < width and 0 <= npy < height:
                    if (npx, npy) not in occupied and (npx, npy) != head:
                        next_danger = False
                        for snake in board.get("snakes", []):
                            if snake["id"] == my_snake["id"]:
                                continue
                            opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                            opp_len = len(snake["body"])
                            if abs(npx - opp_head[0]) + abs(npy - opp_head[1]) <= 2:
                                if opp_len >= my_length:
                                    next_danger = True
                                    break
                        if not next_danger:
                            next_non_dangerous_choices += 1

            not_dangerous = 1 if not is_dangerous else 0
            has_space = 1 if room_size >= min(my_length, 50) else 0
            dist = _manhattan(pos, target)
            score = (not_dangerous, has_space, next_non_dangerous_choices, room_size, -dist)
            print(f"Move {d} to {pos}: score={score} (not_dangerous={not_dangerous}, has_space={has_space}, next_choices={next_non_dangerous_choices}, room_size={room_size}, dist={dist})")
