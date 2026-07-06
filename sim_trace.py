import json

def trace_game(filepath):
    turns = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))
                
    for t in turns:
        if "winnerName" in t:
            print(f"Winner: {t['winnerName']}")
            continue
        if "board" not in t:
            continue
        board = t["board"]
        snakes = {s["name"]: s for s in board["snakes"]}
        if "gemini-3-5-flash" in snakes:
            my_snake = snakes["gemini-3-5-flash"]
            head = my_snake["head"]
            print(f"Turn {t['turn']}: head=({head['x']},{head['y']}), len={my_snake['length']}, health={my_snake['health']}")
        else:
            print(f"Turn {t['turn']}: Gemini is DEAD")

trace_game('/logs/rounds/0/sim_135.jsonl')
