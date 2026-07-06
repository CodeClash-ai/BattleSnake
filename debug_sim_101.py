import json
filepath = "/logs/rounds/0/sim_101.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    if "turn" not in t:
        print("Non-turn data:", t.keys())
        continue
    if t["turn"] >= 30:
        print("--- TURN", t["turn"], "---")
        for s in t["board"]["snakes"]:
            print(f"Snake {s['name']}: head={s['head']}, length={len(s['body'])}, health={s['health']}, body={s['body']}")
