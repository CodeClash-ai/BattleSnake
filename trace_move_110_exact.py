import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

# Turn 110 state is stored at index 111. Let's verify
state_110 = json.loads(lines[111])
print("Verify Turn:", state_110["turn"])

# We run main.move to see what was returned
res = main.move(state_110)
print("Move result:", res)
