import json

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

last_turn = turns[-1]
print("Turn:", last_turn["turn"])
print("Snakes alive at final entry:")
for s in last_turn["board"]["snakes"]:
    print(s["name"], "head:", s["body"][0], "len:", len(s["body"]))
