import json

path = "/logs/rounds/0/sim_171.jsonl"
with open(path) as f:
    for line in f:
        try:
            d = json.loads(line)
            print(f"Turn {d.get('turn')}: {d}")
        except:
            print("Non-JSON:", line)
