import json

# Let's inspect sim_104 fully around turn 139.
with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for i in range(130, len(lines)):
    data = json.loads(lines[i])
    if "board" in data:
        snakes = data["board"].get("snakes", [])
        names = [s["name"] for s in snakes]
        print(f"Turn {data.get('turn')}: {names}")
