import os
import json

rounds_dir = "/logs/rounds"
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
        # check last state before winner declaration
        last_turn_state = json.loads(lines[-2])
        if "winnerId" in last_turn_state:
            continue
        # find if there is a timeout
        snakes = last_turn_state.get("board", {}).get("snakes", [])
        for s in snakes:
            if s.get("latency") and int(s.get("latency")) >= 500:
                print(f"Round {r} file {sf}: {s['name']} timed out at turn {last_turn_state['turn']} with latency {s['latency']}")
