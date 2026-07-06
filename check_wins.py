import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    total = 0
    wins = 0
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            total += 1
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
                if "gemini-3-5-flash" in alive_names:
                    wins += 1
    print(f"Round {round_name}: Wins {wins} / {total} ({(wins/total)*100:.2f}%)")
