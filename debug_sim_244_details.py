import json

filepath = "/logs/rounds/1/sim_244.jsonl"
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            turn = data.get("turn")
            if turn is not None and 60 <= turn <= 65:
                print(f"\n================ Turn {turn} ================")
                board = data["board"]
                for s in board["snakes"]:
                    print(f"Snake: {s['name']}, Health: {s['health']}, Length: {len(s['body'])}, Head: ({s['body'][0]['x']}, {s['body'][0]['y']})")
                    print(f"  Body: {[(b['x'], b['y']) for b in s['body']]}")
