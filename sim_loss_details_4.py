import os
import json

log_dir = "/logs/rounds/1/"
with open(os.path.join(log_dir, "sim_100.jsonl")) as f:
    lines = f.readlines()

print("SIM 100 END GAME:")
for line in lines[-15:]:
    data = json.loads(line)
    if "board" in data:
        turn = data["turn"]
        print(f"Turn {turn}:")
        for s in data["board"]["snakes"]:
            print(f"  Snake {s['name']}: Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}")
            print(f"    Body: {s['body']}")
