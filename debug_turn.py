import json
from main import move

with open("/logs/rounds/4/sim_247.jsonl") as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 249:
                snakes = data["board"]["snakes"]
                my_snake = None
                for s in snakes:
                    if s["name"] == "gemini-3-5-flash":
                        my_snake = s
                        break
                game_state = {
                    "game": data["game"],
                    "turn": data["turn"],
                    "board": data["board"],
                    "you": my_snake
                }
                # Inspect board/occupied info as our code sees it
                print("My head:", my_snake["head"])
                print("My length:", len(my_snake["body"]))
                print("My body:", my_snake["body"])
                
                # Check possible moves
                width = data["board"]["width"]
                height = data["board"]["height"]
                head = (my_snake["head"]["x"], my_snake["head"]["y"])
                directions = {
                    "up": (head[0], head[1] + 1),
                    "down": (head[0], head[1] - 1),
                    "left": (head[0] - 1, head[1]),
                    "right": (head[0] + 1, head[1])
                }
                
                occupied = set()
                for snake in data["board"].get("snakes", []):
                    body = snake["body"]
                    is_growing = snake["health"] == 100
                    for i, seg in enumerate(body):
                        if i == len(body) - 1 and not is_growing and len(body) > 1:
                            continue
                        occupied.add((seg["x"], seg["y"]))
                
                print("Occupied set:", sorted(list(occupied)))
                for d, pos in directions.items():
                    px, py = pos
                    in_bounds = 0 <= px < width and 0 <= py < height
                    is_occ = pos in occupied
                    print(f"Move {d} to {pos}: in_bounds={in_bounds}, occupied={is_occ}")
                
                # Run the actual move function to see its return
                res = move(game_state)
                print("Move result:", res)
