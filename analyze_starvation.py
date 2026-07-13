import os
import json

log_dir = "/logs/rounds/1/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

starved_count = 0
total_losses = 0

for fn in sim_files:
    path = os.path.join(log_dir, fn)
    with open(path, 'r') as f:
        lines = f.readlines()
    if not lines:
        continue
    last_line = json.loads(lines[-1])
    winner = last_line.get("winnerName", None)
    is_draw = last_line.get("isDraw", False)
    if not is_draw and winner != "gemini-3-5-flash":
        total_losses += 1
        # Check penultimate line to see if we died of health = 0
        penultimate = json.loads(lines[-2])
        you = penultimate.get("you", {})
        health = you.get("health", 100)
        if health <= 0:
            starved_count += 1

print(f"Total losses: {total_losses}")
print(f"Starved (health <= 0) losses: {starved_count} ({starved_count / total_losses * 100:.1f}%)")
