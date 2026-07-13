import os
import json

log_dir = "/logs/rounds/0/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

for fn in sim_files:
    path = os.path.join(log_dir, fn)
    with open(path, 'r') as f:
        lines = f.readlines()
    if len(lines) < 5:
        continue
    last_line = json.loads(lines[-1])
    winner = last_line.get("winnerName", None)
    if winner != "gemini-3-5-flash":
        penultimate = json.loads(lines[-2])
        you = penultimate.get("you", {})
        health = you.get("health", 100)
        if health <= 1:
            print(f"Starved or died next turn in {fn} on turn {penultimate.get('turn')}. Our Len: {you.get('length')}, Opp Len: {max([s['length'] for s in penultimate['board']['snakes'] if s['id'] != you['id']])}")
