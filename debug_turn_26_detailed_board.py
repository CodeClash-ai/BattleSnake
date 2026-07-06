import json

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
        width, height = t["board"]["width"], t["board"]["height"]
        board_grid = [["." for _ in range(width)] for _ in range(height)]
        for s in t["board"]["snakes"]:
            for i, seg in enumerate(s["body"]):
                char = s["name"][0].upper()
                if i == 0:
                    char = "@" if s["name"] == "gemini-3-5-flash" else "O"
                board_grid[seg["y"]][seg["x"]] = char
        for y in reversed(range(height)):
            print(" ".join(board_grid[y]))
