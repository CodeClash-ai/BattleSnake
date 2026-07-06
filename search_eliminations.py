import os
import json

rounds_dir = "/logs/rounds"
reasons = {}

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Check if this contains elimination info
                        # In standard Battlesnake JSON, there's sometimes a "results" or "elimination" key
                        # Let's inspect keys of data
                        for k in data.keys():
                            if k not in ["game", "turn", "board", "you"]:
                                reasons[k] = reasons.get(k, 0) + 1
print(reasons)
