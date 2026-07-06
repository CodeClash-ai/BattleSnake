import json

with open("/logs/rounds/2/sim_142.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip() and "board" in json.loads(line)]

for idx in [-3, -2, -1]:
    data = lines[idx]
    print(f"Turn {data['turn']}")
    for s in data['board']['snakes']:
        print(f"  {s['name']}: head {s['head']}, health {s['health']}, body {s['body']}")
