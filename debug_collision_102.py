import json
from main import move, flood_fill_size

filepath = "/logs/rounds/0/sim_102.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

for t in turns:
    if t["turn"] == 26:
        my_snake = next((s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash"), None)
        if not my_snake:
            continue
        game_state = {
            "game": {},
            "turn": t["turn"],
            "board": t["board"],
            "you": my_snake
        }
        
        board = game_state["board"]
        width, height = board["width"], board["height"]
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
                
        print("Occupied cells:", occupied)
        
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
                                print(f"Move {d} to {pos} is dangerous because opponent head is {opp_head} and len {opp_len} >= our len {my_length}")
                    
                    room_size = flood_fill_size(pos, occupied, width, height, max_depth=15)
                    print(f"Move {d} to {pos}: is_dangerous={is_dangerous}, room_size={room_size}")
