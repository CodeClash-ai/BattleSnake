import json
from main import move

with open("/logs/rounds/1/sim_246.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if data.get("turn") == 120:
            # Set 'you' to gemini-3-5-flash so we see its perspective
            gemini_snake = next(s for s in data["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
            data["you"] = gemini_snake
            result = move(data)
            print("Move result:", result)
            
            # Let's see the safe moves list from inside
            # Since we can replicate move() logic:
            board = data["board"]
            width, height = board["width"], board["height"]
            my_snake = gemini_snake
            my_body = my_snake["body"]
            my_length = len(my_body)
            head = (my_body[0]["x"], my_body[0]["y"])
            directions = {
                "up": (head[0], head[1] + 1),
                "down": (head[0], head[1] - 1),
                "left": (head[0] - 1, head[1]),
                "right": (head[0] + 1, head[1])
            }
            occupied = set()
            for snake in board.get("snakes", []):
                body = snake["body"]
                is_growing = snake["health"] == 100
                for i, seg in enumerate(body):
                    if i == len(body) - 1 and not is_growing and len(body) > 1:
                        continue
                    occupied.add((seg["x"], seg["y"]))
            
            print("Head at:", head)
            print("Occupied:", sorted(list(occupied)))
            for d, pos in directions.items():
                in_bounds = 0 <= pos[0] < width and 0 <= pos[1] < height
                is_occ = pos in occupied
                print(f"Dir: {d}, pos: {pos}, in_bounds: {in_bounds}, occupied: {is_occ}")
            break
