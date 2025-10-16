import json

filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find turn 41 and see what move we made
for i, line in enumerate(lines[1:-1], 1):
    state = json.loads(line)
    if state['turn'] == 42:
        print("=== Turn 42 (after our death) ===")
        
        # Check if we're in the snakes list
        our_snake = None
        opp_snake = None
        for s in state['board']['snakes']:
            if s['name'] == 'claude-sonnet-4-5-20250929':
                our_snake = s
            else:
                opp_snake = s
        
        if our_snake:
            print(f"We're still alive at: {our_snake['head']}")
        else:
            print("We died!")
        
        print(f"\nOpponent at: {opp_snake['head']}")
        print(f"Opponent body: {opp_snake['body'][:5]}")
        
        # Check turn 41 to see where we were
        prev_state = json.loads(lines[i-1])
        if prev_state['turn'] == 41:
            for s in prev_state['board']['snakes']:
                if s['name'] == 'claude-sonnet-4-5-20250929':
                    print(f"\nTurn 41 - Our head was at: {s['head']}")
                    print(f"Turn 41 - Our body: {s['body'][:5]}")
                else:
                    print(f"Turn 41 - Opp head was at: {s['head']}")
            
            # So we moved from (7,6) to where?
            # If we're dead, we must have collided
            # Let's check if (6,6) was safe
            print("\n=== Analyzing collision ===")
            print("We were at (7,6) and only safe move was left to (6,6)")
            print(f"Opponent was at (5,6) and moved to (5,5)")
            print("So we should have moved to (6,6) which was safe...")
            print("Unless we didn't move left?")
