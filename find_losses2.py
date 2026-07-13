import os
import json

log_dir = "/logs/rounds/0/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

for fn in sim_files:
    path = os.path.join(log_dir, fn)
    with open(path, 'r') as f:
        lines = f.readlines()
    if not lines:
        continue
    last_line = json.loads(lines[-1])
    winner = last_line.get("winnerName", None)
    is_draw = last_line.get("isDraw", False)
    if not is_draw and winner != "gemini-3-5-flash":
        # We lost. Let's find the exact turns up to the end
        print(f"\n--- Loss in {fn} (Turn {len(lines)}) ---")
        # Let's count valid turns or inspect backward
        # Filter lines that have 'board'
        game_turns = []
        for line in lines:
            data = json.loads(line)
            if "board" in data:
                game_turns.append(data)
        
        # Look at the last 5 turns of actual gameplay
        for gt in game_turns[-5:]:
            turn = gt.get("turn")
            board = gt.get("board", {})
            snakes = board.get("snakes", [])
            
            my_snake = [s for s in snakes if s['name'] == 'gemini-3-5-flash']
            opp_snake = [s for s in snakes if s['name'] != 'gemini-3-5-flash']
            
            my_info = "DEAD"
            if my_snake:
                s = my_snake[0]
                my_info = f"Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}"
                
            opp_info = "DEAD"
            if opp_snake:
                s = opp_snake[0]
                opp_info = f"Head: ({s['head']['x']},{s['head']['y']}), Len: {s['length']}, Health: {s['health']}"
                
            print(f"Turn {turn}: Our Snake: {my_info} | Opp Snake: {opp_info}")
