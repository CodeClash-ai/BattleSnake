import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

# At Turn 109:
data = json.loads(lines[110]) # Since turn 110 contains the response/state *after* turn 109 move.
# Actually, the file stores the game state for each turn *before* moves are processed.
# So lines[109] is Turn 109 state. Let's load that.
state_109 = json.loads(lines[109])

# Let's run our actual logic on state_109 and see what safe_moves we get and how they are scored!
# We can import move from main.py, but let's see how main.py treats it.
import main
import sys

# Redirect stdout to print info
print("Running move() on Turn 109 state...")
res = main.move(state_109)
print("Result move:", res)
