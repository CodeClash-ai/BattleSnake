import json
from main import move, flood_fill_size

with open("test_game.json") as f:
    lines = f.readlines()

for line in lines:
    try:
        data = json.loads(line)
        if "turn" in data and data["turn"] == 51 and data["you"]["id"] == "d717c6dd-6982-4dbe-b93c-169c9bb5c1aa":
            board = data["board"]
            width, height = board["width"], board["height"]
            my_snake = data["you"]
            my_body = my_snake["body"]
            head = (my_body[0]["x"], my_body[0]["y"])
            print("Head:", head)
            
            occupied = set()
            for s in board["snakes"]:
                for seg in s["body"]:
                    occupied.add((seg["x"], seg["y"]))
            
            # Let us see what move choices we had at turn 51
            directions = {
                "up": (head[0], head[1] + 1),
                "down": (head[0], head[1] - 1),
                "left": (head[0] - 1, head[1]),
                "right": (head[0] + 1, head[1])
            }
            for d, pos in directions.items():
                in_bounds = 0 <= pos[0] < width and 0 <= pos[1] < height
                if in_bounds:
                    not_occ = pos not in occupied
                    room_sz = flood_fill_size(pos, occupied, width, height) if not_occ else 0
                    print(f"Dir {d} to {pos}: Not occupied: {not_occ}, room size: {room_sz}")
    except Exception as e:
        import traceback
        traceback.print_exc()
