import os
import json

log_dir = "/logs/rounds/1/"

# Let's inspect sim_120.jsonl details from turn 190 onwards
with open(os.path.join(log_dir, "sim_120.jsonl")) as f:
    lines = f.readlines()

print("SIM 120 TURNS 190 to 196:")
for line in lines:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        if 190 <= turn <= 196:
            print(f"Turn {turn}:")
            print("  Food:", data["board"]["food"])
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
