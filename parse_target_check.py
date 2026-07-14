import json

with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

data = json.loads(lines[139]) # Turn 138
board = data["board"]
food = board["food"]
print("Food:", food)
