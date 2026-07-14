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
                # This is a loss
                # Let's get the last two states with "board" in them
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
    # Print the last turn when we were alive
    if len(states) >= 2:
        alive_state = states[1]
        dead_state = states[0]
        turn = alive_state["turn"]
        print(f"Turn {turn} (Last turn alive):")
        # Let's find my snake and opponent
        my_snake = next((s for s in alive_state["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        opp_snake = next((s for s in alive_state["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
        if my_snake:
            print(f"  My head: ({my_snake['head']['x']}, {my_snake['head']['y']}), length: {my_snake['length']}, health: {my_snake['health']}")
            print(f"  My body: {[(b['x'], b['y']) for b in my_snake['body']]}")
        if opp_snake:
            print(f"  Opp head: ({opp_snake['head']['x']}, {opp_snake['head']['y']}), length: {opp_snake['length']}, health: {opp_snake['health']}")
            print(f"  Opp body: {[(b['x'], b['y']) for b in opp_snake['body']]}")
        print(f"Turn {dead_state['turn']} (Death turn):")
        my_snake_dead = next((s for s in dead_state["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        opp_snake_dead = next((s for s in dead_state["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
        if my_snake_dead:
            print(f"  My head: ({my_snake_dead['head']['x']}, {my_snake_dead['head']['y']})")
        else:
            print("  My snake: DEAD")
        if opp_snake_dead:
            print(f"  Opp head: ({opp_snake_dead['head']['x']}, {opp_snake_dead['head']['y']})")
