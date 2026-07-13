import os
import json

log_dir = "/logs/rounds/1/"
with open(os.path.join(log_dir, "sim_100.jsonl")) as f:
    lines = f.readlines()

print("SIM 100 TURNS 130 to 145:")
for line in lines:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        if 130 <= turn <= 145:
            print(f"Turn {turn}:")
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
