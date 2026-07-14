import json

# Let's inspect sim_104 fully at the last turn.
with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for i in range(len(lines) - 4, len(lines)):
    print(lines[i])
