import json
with open("/logs/rounds/1/sim_121.jsonl") as f:
    lines = f.readlines()
# Let's print the entire JSON for Turn 5 and lines after that
for line in lines[-4:]:
    print(line.strip())
