import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

# Wait, in trace_who_died_3, at Turn 109:
# gemini-3-5-flash head was at (1, 0)
# Let's read lines[109] and print its turn number.
data = json.loads(lines[109])
print("Lines[109] turn number:", data["turn"])
