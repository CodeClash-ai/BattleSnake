import json

files = [("sim_244.jsonl", 59), ("sim_244.jsonl", 60), ("sim_244.jsonl", 61), ("sim_244.jsonl", 62), ("sim_244.jsonl", 63)]

for filename, target_turn in files:
    filepath = f"/logs/rounds/0/{filename}"
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    
    # Get last turn
    turn_data = None
    for t in turns:
        if t.get("turn") == target_turn:
            turn_data = t
            break
            
    if not turn_data:
        print(f"Turn {target_turn} not found in {filename}")
        continue
        
    print(f"\n=================== {filename} Turn {target_turn} ===================")
    
    width, height = turn_data["board"]["width"], turn_data["board"]["height"]
    grid = [["." for _ in range(width)] for _ in range(height)]
    
    my_snake = None
    for s in turn_data["board"]["snakes"]:
        if s["name"] == "gemini-3-5-flash":
            my_snake = s
        for idx, seg in enumerate(s["body"]):
            char = "O" if s["name"] != "gemini-3-5-flash" else "S"
            if idx == 0:
                char = "H" if s["name"] == "gemini-3-5-flash" else "X"
            grid[seg["y"]][seg["x"]] = char
            
    for y in range(height-1, -1, -1):
        row = "".join(grid[y])
        print(f"{y:2d} | {row}")
    print("     " + "".join(str(x) for x in range(width)))
