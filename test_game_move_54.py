import json
from main import move

# Let's mock the game_state from turn 54 where you is Snake1 (d717c6dd-6982-4dbe-b93c-169c9bb5c1aa)
with open("test_game.json") as f:
    lines = f.readlines()

for line in lines:
    try:
        data = json.loads(line)
        if "turn" in data and data["turn"] == 54 and data["you"]["id"] == "d717c6dd-6982-4dbe-b93c-169c9bb5c1aa":
            # Let's run move(data)
            res = move(data)
            print("Move result:", res)
            
            # Let's trace occupied cells and safe_moves manually
            board = data["board"]
            width, height = board["width"], board["height"]
            my_snake = data["you"]
            my_body = my_snake["body"]
            head = (my_body[0]["x"], my_body[0]["y"])
            print("Head:", head)
            
            directions = {
                "up": (head[0], head[1] + 1),
                "down": (head[0], head[1] - 1),
                "left": (head[0] - 1, head[1]),
                "right": (head[0] + 1, head[1])
            }
            occupied = set()
            for s in board["snakes"]:
                for seg in s["body"]:
                    occupied.add((seg["x"], seg["y"]))
            print("Occupied cells:", sorted(list(occupied)))
            for d, pos in directions.items():
                in_bounds = 0 <= pos[0] < width and 0 <= pos[1] < height
                not_occ = pos not in occupied if in_bounds else False
                print(f"Dir {d} to {pos}: In bounds: {in_bounds}, Not occupied: {not_occ}")
    except Exception as e:
        import traceback
        traceback.print_exc()
