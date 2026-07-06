import json

filepath = "/logs/rounds/0/sim_101.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

for t in turns:
    if t["turn"] == 32:
        print("Food:", t["board"]["food"])
