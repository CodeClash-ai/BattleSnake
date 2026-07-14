import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    print(f"--- Round {round_name} ---")
    results_file = os.path.join(round_path, "results.json")
    if os.path.exists(results_file):
        with open(results_file) as f:
            print(json.load(f))
