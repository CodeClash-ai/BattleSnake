import json

def analyze_game(filename):
    """Analyze a game in detail."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    print(f"Analyzing {filename}")
    print("=" * 80)
    
    for line in lines:
        data = json.loads(line)
        if 'board' not in data:
            continue
        
        turn = data['turn']
        board = data['board']
        snakes = board['snakes']
        food = board['food']
        
        our_snake = None
        opp_snake = None
        for snake in snakes:
            if snake['name'] == 'claude-sonnet-4-5-20250929':
                our_snake = snake
            else:
                opp_snake = snake
        
        if turn % 20 == 0 or turn < 10 or not our_snake or not opp_snake:
            print(f"\nTurn {turn}:")
            if our_snake:
                print(f"  Us: Health={our_snake['health']}, Length={our_snake['length']}, Head={our_snake['head']}")
            else:
                print(f"  Us: DEAD")
            if opp_snake:
                print(f"  Opp: Health={opp_snake['health']}, Length={opp_snake['length']}, Head={opp_snake['head']}")
            else:
                print(f"  Opp: DEAD")
            print(f"  Food: {len(food)} pieces at {food[:3]}")

analyze_game('/logs/rounds/4/sim_1.jsonl')
