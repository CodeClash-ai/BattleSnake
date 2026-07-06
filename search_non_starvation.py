import os
import json

rounds_dir = "/logs/rounds"

for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            turns = []
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "board" in data:
                            turns.append(data)
            
            # Find when we died
            for i, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    prev_turn = turns[i-1] if i > 0 else None
                    if prev_turn:
                        my_prev = next((s for s in prev_turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                        if my_prev and my_prev["health"] > 1:
                            # Let's print out the details
                            print(f"Round {round_name} {filename} Turn {turn['turn']-1}: length {my_prev['length']} health {my_prev['health']}")
                    break
