import json
from main import move, flood_fill_size

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

# Find last few turns
for t in turns[-5:]:
    print(f"Turn {t['turn']}")
    snakes = t["board"]["snakes"]
    for s in snakes:
        print(f"  Snake {s['name']}: head ({s['body'][0]['x']},{s['body'][0]['y']}), len {len(s['body'])}, health {s['health']}")
