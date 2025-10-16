import json
import os

def check_game_outcome(filename):
    """Check if we won or lost this game."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    last_state = None
    for line in lines:
        data = json.loads(line)
        if 'board' in data:
            last_state = data
    
    if not last_state:
        return None
    
    snakes = last_state['board']['snakes']
    our_alive = False
    opp_alive = False
    
    for snake in snakes:
        if snake['name'] == 'claude-sonnet-4-5-20250929':
            our_alive = True
        else:
            opp_alive = True
    
    if our_alive and not opp_alive:
        return 'WIN'
    elif not our_alive and opp_alive:
        return 'LOSS'
    elif not our_alive and not opp_alive:
        return 'TIE'
    else:
        return 'BOTH_ALIVE'

# Find first 10 losses
losses = []
for i in range(100):
    filename = f'/logs/rounds/4/sim_{i}.jsonl'
    if os.path.exists(filename):
        outcome = check_game_outcome(filename)
        if outcome == 'LOSS':
            losses.append(i)
            if len(losses) >= 10:
                break

print("First 10 loss game numbers:", losses)
