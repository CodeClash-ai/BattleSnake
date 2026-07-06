import json

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "turn" in data:
                turns.append(data)

for i in range(143, 148):
    t = next((turn for turn in turns if turn["turn"] == i), None)
    if t:
        print(f"Turn {i}:")
        for s in t["board"]["snakes"]:
            print(f"  {s['name']}: head {s['head']}, body {s['body'][:3]}")
