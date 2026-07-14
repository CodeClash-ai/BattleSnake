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
                # Get states
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

for filename, states in sorted(losses)[:10]:
    print(f"\n==================== {filename} ====================")
    if len(states) >= 2:
        alive_state = states[1]
        dead_state = states[0]
        # Let's see what moves were chosen/possible in the last turn alive
        turn = alive_state["turn"]
        my_snake = next((s for s in alive_state["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        opp_snake = next((s for s in alive_state["board"]["snakes"] if s["name"] != "gemini-3-5-flash"), None)
        if my_snake:
            head = (my_snake["head"]["x"], my_snake["head"]["y"])
            # Let's print neighbors of head and if they are blocked by walls or bodies or opponent heads
            neighbors = {
                "up": (head[0], head[1]+1),
                "down": (head[0], head[1]-1),
                "left": (head[0]-1, head[1]),
                "right": (head[0]+1, head[1])
            }
            print(f"Turn {turn}: Head at {head}. Neighbors:")
            # Obstacles
            obstacle_positions = set()
            for s in alive_state["board"]["snakes"]:
                is_growing = (s["health"] == 100)
                body = s["body"]
                active_body = body if is_growing else body[:-1]
                for seg in active_body:
                    obstacle_positions.add((seg["x"], seg["y"]))
            
            width = alive_state["board"]["width"]
            height = alive_state["board"]["height"]
            
            for d, pos in neighbors.items():
                status = "SAFE"
                if not (0 <= pos[0] < width and 0 <= pos[1] < height):
                    status = "WALL"
                elif pos in obstacle_positions:
                    status = "BODY"
                print(f"  {d}: {pos} -> {status}")
