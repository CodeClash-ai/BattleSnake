import json
import os
import sys

# We can simulate game turns using main.py's move function.
# Let's inspect what simulations look like.
with open("/logs/rounds/3/sim_0.jsonl") as f:
    for i in range(3):
        line = f.readline()
        if not line:
            break
        data = json.loads(line)
        print(f"Turn {data.get('turn')}")
        print("Board keys:", data.get("board", {}).keys() if "board" in data else "None")
        print("You keys:", data.get("you", {}).keys() if "you" in data else "None")
