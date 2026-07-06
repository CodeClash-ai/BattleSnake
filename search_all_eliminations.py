import os
import json

rounds_dir = "/logs/rounds"
eliminations = []

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Check if this line is an elimination message or has game events
                        # Some logs have "events" or "eliminated" or similar. Let's see what keys exist.
                        # Wait, we can see if our snake's health went to 0 or if there is a 'death' field, etc.
                        pass

# Let's inspect the last line of a few jsonl files directly to see if they contain elimination reasons.
