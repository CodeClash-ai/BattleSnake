import json

fname = "/logs/rounds/0/sim_101.jsonl"
with open(fname) as f:
    lines = f.readlines()

for line in lines[-10:]:
    try:
        d = json.loads(line)
        # Check if there is a warning, elimination, or similar field
        if "winner" in d or "elimination" in str(d) or "died" in str(d):
            print(d)
    except:
        pass
