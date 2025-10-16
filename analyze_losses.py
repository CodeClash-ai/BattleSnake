import json
import os

round_dir = "/logs/rounds/7"
our_name = "claude-sonnet-4-5-20250929"
opponent_name = "gemini-2.5-pro"

# Find first 5 losses
losses_found = 0
for i in range(1000):
    if losses_found >= 5:
        break
        
    game_file = f"{round_dir}/sim_{i}.jsonl"
    if not os.path.exists(game_file):
        continue
    
    with open(game_file, 'r') as f:
        lines = f.readlines()
        if len(lines) < 2:
            continue
        
        result = json.loads(lines[-1])
        if result.get('winnerName') != our_name and not result.get('isDraw', False):
            losses_found += 1
            print(f"\n=== Loss Game {i} ===")
            
            # Find when we died
            for j in range(len(lines)-2, -1, -1):
                state = json.loads(lines[j])
                if 'board' not in state:
                    continue
                    
                snakes = state['board']['snakes']
                our_snake = [s for s in snakes if s['name'] == our_name]
                
                if not our_snake:
                    # We died this turn
                    print(f"We died on turn {state['turn']}")
                    
                    # Check previous turn to see what happened
                    if j > 0:
                        prev_state = json.loads(lines[j-1])
                        prev_snakes = prev_state['board']['snakes']
                        prev_our = [s for s in prev_snakes if s['name'] == our_name]
                        prev_opp = [s for s in prev_snakes if s['name'] == opponent_name]
                        
                        if prev_our and prev_opp:
                            print(f"Turn {prev_state['turn']}: Our length={prev_our[0]['length']}, health={prev_our[0]['health']}")
                            print(f"Turn {prev_state['turn']}: Opp length={prev_opp[0]['length']}, health={prev_opp[0]['health']}")
                            print(f"Our head was at: {prev_our[0]['head']}")
                            print(f"Opp head was at: {prev_opp[0]['head']}")
                    break

print(f"\nAnalyzed {losses_found} losses")
