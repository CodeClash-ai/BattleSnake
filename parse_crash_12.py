import json

with open("/logs/rounds/0/sim_144.jsonl") as f:
    lines = f.readlines()

for line in lines:
    data = json.loads(line)
    if "turn" in data and data["turn"] == 76:
        # Let's inspect the entire Turn 76 state
        print(json.dumps(data, indent=2))
