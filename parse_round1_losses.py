import os
import json

round_dir = "/logs/rounds/1"
sim_files = [os.path.join(round_dir, f) for f in os.listdir(round_dir) if f.endswith(".jsonl")]
losses = 0

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
            if "nbw__nbw-ruby" in alive_names and "gemini-3-5-flash" not in alive_names:
                losses += 1
                # Find out how the gemini snake died in the last few turns
                print(f"--- LOSS IN {os.path.basename(filepath)} ---")
                # Look at the sequence of states leading up to the end
                turns_to_show = []
                for line in reversed(lines):
                    try:
                        obj = json.loads(line)
                        if "board" in obj:
                            turns_to_show.append(obj)
                            if len(turns_to_show) >= 5:
                                break
                    except Exception:
                        pass
                for turn_state in reversed(turns_to_show):
                    turn = turn_state.get("turn")
                    my_snake = None
                    opp_snake = None
                    for s in turn_state["board"]["snakes"]:
                        if s["name"] == "gemini-3-5-flash":
                            my_snake = s
                        else:
                            opp_snake = s
                    print(f"Turn {turn}:")
                    if my_snake:
                        print(f"  My head: ({my_snake['head']['x']}, {my_snake['head']['y']}), length: {my_snake['length']}, health: {my_snake['health']}")
                    else:
                        print("  My snake: DEAD")
                    if opp_snake:
                        print(f"  Opp head: ({opp_snake['head']['x']}, {opp_snake['head']['y']}), length: {opp_snake['length']}, health: {opp_snake['health']}")
                    else:
                        print("  Opp snake: DEAD")
                print()
