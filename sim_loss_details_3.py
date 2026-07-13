import os
import json

log_dir = "/logs/rounds/1/"
# Let's inspect sim_146.jsonl because it went to turn 267 where we lost
with open(os.path.join(log_dir, "sim_146.jsonl")) as f:
    lines = f.readlines()

print("SIM 146 TURNS 255 to 267:")
for line in lines:
    try:
        data = json.loads(line)
    except Exception:
        continue
    if "board" in data:
        turn = data["turn"]
        if 255 <= turn <= 267:
            print(f"Turn {turn}:")
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
