import os
import json

log_dir = "/logs/rounds/1/"
# Let's inspect sim_100.jsonl details from turn 120 onwards
with open(os.path.join(log_dir, "sim_100.jsonl")) as f:
    lines = f.readlines()

print("SIM 100 TURNS 120 to 132:")
for line in lines:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        if 120 <= turn <= 132:
            print(f"Turn {turn}:")
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
