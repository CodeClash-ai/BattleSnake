import json

with open("/logs/rounds/0/sim_141.jsonl", "r") as f:
    lines = f.readlines()

print(lines[134])
