import json

filename = "sim_185.jsonl"
filepath = f"/logs/rounds/0/{filename}"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for turn_num in [147, 148]:
    t = [turn for turn in turns if turn.get("turn") == turn_num][0]
    print(f"\n--- Turn {turn_num} ---")
    width, height = t["board"]["width"], t["board"]["height"]
    grid = [["." for _ in range(width)] for _ in range(height)]
    for s in t["board"]["snakes"]:
        name = s["name"]
        for idx, seg in enumerate(s["body"]):
            char = "O" if name != "gemini-3-5-flash" else "S"
            if idx == 0:
                char = "H" if name == "gemini-3-5-flash" else "X"
            grid[seg["y"]][seg["x"]] = char
    for y in range(height-1, -1, -1):
        print(f"{y:2d} | " + "".join(grid[y]))
    print("     " + "".join(str(x) for x in range(width)))
