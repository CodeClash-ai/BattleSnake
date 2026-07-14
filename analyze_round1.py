import json
import os

round_dir = "/logs/rounds/1"
wins = 0
losses = 0
ties = 0

for filename in os.listdir(round_dir):
    if not filename.endswith(".json"):
        continue
    filepath = os.path.join(round_dir, filename)
    with open(filepath, 'r') as f:
        try:
            data = json.load(f)
            # Find the winner
            # In battlesnake logs, typically there is an "outcome" or "winner" field, or we can check the status of snakes at the end
            # Let's inspect one file first or analyze based on snakes.
        except Exception as e:
            pass
