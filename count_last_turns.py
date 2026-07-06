import os
import json

rounds_dir = "/logs/rounds"
counts = {}

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            with open(filepath) as f:
                last_turn_data = None
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            last_turn_data = data
                if last_turn_data:
                    turn = last_turn_data["turn"]
                    counts[turn] = counts.get(turn, 0) + 1

print(sorted(counts.items()))
