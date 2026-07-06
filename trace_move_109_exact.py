import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

state_109 = json.loads(lines[110])
print("Verify Turn:", state_109["turn"])

res = main.move(state_109)
print("Move result at Turn 109:", res)
