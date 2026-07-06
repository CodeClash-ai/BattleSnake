import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

state_108 = json.loads(lines[109])
gemini = next(s for s in state_108["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
state_108["you"] = gemini

# Let's see the calculations:
board = state_108["board"]
width, height = board["width"], board["height"]
my_snake = state_108["you"]
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
            
            room_size = main.flood_fill_size(pos, occupied, width, height, max_depth=15)
            
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
            
            safe_moves.append({
                "direction": d,
                "position": pos,
                "is_dangerous": is_dangerous,
                "room_size": room_size,
                "next_choices": next_non_dangerous_choices
            })

food = board.get("food", [])
target = None
if food:
    best_dist = float('inf')
    for f in food:
        fp = (f["x"], f["y"])
        d = main._manhattan(head, fp)
        if d < best_dist:
            best_dist = d
            target = fp

for m in safe_moves:
    not_dangerous = 1 if not m["is_dangerous"] else 0
    has_space = 1 if m["room_size"] >= min(my_length, 50) else 0
    dist = main._manhattan(m["position"], target)
    score = (not_dangerous, has_space, m["next_choices"], m["room_size"], -dist)
    print(f"Move: {m['direction']}, pos: {m['position']}, is_dangerous: {m['is_dangerous']}, room_size: {m['room_size']}, next_choices: {m['next_choices']}, score: {score}")
