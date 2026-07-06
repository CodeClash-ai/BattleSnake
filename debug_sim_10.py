import json
from main import move

with open("/logs/rounds/2/sim_10.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

for turn_idx in range(len(lines)-5, len(lines)):
    data = lines[turn_idx]
    if "turn" in data and data["turn"] is not None:
        print(f"Turn {data['turn']}")
        for s in data['board']['snakes']:
            print(f"  {s['name']}: head {s['head']}, body {s['body']}")
