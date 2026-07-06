import json

filepath = "/logs/rounds/1/sim_210.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

for t in turns:
    # Print turns leading up to 234 to see how it trapped itself
    turn_num = t.get("turn")
    if turn_num is not None and 228 <= turn_num <= 234:
        print(f"Turn {turn_num}:")
        for s in t["board"]["snakes"]:
            if s["name"] == "gemini-3-5-flash":
                print("  gemini-3-5-flash Head:", s["head"])
                print("  gemini-3-5-flash Body (first 10):", s["body"][:10])
