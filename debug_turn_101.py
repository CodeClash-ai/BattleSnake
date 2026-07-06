import json
from main import move

filepath = "/logs/rounds/0/sim_101.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            d = json.loads(line)
            if "turn" in d:
                turns.append(d)

for t in turns:
    if t["turn"] == 32:
        # Reconstruct game state
        my_snake = next(s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
        game_state = {
            "game": {},
            "turn": t["turn"],
            "board": t["board"],
            "you": my_snake
        }
        # Run move
        print("Our body:", my_snake["body"])
        print("Our head:", my_snake["head"])
        print("Board snakes:")
        for s in t["board"]["snakes"]:
            print(f"Snake {s['name']}: body={s['body']}")
        print("Selected move:", move(game_state))
