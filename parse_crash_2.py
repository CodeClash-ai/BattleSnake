import json

with open("/logs/rounds/0/sim_106.jsonl") as f:
    lines = f.readlines()

for idx, line in enumerate(lines[-10:]):
    data = json.loads(line)
    if "board" not in data: continue
    print(f"Turn {data['turn']}:")
    for s in data["board"]["snakes"]:
        print(f"  {s['name']}: head={s['head']} health={s['health']} body={s['body']}")
