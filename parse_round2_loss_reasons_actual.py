import os
import json

round_dir = "/logs/rounds/2"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl") and os.path.getsize(os.path.join(round_dir, f)) > 0]

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
            if "gemini-3-5-flash" not in alive_names:
                # We lost
                states = []
                for line in reversed(lines):
                    try:
                        obj = json.loads(line)
                        if "board" in obj:
                            states.append(obj)
                            if len(states) >= 3:
                                break
                    except Exception:
                        pass
                losses.append((os.path.basename(filepath), states))

print(f"Total losses: {len(losses)}")
for filename, states in sorted(losses)[:10]:
    print(f"\n==================== {filename} ====================")
    if len(states) >= 2:
        alive_state = states[1]
        dead_state = states[0]
        turn = alive_state["turn"]
        print(f"Turn {turn} (Last turn alive):")
        # Find our snake in alive_state
        our_snake = None
        for s in alive_state["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                our_snake = s
        opp_snake = None
        for s in alive_state["board"]["snakes"]:
            if s["name"] != "gemini-3-5-flash":
                opp_snake = s
        if our_snake and opp_snake:
            print(f"Our head: {our_snake['head']}, length: {our_snake['length']}, health: {our_snake['health']}")
            print(f"Opp head: {opp_snake['head']}, length: {opp_snake['length']}, health: {opp_snake['health']}")
            # Let's find what action was taken by seeing where our head went in dead_state or if we just died of starvation/collision
            our_dead_snake = None
            for s in dead_state["board"]["snakes"]:
                if s["name"] == "gemini-3-5-flash":
                    our_dead_snake = s
            if not our_dead_snake:
                print("We died on transition to next turn!")
                # Let's find standard hazards or if our head crashed into wall or body
                head = our_snake['head']
                print(f"Last known head: {head}")
            else:
                print(f"We are still alive? Head: {our_dead_snake['head']}")
