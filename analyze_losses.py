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
        if not lines:
            continue
        # Parse the last line or lines to check the winner
        winner = None
        for line in reversed(lines):
            data = json.loads(line)
            if "winnerId" in data:
                winner = data.get("winnerId")
                break
        
        # If gemini is not the winner or there is no winnerId, let's look closer
        # Let's inspect the last state before the end
        if len(lines) >= 2:
            last_state = json.loads(lines[-2])
            if "board" in last_state:
                snakes = last_state["board"].get("snakes", [])
                alive_names = [s["name"] for s in snakes]
                # If gemini-3-5-flash is not in the alive names or there's a different winner
                if "gemini-3-5-flash" not in alive_names:
                    print(f"Loss/Draw in Round {r} {sf}. Alive snakes at last turn: {alive_names}")
