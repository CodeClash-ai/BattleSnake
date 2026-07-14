import json

with open("/logs/rounds/0/sim_144.jsonl") as f:
    lines = f.readlines()

# let's look at turn 75 and 76 logic specifically
for line in lines:
    data = json.loads(line)
    if "turn" in data and data["turn"] in [75, 76]:
        print(f"Turn {data['turn']}:")
        for s in data["board"]["snakes"]:
            print(f"  {s['name']}: head={s['head']} len={s['length']} body={s['body']}")
