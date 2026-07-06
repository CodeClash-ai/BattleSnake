import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    results = {}
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            # Find the last turn line
            last_turn = None
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "turn" in data and data["turn"] is not None:
                            last_turn = data
            if last_turn:
                snakes = last_turn["board"]["snakes"]
                alive_names = [s["name"] for s in snakes]
                if len(alive_names) == 1:
                    winner = alive_names[0]
                    results[winner] = results.get(winner, 0) + 1
                elif len(alive_names) == 0:
                    results["draw/both died"] = results.get("draw/both died", 0) + 1
                else:
                    results["multiple_alive"] = results.get("multiple_alive", 0) + 1
    print(f"Round {round_name} outcome stats:")
    for k, v in results.items():
        print(f"  {k}: {v}")
