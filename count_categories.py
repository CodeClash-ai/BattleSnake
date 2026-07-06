import os
import json

rounds_dir = "/logs/rounds"
only_dangerous = 0
no_options = 0
had_safe_but_died = 0
total_deaths = 0

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            turns = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            turns.append(data)
            
            # Find when gemini-3-5-flash died, and look at the turn before it
            died_turn = None
            for idx, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    died_turn = turn["turn"]
                    break
            
            if died_turn is not None:
                total_deaths += 1
                prev_turn_idx = None
                for idx, turn in enumerate(turns):
                    if turn["turn"] == died_turn - 1:
                        prev_turn_idx = idx
                        break
                
                if prev_turn_idx is not None:
                    prev_turn = turns[prev_turn_idx]
                    my_prev = next((s for s in prev_turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                    if my_prev:
                        head = my_prev["head"]
                        width, height = prev_turn["board"]["width"], prev_turn["board"]["height"]
                        occupied = set()
                        for s in prev_turn["board"]["snakes"]:
                            is_growing = s["health"] == 100
                            for i, seg in enumerate(s["body"]):
                                if i == len(s["body"]) - 1 and not is_growing and len(s["body"]) > 1:
                                    continue
                                occupied.add((seg["x"], seg["y"]))
                        
                        safe_options = []
                        dangerous_options = []
                        from main import flood_fill_size
                        for d, (dx, dy) in [("up", (0, 1)), ("down", (0, -1)), ("left", (-1, 0)), ("right", (1, 0))]:
                            pos = (head["x"] + dx, head["y"] + dy)
                            if 0 <= pos[0] < width and 0 <= pos[1] < height:
                                if pos not in occupied:
                                    is_dangerous = False
                                    for snake in prev_turn["board"]["snakes"]:
                                        if snake["id"] == my_prev["id"]:
                                            continue
                                        opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                                        opp_len = len(snake["body"])
                                        if abs(pos[0] - opp_head[0]) + abs(pos[1] - opp_head[1]) == 1:
                                            if opp_len >= len(my_prev["body"]):
                                                is_dangerous = True
                                    room = flood_fill_size(pos, occupied, width, height)
                                    if is_dangerous:
                                        dangerous_options.append(f"{d} (room: {room})")
                                    else:
                                        safe_options.append(f"{d} (room: {room})")
                        
                        if not safe_options and not dangerous_options:
                            no_options += 1
                        elif not safe_options and dangerous_options:
                            only_dangerous += 1
                        else:
                            had_safe_but_died += 1
                            print(f"Had safe move but died: Round {round_name} {filename} Turn {died_turn-1}. Options: {safe_options}, dangerous: {dangerous_options}")

print(f"Total deaths: {total_deaths}")
print(f"No options: {no_options}")
print(f"Only dangerous: {only_dangerous}")
print(f"Had safe moves but died: {had_safe_but_died}")
