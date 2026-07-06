import json
from main import move

filepath = "/logs/rounds/0/sim_102.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

for t in turns:
    if t["turn"] == 25:
        my_snake = next(s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
        game_state = {
            "game": {},
            "turn": t["turn"],
            "board": t["board"],
            "you": my_snake
        }
        print("Our head at turn 25:", my_snake["head"])
        print("Bot choice at turn 25:", move(game_state))
