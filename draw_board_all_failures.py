import json

files = ["sim_210.jsonl", "sim_215.jsonl", "sim_219.jsonl"]

for filename in files:
    filepath = f"/logs/rounds/1/{filename}"
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    
    # Get last turn
    last_turn = turns[-1]
    turn_num = last_turn.get("turn")
    print(f"\n=================== {filename} Turn {turn_num} ===================")
    
    width, height = last_turn["board"]["width"], last_turn["board"]["height"]
    grid = [["." for _ in range(width)] for _ in range(height)]
    
    my_snake = None
    for s in last_turn["board"]["snakes"]:
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
