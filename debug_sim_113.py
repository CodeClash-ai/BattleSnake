import json

filepath = "/logs/rounds/1/sim_113.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

print("Total turns:", len(turns))
# Find when gemini-3-5-flash died
for i, turn in enumerate(turns):
    if "board" in turn:
        names = [s["name"] for s in turn["board"]["snakes"]]
        if "gemini-3-5-flash" not in names:
            print("Died on turn:", turn["turn"])
            prev_turn = turns[i-1]
            my_prev = next(s for s in prev_turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
            print("Head at last turn:", my_prev["head"])
            print("Bob head at last turn:", next(s for s in prev_turn["board"]["snakes"] if s["name"] == "coreyja_bombastic-bob")["head"])
            break
# Let's inspect turns 105, 106, 107
for t in range(104, 108):
    turn_data = next(turn for turn in turns if turn.get("turn") == t)
    for s in turn_data["board"]["snakes"]:
        print(f"Turn {t} - Snake {s['name']}: head {s['head']}, len {len(s['body'])}, health {s['health']}")
