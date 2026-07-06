import json

filepath = "/logs/rounds/1/sim_215.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "board" in data:
                turns.append(data)

# Print turns around 220 to 230
for t in turns:
    turn_num = t.get("turn")
    if turn_num is not None and 215 <= turn_num <= 230:
        # Find snake
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        
        # Calculate moves manually
        board = t["board"]
        width, height = board["width"], board["height"]
        head = (my_snake["head"]["x"], my_snake["head"]["y"])
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
                
        choices = []
        from main import flood_fill_size
        for d, pos in directions.items():
            if 0 <= pos[0] < width and 0 <= pos[1] < height:
                if pos not in occupied:
                    room = flood_fill_size(pos, occupied, width, height)
                    choices.append(f"{d} (room: {room})")
        print(f"Turn {turn_num}: head {head}, snake len: {len(my_snake['body'])}, choices: {', '.join(choices)}")
