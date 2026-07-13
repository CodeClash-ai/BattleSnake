import os
import json

log_dir = "/logs/rounds/0/"
with open(os.path.join(log_dir, "sim_106.jsonl")) as f:
    lines = f.readlines()

print("SIM 106 TURNS 88 to 93:")
for line in lines:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        if 88 <= turn <= 93:
            print(f"Turn {turn}:")
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
