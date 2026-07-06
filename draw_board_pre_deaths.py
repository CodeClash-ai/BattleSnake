import json

files = [("sim_210.jsonl", 234), ("sim_215.jsonl", 238), ("sim_219.jsonl", 35)]

for filename, target_turn in files:
    filepath = f"/logs/rounds/1/{filename}"
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
            
    print(f"\n=================== {filename} Turn {target_turn} ===================")
    
    width, height = turn_data["board"]["width"], turn_data["board"]["height"]
    grid = [["." for _ in range(width)] for _ in range(height)]
    
    my_snake = None
    for s in turn_data["board"]["snakes"]:
        if s["name"] == "gemini-3-5-flash":
            my_snake = s
        for seg in s["body"]:
            grid[seg["y"]][seg["x"]] = "O" if s["name"] != "gemini-3-5-flash" else "S"
            
    if my_snake:
        h = my_snake["head"]
        grid[h["y"]][h["x"]] = "H"
        
    for y in range(height-1, -1, -1):
        row = "".join(grid[y])
        print(f"{y:2d} | {row}")
    print("     " + "".join(str(x) for x in range(width)))
