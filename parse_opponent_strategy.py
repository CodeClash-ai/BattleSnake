import json
import os

path = "/logs/rounds/0/sim_112.jsonl"
with open(path) as f:
    for line in f:
        data = json.loads(line)
        if "board" in data:
            snakes = data["board"].get("snakes", [])
            for s in snakes:
                if s["name"] == "tim-hub__awesome-snake":
                    # Print head and length
                    print(f"Turn {data.get('turn')}: length={s['length']} head={s['head']}")
            if data.get('turn', 0) > 20:
                break
