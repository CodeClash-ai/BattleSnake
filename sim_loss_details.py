import os
import json

log_dir = "/logs/rounds/1/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

# Let's inspect sim_100.jsonl details from turn 260 onwards
with open(os.path.join(log_dir, "sim_100.jsonl")) as f:
    lines = f.readlines()

print("SIM 100 TURNS 260 to 267:")
for line in lines:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        if 260 <= turn <= 267:
            print(f"Turn {turn}:")
            print("  Food:", data["board"]["food"])
            for s in data["board"]["snakes"]:
                print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
                print(f"    Body: {s['body']}")
