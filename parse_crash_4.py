import json

with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

for line in lines[140:142]:
    print(line)
