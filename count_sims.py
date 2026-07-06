import os
rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if os.path.isdir(round_path):
        sim_files = [f for f in os.listdir(round_path) if f.startswith("sim_") and f.endswith(".jsonl")]
        print(f"Round {round_name} has {len(sim_files)} sim files")
