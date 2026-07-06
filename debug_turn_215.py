import json
from main import move, flood_fill_size, _manhattan

filepath = "/logs/rounds/1/sim_215.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

turn_data = None
for t in turns:
    if t.get("turn") == 238:
        turn_data = t
        break

if turn_data:
    snakes = turn_data["board"]["snakes"]
    my_snake = None
    for s in snakes:
        if s["name"] == "gemini-3-5-flash":
            my_snake = s
            break
            
    game_state = {
        "game": turn_data["game"],
        "turn": turn_data["turn"],
        "board": turn_data["board"],
        "you": my_snake
    }
    
    # Let's inspect everything before move logic
    board = game_state["board"]
    width, height = board["width"], board["height"]
    my_body = my_snake["body"]
    my_length = len(my_body)
    head_seg = my_body[0]
    head = (head_seg["x"], head_seg["y"])
    
    print("My Snake head:", head)
    print("My Snake length:", my_length)
    print("My Snake body:", my_body)
    print("All Snakes:")
    for s in snakes:
        print(f"Name: {s['name']}, Length: {len(s['body'])}, Health: {s['health']}, Head: {s['head']}")
        
    # Run the move decision manually with prints
    # Directions mapping
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
        
        # Add all body segments except the tail (if it's not growing and length > 1)
        for i, seg in enumerate(body):
            if i == len(body) - 1 and not is_growing and len(body) > 1:
                continue
            occupied.add((seg["x"], seg["y"]))
            
    print("Occupied size:", len(occupied))
    
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
                
                room_size = flood_fill_size(pos, occupied, width, height)
                
                safe_moves.append({
                    "direction": d,
                    "position": pos,
                    "is_dangerous": is_dangerous,
                    "room_size": room_size
                })
                
    print("Safe Moves calculated:")
    for sm in safe_moves:
        print(sm)
        
    res = move(game_state)
    print("Result:", res)
