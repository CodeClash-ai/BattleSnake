import json
import os
from collections import defaultdict

def analyze_game(filepath):
    """Analyze a single game log"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return None
    
    # Get final state
    final_state = json.loads(lines[-1])
    
    # Determine winner
    snakes = final_state['board']['snakes']
    if len(snakes) == 0:
        return {'winner': 'tie', 'reason': 'all_died'}
    elif len(snakes) == 1:
        winner = snakes[0]['name']
        return {'winner': winner, 'reason': 'last_alive'}
    else:
        # Game ended with multiple snakes alive (shouldn't happen normally)
        return {'winner': 'unknown', 'reason': 'multiple_alive'}

def analyze_death_cause(filepath, our_name='claude-sonnet-4-5-20250929'):
    """Analyze how our snake died"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    our_snake = None
    prev_state = None
    
    for line in lines:
        state = json.loads(line)
        snakes = {s['id']: s for s in state['board']['snakes']}
        
        # Find our snake
        our_id = None
        for sid, snake in snakes.items():
            if snake['name'] == our_name:
                our_id = sid
                our_snake = snake
                break
        
        if our_id and prev_state:
            # Check if we just died
            prev_snakes = {s['id']: s for s in prev_state['board']['snakes']}
            if our_id in prev_snakes and our_id not in snakes:
                # We died this turn
                return analyze_death_reason(prev_state, state, our_id, our_name)
        
        prev_state = state
    
    return None

def analyze_death_reason(prev_state, curr_state, our_id, our_name):
    """Determine why we died"""
    prev_snakes = {s['id']: s for s in prev_state['board']['snakes']}
    our_snake = prev_snakes[our_id]
    our_head = tuple(our_snake['head'].values())
    
    # Check for wall collision
    board_width = prev_state['board']['width']
    board_height = prev_state['board']['height']
    if our_head[0] < 0 or our_head[0] >= board_width or our_head[1] < 0 or our_head[1] >= board_height:
        return 'wall_collision'
    
    # Check for self collision
    our_body = [tuple(b.values()) for b in our_snake['body']]
    if our_body.count(our_head) > 1:
        return 'self_collision'
    
    # Check for body collision with other snake
    for sid, snake in prev_snakes.items():
        if sid != our_id:
            other_body = [tuple(b.values()) for b in snake['body']]
            if our_head in other_body:
                return 'body_collision_other'
    
    # Check for head-to-head collision
    for sid, snake in prev_snakes.items():
        if sid != our_id:
            other_head = tuple(snake['head'].values())
            if our_head == other_head:
                if len(our_snake['body']) <= len(snake['body']):
                    return 'head_collision_lost'
                else:
                    return 'head_collision_won'
    
    # Check for starvation
    if our_snake['health'] == 0:
        return 'starvation'
    
    return 'unknown'

# Analyze all games
round_dir = '/logs/rounds/13'
results = defaultdict(int)
death_causes = defaultdict(int)

game_files = [f for f in os.listdir(round_dir) if f.startswith('sim_') and f.endswith('.jsonl')]

for game_file in sorted(game_files, key=lambda x: int(x.split('_')[1].split('.')[0]))[:100]:  # First 100 games
    filepath = os.path.join(round_dir, game_file)
    
    result = analyze_game(filepath)
    if result:
        results[result['winner']] += 1
    
    death_cause = analyze_death_cause(filepath)
    if death_cause:
        death_causes[death_cause] += 1

print("=== Round 13 Analysis (First 100 Games) ===\n")
print("Game Results:")
for winner, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
    print(f"  {winner}: {count}")

print("\nDeath Causes (when we lost):")
for cause, count in sorted(death_causes.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cause}: {count}")

print(f"\nTotal games analyzed: {len(game_files[:100])}")
