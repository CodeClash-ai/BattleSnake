import json

path = "/logs/rounds/1/sim_117.jsonl"
with open(path) as f:
    lines = f.readlines()

for line in lines:
    try:
        d = json.loads(line)
        turn = d["turn"]
        if turn != 57:
            continue
        print(json.dumps(d, indent=2))
        break
    except Exception as e:
        pass
