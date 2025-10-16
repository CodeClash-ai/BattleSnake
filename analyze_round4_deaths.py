import json
import sys

def analyze_game(filename):
    """Analyze a single game file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    our_snake_id = None
    last_turn = None
    
    for line in lines:
        data = json.loads(line)
        if 'game' not in data:
            continue
            
        turn_data = data
        board = turn_data.get('board', {})
        snakes = board.get('snakes', [])
        
        # Find our snake
        our_snake = None
        opponent_snake = None
        for snake in snakes:
            if snake['name'] == 'claude-sonnet-4-5-20250929':
                our_snake = snake
                our_snake_id = snake['id']
            else:
                opponent_snake = snake
        
        if our_snake:
            last_turn = {
                'turn': turn_data['turn'],
                'our_health': our_snake['health'],
                'our_length': our_snake['length'],
                'opp_health': opponent_snake['health'] if opponent_snake else 0,
                'opp_length': opponent_snake['length'] if opponent_snake else 0,
                'food_count': len(board.get('food', []))
            }
    
    return last_turn

# Analyze first 20 games
for i in range(20):
    filename = f'/logs/rounds/4/sim_{i}.jsonl'
    result = analyze_game(filename)
    if result:
        print(f"Game {i}: Turn {result['turn']}, Our Health={result['our_health']}, Our Len={result['our_length']}, Opp Health={result['opp_health']}, Opp Len={result['opp_length']}, Food={result['food_count']}")
