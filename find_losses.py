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
        # We lost. Let's trace back from the end to find the exact state of our snake.
        # Let's inspect the last 5 turns.
        print(f"\n--- Loss in {fn} (Turn {len(lines)}) ---")
        for i in range(max(0, len(lines)-5), len(lines)):
            state = json.loads(lines[i])
            turn = state.get("turn")
            snakes = state.get("snakes", [])
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
