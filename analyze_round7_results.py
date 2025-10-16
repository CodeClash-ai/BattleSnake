import json
import os

round_dir = "/logs/rounds/7"
wins = 0
losses = 0
ties = 0
our_name = "claude-sonnet-4-5-20250929"

# Check all games
for i in range(1000):
    game_file = f"{round_dir}/sim_{i}.jsonl"
    if not os.path.exists(game_file):
        continue
    
    with open(game_file, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            continue
        
        # Get final result
        result = json.loads(lines[-1])
        
        if result.get('isDraw', False):
            ties += 1
        elif result.get('winnerName') == our_name:
            wins += 1
        else:
            losses += 1

print(f"Round 7 Results:")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Ties: {ties}")
print(f"Win rate: {wins/(wins+losses+ties)*100:.1f}%")
