import json

filepath = "/logs/rounds/0/sim_102.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

for t in turns:
    if t["turn"] in (25, 26):
        print(f"--- TURN {t['turn']} ---")
        for s in t["board"]["snakes"]:
            print(f"{s['name']}: head={s['head']}, body={s['body']}")
