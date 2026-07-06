import os
import json

rounds_dir = "/logs/rounds"
reasons = {}

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
            
            # See who died when
            # The last turn in a game lists remaining snakes.
            # If "gemini-3-5-flash" is missing on turn T, they died at turn T-1 to T transition.
            died_turn = None
            for idx, turn in enumerate(turns):
                names = [s["name"] for s in turn["board"]["snakes"]]
                if "gemini-3-5-flash" not in names:
                    died_turn = turn["turn"]
                    break
            
            if died_turn is not None:
                # Let's inspect the turn before death
                prev_turn = next((t for t in turns if t["turn"] == died_turn - 1), None)
                curr_turn = next((t for t in turns if t["turn"] == died_turn), None)
                if prev_turn and curr_turn:
                    # Let's see what happened to gemini-3-5-flash
                    # Let's find my head in prev_turn
                    my_prev = next((s for s in prev_turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
                    if my_prev:
                        px, py = my_prev["head"]["x"], my_prev["head"]["y"]
                        # Let's check my_prev health or body collisions or out of bounds.
                        # Wait, what was the winner or remaining snakes?
                        pass

