import json
import sys
sys.path.append("/workspace")
from main import move

def run_trace(filepath, target_turn):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
    for turn in turns:
        if turn["turn"] == target_turn:
            my_snake = next(s for s in turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
            game_state = {
                "game": turn.get("game", {}),
                "turn": turn["turn"],
                "board": turn["board"],
                "you": my_snake
            }
            res = move(game_state)
            print(f"Turn {target_turn}: {res}")
            break

run_trace("/logs/rounds/0/sim_128.jsonl", 50)
run_trace("/logs/rounds/0/sim_128.jsonl", 51)
run_trace("/logs/rounds/0/sim_128.jsonl", 52)
run_trace("/logs/rounds/0/sim_128.jsonl", 53)
