import json
from main import flood_fill_size, _manhattan

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 65:
                board = data["board"]
                width, height = board["width"], board["height"]
                my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
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
                
                print("Head:", head)
                print("Occupied:", sorted(list(occupied)))
                
                for d, pos in directions.items():
                    px, py = pos
                    if 0 <= px < width and 0 <= py < height:
                        in_occ = pos in occupied
                        room_size = flood_fill_size(pos, occupied, width, height)
                        print(f"Dir: {d:5s}, Pos: {pos}, In Occupied: {in_occ}, Room Size: {room_size}")

# Let's inspect Turn 64 options to see how we got here!
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 64:
                board = data["board"]
                width, height = board["width"], board["height"]
                my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
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
                
                print("\n--- Turn 64 ---")
                print("Head:", head)
                for d, pos in directions.items():
                    px, py = pos
                    if 0 <= px < width and 0 <= py < height:
                        in_occ = pos in occupied
                        room_size = flood_fill_size(pos, occupied, width, height)
                        print(f"Dir: {d:5s}, Pos: {pos}, In Occupied: {in_occ}, Room Size: {room_size}")

# Let's inspect Turn 63 options to see how we got here!
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 63:
                board = data["board"]
                width, height = board["width"], board["height"]
                my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
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
                
                print("\n--- Turn 63 ---")
                print("Head:", head)
                for d, pos in directions.items():
                    px, py = pos
                    if 0 <= px < width and 0 <= py < height:
                        in_occ = pos in occupied
                        room_size = flood_fill_size(pos, occupied, width, height)
                        print(f"Dir: {d:5s}, Pos: {pos}, In Occupied: {in_occ}, Room Size: {room_size}")

# Let's inspect Turn 61 options!
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 61:
                board = data["board"]
                width, height = board["width"], board["height"]
                my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
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
                
                print("\n--- Turn 61 ---")
                print("Head:", head)
                for d, pos in directions.items():
                    px, py = pos
                    if 0 <= px < width and 0 <= py < height:
                        in_occ = pos in occupied
                        room_size = flood_fill_size(pos, occupied, width, height)
                        print(f"Dir: {d:5s}, Pos: {pos}, In Occupied: {in_occ}, Room Size: {room_size}")

# Let's inspect Turn 62 options!
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("turn") == 62:
                board = data["board"]
                width, height = board["width"], board["height"]
                my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
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
                
                print("\n--- Turn 62 ---")
                print("Head:", head)
                for d, pos in directions.items():
                    px, py = pos
                    if 0 <= px < width and 0 <= py < height:
                        in_occ = pos in occupied
                        room_size = flood_fill_size(pos, occupied, width, height)
                        print(f"Dir: {d:5s}, Pos: {pos}, In Occupied: {in_occ}, Room Size: {room_size}")
