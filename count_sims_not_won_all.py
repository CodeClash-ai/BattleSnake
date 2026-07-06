import os
import json

rounds_dir = "/logs/rounds"
for round_name in sorted(os.listdir(rounds_dir)):
    round_path = os.path.join(rounds_dir, round_name)
    if not os.path.isdir(round_path):
        continue
    not_won = []
    total = 0
    for filename in sorted(os.listdir(round_path)):
        if filename.startswith("sim_") and filename.endswith(".jsonl"):
            filepath = os.path.join(round_path, filename)
            total += 1
            is_won = False
            last_board = None
            winnerName = ""
            isDraw = False
            with open(filepath) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if "winnerName" in data:
                            winnerName = data["winnerName"]
                            isDraw = data.get("isDraw", False)
                        if "board" in data:
                            last_board = data
            if winnerName == "gemini-3-5-flash":
                is_won = True
            if not is_won:
                # Find turn and survivors
                alive = []
                turn = 0
                if last_board:
                    turn = last_board["turn"]
                    alive = [s["name"] for s in last_board["board"]["snakes"] if s["name"] != "gemini-3-5-flash"]
                not_won.append((filename, turn, alive, winnerName, isDraw))
    print(f"Round {round_name}: Out of {total} games, {len(not_won)} games not won by gemini-3-5-flash:")
    for fn, t, alive, winnerName, isDraw in not_won[:10]: # show first 10
        print(f"  {fn} at turn {t}, alive: {alive}, winner: {winnerName}, isDraw: {isDraw}")
