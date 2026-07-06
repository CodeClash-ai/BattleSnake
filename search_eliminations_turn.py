import os
import json

rounds_dir = "/logs/rounds"
keys = set()
with open(os.path.join(rounds_dir, "0", "sim_101.jsonl")) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            # Print if there is anything that is not game, turn, board, you
            extra = {k: v for k, v in data.items() if k not in ["game", "turn", "board", "you"]}
            if extra:
                print(f"Turn {data.get('turn')}: {extra}")
                break
