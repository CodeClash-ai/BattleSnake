import json

path = "/logs/rounds/0/sim_12.jsonl"
with open(path) as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    data = json.loads(line)
    if "board" not in data:
        continue
    turn = data.get("turn")
    if turn >= 175:
        print(f"\n--- Turn {turn} ---")
        for s in data["board"].get("snakes", []):
            print(f"  {s['name']}: head={s['head']} body={s['body']} health={s['health']}")
