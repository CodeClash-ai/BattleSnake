import json

with open("/logs/rounds/0/sim_144.jsonl") as f:
    lines = f.readlines()

for i in range(len(lines) - 5, len(lines)):
    print(lines[i])
