import json

path = "/logs/rounds/1/sim_24.jsonl"
with open(path) as f:
    lines = f.readlines()

# Let's print turn 114 to see if there's any crash/latency/error message in the response
for line in lines:
    data = json.loads(line)
    if data.get("turn") == 114:
        print(json.dumps(data, indent=2))
