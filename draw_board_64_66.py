import json

files = [("sim_244.jsonl", 64), ("sim_244.jsonl", 65), ("sim_244.jsonl", 66)]

for filename, target_turn in files:
    filepath = f"/logs/rounds/1/{filename}"
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    
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
    
    for s in turn_data["board"]["snakes"]:
        for idx, seg in enumerate(s["body"]):
            char = "O" if s["name"] != "gemini-3-5-flash" else "S"
            if idx == 0:
                char = "H" if s["name"] == "gemini-3-5-flash" else "X"
            grid[seg["y"]][seg["x"]] = char
            
    for y in range(height-1, -1, -1):
        row = "".join(grid[y])
        print(f"{y:2d} | {row}")
    print("     " + "".join(str(x) for x in range(width)))
