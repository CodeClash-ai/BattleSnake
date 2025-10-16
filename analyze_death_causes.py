import json
import os

def analyze_death_causes(round_num):
    round_dir = f"/logs/rounds/{round_num}"
    
    death_causes = {
        "out_of_bounds": 0,
        "self_collision": 0,
        "opponent_collision": 0,
        "head_to_head": 0,
        "starvation": 0,
        "unknown": 0
    }
    
    games_analyzed = 0
    
    for filename in os.listdir(round_dir):
        if not filename.startswith("sim_") or not filename.endswith(".jsonl"):
            continue
            
        filepath = os.path.join(round_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
                
            # Get the last game state before death
            last_state = None
            for line in reversed(lines):
                data = json.loads(line)
                if 'board' in data:
                    last_state = data
                    break
            
            if not last_state:
                continue
                
            games_analyzed += 1
            
            # Check if we're in the game
            our_snake = None
            for snake in last_state['board']['snakes']:
                if 'claude-sonnet' in snake['name']:
                    our_snake = snake
                    break
            
            # If we're not in the final board state, we died
            if our_snake is None:
                # Look at second-to-last state to see our position
                second_last = None
                for line in reversed(lines[:-1]):
                    data = json.loads(line)
                    if 'board' in data:
                        second_last = data
                        break
                
                if second_last:
                    for snake in second_last['board']['snakes']:
                        if 'claude-sonnet' in snake['name']:
                            head = snake['head']
                            board_width = second_last['board']['width']
                            board_height = second_last['board']['height']
                            
                            # Check out of bounds
                            if head['x'] < 0 or head['x'] >= board_width or head['y'] < 0 or head['y'] >= board_height:
                                death_causes["out_of_bounds"] += 1
                            # Check starvation
                            elif snake['health'] == 0:
                                death_causes["starvation"] += 1
                            else:
                                death_causes["unknown"] += 1
                            break
                else:
                    death_causes["unknown"] += 1
                    
        except Exception as e:
            print(f"Error analyzing {filename}: {e}")
            continue
    
    print(f"\n=== Death Cause Analysis for Round {round_num} ===")
    print(f"Games analyzed: {games_analyzed}")
    print("\nDeath causes:")
    for cause, count in sorted(death_causes.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / games_analyzed * 100) if games_analyzed > 0 else 0
            print(f"  {cause}: {count} ({pct:.1f}%)")

if __name__ == "__main__":
    import sys
    round_num = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    analyze_death_causes(round_num)
