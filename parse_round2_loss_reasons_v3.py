import os
import json

round_dir = "/logs/rounds/1"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl")]

losses = []

for filepath in sim_files:
    with open(filepath, "r") as f:
        lines = f.readlines()
        if not lines:
            continue
        last_turn_data = None
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                if "board" in obj:
                    last_turn_data = obj
                    break
            except Exception:
                pass
        
        if last_turn_data:
            snakes = last_turn_data["board"]["snakes"]
            alive_names = [s["name"] for s in snakes]
            if "jackisherwood__battlesnake-elon" in alive_names and "gemini-3-5-flash" not in alive_names:
                states = []
                for line in reversed(lines):
                    try:
                        obj = json.loads(line)
                        if "board" in obj:
                            states.append(obj)
                            if len(states) >= 15: # let's go further back
                                break
                    except Exception:
                        pass
                losses.append((os.path.basename(filepath), states))

for filename, states in sorted(losses)[:3]:
    print(f"\n==================== {filename} ====================")
    for state in reversed(states):
        turn = state["turn"]
        my_snake = next((s for s in state["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        opp_snake = next((s for s in state["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
        if my_snake:
            head = (my_snake["head"]["x"], my_snake["head"]["y"])
            print(f"Turn {turn}: head={head}, length={my_snake['length']}, health={my_snake['health']}")
        else:
            print(f"Turn {turn}: DEAD")
