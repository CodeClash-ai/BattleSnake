import json

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "board" in data:
                turn = data.get("turn")
                if 58 <= turn <= 65:
                    board = data["board"]
                    my_snake = [s for s in board["snakes"] if s["name"] == "gemini-3-5-flash"][0]
                    # Print food list
                    food = board["food"]
                    food_coords = [(f["x"], f["y"]) for f in food]
                    print(f"Turn {turn}: Food coords: {food_coords}, My health: {my_snake['health']}")
