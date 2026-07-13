import os
import json

log_dir = "/logs/rounds/1/"
sim_files = [f for f in os.listdir(log_dir) if f.startswith("sim_") and f.endswith(".jsonl")]

our_wins = 0
opp_wins = 0
ties = 0

for fn in sim_files:
    path = os.path.join(log_dir, fn)
    with open(path, 'r') as f:
        lines = f.readlines()
    if not lines:
        continue
    # parse the last line
    last_line = json.loads(lines[-1])
    # check winnerName
    winner = last_line.get("winnerName", None)
    is_draw = last_line.get("isDraw", False)
    if is_draw:
        ties += 1
    elif winner == "gemini-3-5-flash":
        our_wins += 1
    else:
        opp_wins += 1
        # let's see how our snake died by checking the line before last
        penultimate = json.loads(lines[-2])
        # Find the snakes
        turn = penultimate.get("turn")
        you = penultimate.get("you", {})
        my_len = you.get("length")
        my_head = you.get("head")
        my_health = you.get("health")
        print(f"Opponent {winner} won {fn} on turn {turn}. Our Head: {my_head}, Len: {my_len}, Health: {my_health}")

print(f"Our wins: {our_wins}, Opp wins: {opp_wins}, Ties: {ties}")
