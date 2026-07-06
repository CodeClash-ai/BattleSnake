import json
import os
import sys

# Append the directory containing main.py to path
sys.path.append("/workspace")
from main import move

def run_move_on_turn(filepath, turn_num):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "board" in data:
                    turns.append(data)
                    
    for turn in turns:
        if turn["turn"] == turn_num:
            # We need to construct a proper game_state for our move function
            # The game state passed to move is structured like this:
            # {
            #   "game": turn["game"],
            #   "turn": turn["turn"],
            #   "board": turn["board"],
            #   "you": our_snake_object
            # }
            my_snake = next(s for s in turn["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
            game_state = {
                "game": turn.get("game", {}),
                "turn": turn["turn"],
                "board": turn["board"],
                "you": my_snake
            }
            # Run move
            res = move(game_state)
            print(f"Turn {turn_num} decided move: {res}")
            break

failures = [
    ("sim_128.jsonl", 110),
    ("sim_131.jsonl", 95),
    ("sim_154.jsonl", 60),
    ("sim_195.jsonl", 68),
    ("sim_221.jsonl", 120),
    ("sim_223.jsonl", 60),
    ("sim_27.jsonl", 58)
]

for f, turn_num in failures:
    print(f"\nAnalyzing choice in {f}:")
    run_move_on_turn(os.path.join("/logs/rounds/0", f), turn_num)

# Let's inspect sim_128.jsonl turn 110 details
# My head: {'x': 0, 'y': 0}, length: 7
# My body: [(0, 0), (1, 0), (1, 1), (0, 1), (0, 2), (0, 3), (0, 4)]
# Board size is usually 11x11 (from 0 to 10)
# From (0,0), directions are:
# - up: (0, 1) -> occupied by my body
# - down: (0, -1) -> out of bounds
# - left: (-1, 0) -> out of bounds
# - right: (1, 0) -> occupied by my body
# Wait, we are completely trapped! Let's check!
