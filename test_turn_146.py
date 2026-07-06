import json
from main import move

filepath = "/logs/rounds/4/sim_219.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if "turn" in data:
                turns.append(data)

t = next(turn for turn in turns if turn["turn"] == 146)
my_snake = next(s for s in t["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
game_state = {
    "game": t["game"],
    "turn": t["turn"],
    "board": t["board"],
    "you": my_snake
}

res = move(game_state)
print("Move result:", res)
