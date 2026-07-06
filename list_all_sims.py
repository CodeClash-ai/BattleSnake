import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if os.path.isdir(round_path):
        sim_files = sorted([f for f in os.listdir(round_path) if f.startswith("sim_") and f.endswith(".jsonl")], key=lambda x: int(x.split('_')[1].split('.')[0]))
        print(f"Round {round_name} has {len(sim_files)} files: {sim_files[:5]} ... {sim_files[-5:]}")
