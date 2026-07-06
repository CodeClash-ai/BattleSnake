import os
import json

rounds_dir = "/workspace" # we'll inspect test_game.json or others if any
# Let's search rounds for any other deaths
rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl") and os.path.getsize(os.path.join(round_path, filename)) > 0:
            filepath = os.path.join(round_path, filename)
            turns = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            turns.append(data)
            
            # Find when gemini-3-5-flash died, and look at the turn before it
            died_turn = None
            for idx, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    died_turn = turn["turn"]
                    break
            
            if died_turn is not None:
                print(f"Round {round_name} {filename} Death at Turn {died_turn}")
