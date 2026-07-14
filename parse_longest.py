import os
import json

rounds_dir = "/logs/rounds"
max_turns = 0
longest_game = ""
for r in sorted(os.listdir(rounds_dir)):
    r_path = os.path.join(rounds_dir, r)
    if not os.path.isdir(r_path):
        continue
    sim_files = [f for f in os.listdir(r_path) if f.startswith("sim_") and f.endswith(".jsonl")]
    for sf in sorted(sim_files):
        path = os.path.join(r_path, sf)
        if os.path.getsize(path) == 0:
            continue
        with open(path) as f:
            lines = f.readlines()
        if len(lines) < 2:
            continue
        last_turn_state = json.loads(lines[-2])
        if "winnerId" in last_turn_state:
            continue
        turn = last_turn_state.get("turn", 0)
        if turn > max_turns:
            max_turns = turn
            longest_game = f"Round {r} {sf}"

print(f"Max turns seen: {max_turns} in {longest_game}")
