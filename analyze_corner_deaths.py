import os
import json

log_dir = "/logs/rounds/0/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

deaths = []

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
        game_turns = [json.loads(line) for line in lines if "board" in json.loads(line)]
        if len(game_turns) >= 2:
            last_alive_turn = game_turns[-2]
            board = last_alive_turn.get("board", {})
            snakes = board.get("snakes", [])
            my_snake = [s for s in snakes if s['name'] == 'gemini-3-5-flash'][0]
            deaths.append({
                "file": fn,
                "turn": last_alive_turn['turn'],
                "head": my_snake['head'],
                "body": my_snake['body'],
                "length": my_snake['length'],
                "health": my_snake['health']
            })

for d in deaths[:15]:
    print(f"{d['file']} turn {d['turn']}: head: ({d['head']['x']},{d['head']['y']}), len: {d['length']}, health: {d['health']}")
    # Print body segments
    print(f"  Body: {d['body']}")
