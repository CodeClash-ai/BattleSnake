import os
import json

# Check the results in /logs/rounds/0/
with open("/logs/rounds/0/results.json") as f:
    res = json.load(f)
    print("Scores:")
    for k, v in res.get("scores", {}).items():
        print(f"  {k}: {v}")
