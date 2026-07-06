import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

# Since index 109 in lines corresponds to turn 108:
# We want Turn 109, which should be index 110 of lines.
data_109 = json.loads(lines[110])
print("Turn number:", data_109["turn"])
print("My head:", data_109["you"]["head"])

# Let's run move on data_109
import main
res = main.move(data_109)
print("Result move on Turn 109:", res)
