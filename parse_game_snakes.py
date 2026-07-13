import json

with open("/logs/rounds/0/sim_141.jsonl", "r") as f:
    lines = f.readlines()

# Let's inspect turn 133 and 134 specifically
for t in [133, 134, 135]:
    data = json.loads(lines[t])
    print(f"Turn {t}:")
    for s in data["board"]["snakes"]:
        print(f"  Snake {s['name']}: head={s['head']}, body_len={len(s['body'])}")
