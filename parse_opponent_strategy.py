import json
import glob

sim_files = glob.glob("/logs/rounds/0/*.jsonl")
tot_moves = 0
head_collisions = 0
body_collisions = 0
wall_collisions = 0

for path in sim_files:
    with open(path) as f:
        lines = f.readlines()
    if not lines: continue
    
    # Analyze the opponent's moves
    for idx, line in enumerate(lines):
        try:
            data = json.loads(line)
        except:
            continue
        if "board" not in data: continue
        # Find opponent
        opp = None
        for s in data["board"]["snakes"]:
            if s["name"] == "OliverMKing__astar-snake":
                opp = s
                break
        # Just verifying general lengths or food consumption
