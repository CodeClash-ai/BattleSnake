import json
from main import move

with open("/logs/rounds/2/sim_10.jsonl") as f:
    for line in f:
        data = json.loads(line)
        if data.get("turn") == 32:
            # We need to find the state where gemini-3-5-flash was "you" (the active snake request is stored in lines, but in standard game log, each turn has one record with "you" being one of the snakes. Let's find or construct the actual request for gemini-3-5-flash).
            # The game engine logs standard board. We can just set data["you"] to the gemini snake.
            gemini_snake = next(s for s in data['board']['snakes'] if "gemini" in s["name"])
            data["you"] = gemini_snake
            
            # Let's inspect the decision process
            board = data["board"]
            width, height = board["width"], board["height"]
            my_snake = data["you"]
            my_body = my_snake["body"]
            my_length = len(my_body)
            head_seg = my_body[0]
            head = (head_seg["x"], head_seg["y"])

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

            print("occupied:", occupied)

            safe_moves = []
            for d, pos in directions.items():
                px, py = pos
                if 0 <= px < width and 0 <= py < height:
                    if pos not in occupied:
                        is_dangerous = False
                        for snake in board.get("snakes", []):
                            if snake["id"] == my_snake["id"]:
                                continue
                            opp_head = (snake["body"][0]["x"], snake["body"][0]["y"])
                            opp_len = len(snake["body"])
                            if abs(pos[0] - opp_head[0]) + abs(pos[1] - opp_head[1]) == 1:
                                if opp_len >= my_length:
                                    is_dangerous = True
                                    break
                        
                        from main import flood_fill_size
                        room_size = flood_fill_size(pos, occupied, width, height, max_depth=15)
                        safe_moves.append({
                            "direction": d,
                            "position": pos,
                            "is_dangerous": is_dangerous,
                            "room_size": room_size
                        })

            print("safe_moves:")
            for m in safe_moves:
                print(m)
            print("Move selected:", move(data))
