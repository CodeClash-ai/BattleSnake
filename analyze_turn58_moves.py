import json

path = "/logs/rounds/0/sim_101.jsonl"
with open(path) as f:
    lines = f.readlines()

for line in lines:
    try:
        d = json.loads(line)
        if d.get("turn") == 58:
            board = d["board"]
            for s in board["snakes"]:
                print(s["name"], s["body"])
    except:
        pass
