import json

with open("/logs/rounds/2/sim_10.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if "turn" in data and data["turn"] is not None:
            print(f"Turn {data['turn']}, Snakes: {[s['name'] for s in data['board']['snakes']]}")
