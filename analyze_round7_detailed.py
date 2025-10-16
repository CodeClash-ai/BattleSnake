import json
import os

round_dir = "/logs/rounds/7"
wins = 0
losses = 0
ties = 0
our_name = "claude-sonnet-4-5-20250929"
opponent_name = "gemini-2.5-pro"

# Sample 20 games to understand patterns
for i in range(0, 1000, 50):
    game_file = f"{round_dir}/sim_{i}.jsonl"
    if not os.path.exists(game_file):
        continue
    
    with open(game_file, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            continue
        
        # Get final state
        final_state = json.loads(lines[-1])
        board = final_state['board']
        
        snakes = board['snakes']
        if len(snakes) == 0:
            ties += 1
            print(f"Game {i}: TIE - both died")
        elif len(snakes) == 1:
            winner = snakes[0]['name']
            if winner == our_name:
                wins += 1
                print(f"Game {i}: WIN - we survived")
            else:
                losses += 1
                print(f"Game {i}: LOSS - opponent survived")
        else:
            # Both alive, check lengths
            our_snake = [s for s in snakes if s['name'] == our_name]
            opp_snake = [s for s in snakes if s['name'] == opponent_name]
            if our_snake and opp_snake:
                if our_snake[0]['length'] > opp_snake[0]['length']:
                    wins += 1
                    print(f"Game {i}: WIN - we're longer ({our_snake[0]['length']} vs {opp_snake[0]['length']})")
                elif our_snake[0]['length'] < opp_snake[0]['length']:
                    losses += 1
                    print(f"Game {i}: LOSS - opponent longer ({opp_snake[0]['length']} vs {our_snake[0]['length']})")
                else:
                    ties += 1
                    print(f"Game {i}: TIE - same length")

print(f"\nSample results: {wins} wins, {losses} losses, {ties} ties out of ~20 games")
