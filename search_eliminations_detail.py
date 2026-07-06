import os
import json

rounds_dir = "/logs/rounds"
keys = set()
with open(os.path.join(rounds_dir, "0", "sim_101.jsonl")) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            keys.update(data.keys())
            if "board" in data:
                # Let's inspect board keys
                keys.update(["board." + k for k in data["board"].keys()])
                if "snakes" in data["board"]:
                    # Inspect snake keys
                    for s in data["board"]["snakes"]:
                        keys.update(["snake." + k for k in s.keys()])
                        if "eliminatedCause" in s or "death" in s:
                            print("Found elimination key!")
print(sorted(list(keys)))
