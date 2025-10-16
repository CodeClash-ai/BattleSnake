import json
import os
from collections import defaultdict

def analyze_game(filepath):
    """Analyze a single game log"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        return None
    
    # Skip first line (metadata), get final state
    final_state = json.loads(lines[-1])
    
    # Determine winner
    snakes = final_state['board']['snakes']
    our_name = 'claude-sonnet-4-5-20250929'
    opp_name = 'gemini-2.5-pro'
    
    our_alive = any(s['name'] == our_name for s in snakes)
    opp_alive = any(s['name'] == opp_name for s in snakes)
    
    if our_alive and not opp_alive:
        return 'we_won'
    elif opp_alive and not our_alive:
        return 'we_lost'
    elif not our_alive and not opp_alive:
        return 'tie'
    else:
        return 'both_alive'

def analyze_death_cause(filepath, our_name='claude-sonnet-4-5-20250929'):
    """Analyze how our snake died"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 2:
        return None
    
    prev_state = None
    
    for line in lines[1:]:  # Skip metadata line
        state = json.loads(line)
        snakes = {s['id']: s for s in state['board']['snakes']}
        
        # Find our snake
        our_id = None
        for sid, snake in snakes.items():
            if snake['name'] == our_name:
                our_id = sid
                break
        
        if prev_state:
            prev_snakes = {s['id']: s for s in prev_state['board']['snakes']}
            
            # Check if we just died
            if our_id:
                # We're alive now, continue
                pass
            else:
                # We're dead now, check if we were alive before
                our_prev_id = None
                for sid, snake in prev_snakes.items():
                    if snake['name'] == our_name:
                        our_prev_id = sid
                        break
                
                if our_prev_id:
                    # We just died
                    return analyze_death_reason(prev_state, state, our_prev_id, our_name)
        
        prev_state = state
    
    return None

def analyze_death_reason(prev_state, curr_state, our_id, our_name):
    """Determine why we died"""
    prev_snakes = {s['id']: s for s in prev_state['board']['snakes']}
    our_snake = prev_snakes[our_id]
    our_head = (our_snake['head']['x'], our_snake['head']['y'])
    our_body = [(b['x'], b['y']) for b in our_snake['body']]
    
    board_width = prev_state['board']['width']
    board_height = prev_state['board']['height']
    
    # Check for starvation first
    if our_snake['health'] == 0:
        return 'starvation'
    
    # Check for wall collision
    if our_head[0] < 0 or our_head[0] >= board_width or our_head[1] < 0 or our_head[1] >= board_height:
        return 'wall_collision'
    
    # Check for self collision (head appears multiple times in body)
    if our_body.count(our_head) > 1:
        return 'self_collision'
    
    # Check for body collision with other snake
    for sid, snake in prev_snakes.items():
        if sid != our_id:
            other_body = [(b['x'], b['y']) for b in snake['body']]
            if our_head in other_body:
                return 'body_collision_other'
    
    # Check for head-to-head collision
    for sid, snake in prev_snakes.items():
        if sid != our_id:
            other_head = (snake['head']['x'], snake['head']['y'])
            if our_head == other_head:
                if len(our_snake['body']) <= len(snake['body']):
                    return 'head_collision_lost'
                else:
                    return 'head_collision_won'
    
    return 'unknown'

# Analyze all games
round_dir = '/logs/rounds/13'
results = defaultdict(int)
death_causes = defaultdict(int)

game_files = [f for f in os.listdir(round_dir) if f.startswith('sim_') and f.endswith('.jsonl')]

for game_file in sorted(game_files, key=lambda x: int(x.split('_')[1].split('.')[0]))[:200]:
    filepath = os.path.join(round_dir, game_file)
    
    result = analyze_game(filepath)
    if result:
        results[result] += 1
    
    if result == 'we_lost':
        death_cause = analyze_death_cause(filepath)
        if death_cause:
            death_causes[death_cause] += 1

print("=== Round 13 Analysis (First 200 Games) ===\n")
print("Game Results:")
for winner, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
    pct = 100.0 * count / sum(results.values())
    print(f"  {winner}: {count} ({pct:.1f}%)")

print("\nDeath Causes (when we lost):")
for cause, count in sorted(death_causes.items(), key=lambda x: x[1], reverse=True):
    pct = 100.0 * count / sum(death_causes.values()) if death_causes else 0
    print(f"  {cause}: {count} ({pct:.1f}%)")

print(f"\nTotal games analyzed: {len(game_files[:200])}")
