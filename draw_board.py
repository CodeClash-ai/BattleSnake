import json

filepath = "/logs/rounds/1/sim_210.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    turn_num = t.get("turn")
    if turn_num == 228:
        # Construct grid
        width, height = 11, 11
        grid = [["." for _ in range(width)] for _ in range(height)]
        
        # Mark snake
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
            # Mark other snakes
            for seg in s["body"]:
                grid[seg["y"]][seg["x"]] = "O" if s["name"] != "gemini-3-5-flash" else "S"
        
        # Mark my head specially
        h = my_snake["head"]
        grid[h["y"]][h["x"]] = "H"
        
        # Print grid from top (y = 10) to bottom (y = 0)
        for y in range(height-1, -1, -1):
            row = "".join(grid[y])
            print(f"{y:2d} | {row}")
        print("     " + "".join(str(x) for x in range(width)))

print("\n--- Board at turn 229 ---")
for t in turns:
    turn_num = t.get("turn")
    if turn_num == 229:
        width, height = 11, 11
        grid = [["." for _ in range(width)] for _ in range(height)]
        
        my_snake = None
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
            for seg in s["body"]:
                grid[seg["y"]][seg["x"]] = "O" if s["name"] != "gemini-3-5-flash" else "S"
        
        h = my_snake["head"]
        grid[h["y"]][h["x"]] = "H"
        
        for y in range(height-1, -1, -1):
            row = "".join(grid[y])
            print(f"{y:2d} | {row}")
        print("     " + "".join(str(x) for x in range(width)))
