import json
import sys

def analyze_game(filepath):
    """Analyze a single game file."""
    with open(filepath, 'r') as f:
        lines = [json.loads(line) for line in f]
    
    if len(lines) == 0:
        return None
    
    last_state = lines[-1]
    
    # Find our snake and opponent
    our_id = None
    for snake in last_state['board']['snakes']:
        if snake['id'] == last_state['you']['id']:
            our_id = snake['id']
            break
    
    # Check if we're alive at the end
    our_snake = None
    opp_snake = None
    for snake in last_state['board']['snakes']:
        if snake['id'] == our_id:
            our_snake = snake
        else:
            opp_snake = snake
    
    result = {
        'turns': len(lines),
        'we_survived': our_snake is not None,
        'opp_survived': opp_snake is not None,
        'our_final_length': our_snake['length'] if our_snake else 0,
        'opp_final_length': opp_snake['length'] if opp_snake else 0,
    }
    
    # If we died, find when and why
    if not result['we_survived']:
        for i in range(len(lines) - 1, -1, -1):
            state = lines[i]
            found_us = False
            for snake in state['board']['snakes']:
                if snake['id'] == our_id:
                    found_us = True
                    result['death_turn'] = i + 1
                    result['death_health'] = snake['health']
                    result['death_length'] = snake['length']
                    break
            if found_us:
                break
    
    return result

if __name__ == '__main__':
    round_num = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    
    import os
    import glob
    
    loss_files = []
    
    # Read results to find losses
    results_file = f'/logs/rounds/{round_num}/results.json'
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    losses = []
    for sim_id, result in results.items():
        if result['winner'] != 'you':
            losses.append(sim_id)
    
    print(f"Analyzing {len(losses)} losses from round {round_num}...")
    
    death_reasons = {
        'starvation': 0,
        'collision': 0,
        'unknown': 0
    }
    
    early_deaths = []  # Deaths before turn 50
    late_deaths = []   # Deaths after turn 100
    
    for sim_id in losses[:20]:  # Analyze first 20 losses
        filepath = f'/logs/rounds/{round_num}/{sim_id}.jsonl'
        result = analyze_game(filepath)
        
        if result and not result['we_survived']:
            if result.get('death_health', 100) == 0:
                death_reasons['starvation'] += 1
            else:
                death_reasons['collision'] += 1
            
            if result.get('death_turn', 0) < 50:
                early_deaths.append((sim_id, result))
            elif result.get('death_turn', 0) > 100:
                late_deaths.append((sim_id, result))
    
    print(f"\nDeath reasons (first 20 losses):")
    print(f"  Starvation: {death_reasons['starvation']}")
    print(f"  Collision: {death_reasons['collision']}")
    
    print(f"\nEarly deaths (< turn 50): {len(early_deaths)}")
    for sim_id, result in early_deaths[:5]:
        print(f"  {sim_id}: Turn {result.get('death_turn')}, Health {result.get('death_health')}, Length {result.get('death_length')}")
    
    print(f"\nLate deaths (> turn 100): {len(late_deaths)}")
    for sim_id, result in late_deaths[:5]:
        print(f"  {sim_id}: Turn {result.get('death_turn')}, Health {result.get('death_health')}, Length {result.get('death_length')}")
