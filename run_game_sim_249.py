import json
from main import move

def run_sim(filepath):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                if "turn" in data and "board" in data:
                    turns.append(data)
                
    for i in range(len(turns) - 1):
        turn_data = turns[i]
        next_turn = turns[i+1]
        
        snakes = turn_data["board"]["snakes"]
        my_snake = None
        for s in snakes:
            if s["name"] == "gemini-3-5-flash":
                my_snake = s
                break
        if not my_snake:
            continue
            
        game_state = {
            "game": turn_data["game"],
            "turn": turn_data["turn"],
            "board": turn_data["board"],
            "you": my_snake
        }
        
        result = move(game_state)
        bot_move = result["move"]
        
        next_snakes = next_turn["board"]["snakes"]
        next_my_snake = None
        for s in next_snakes:
            if s["name"] == "gemini-3-5-flash":
                next_my_snake = s
                break
                
        if next_my_snake:
            curr_head = my_snake["head"]
            next_head = next_my_snake["head"]
            dx = next_head["x"] - curr_head["x"]
            dy = next_head["y"] - curr_head["y"]
            actual_move = None
            if dx == 1: actual_move = "right"
            elif dx == -1: actual_move = "left"
            elif dy == 1: actual_move = "up"
            elif dy == -1: actual_move = "down"
        else:
            print(f"Turn {turn_data['turn']}: gemini-3-5-flash died next turn. Bot chose {bot_move}")

run_sim("/logs/rounds/4/sim_249.jsonl")
