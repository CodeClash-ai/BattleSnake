import json

# Look at a game where we lost
filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Get summary
summary = json.loads(lines[-1])
print(f"Winner: {summary['winnerName']}")
print(f"Is Draw: {summary['isDraw']}")

# Get final game state (second to last line)
final_state = json.loads(lines[-2])
print(f"\nFinal Turn: {final_state['turn']}")
print(f"Snakes alive: {len(final_state['board']['snakes'])}")

for snake in final_state['board']['snakes']:
    print(f"  - {snake['name']}: length={snake['length']}, health={snake['health']}")

# Look at the last few turns to see what happened
print("\n=== Last 5 turns ===")
for line in lines[-7:-1]:  # Skip metadata and summary
    state = json.loads(line)
    turn = state['turn']
    snakes = state['board']['snakes']
    
    our_snake = None
    opp_snake = None
    for s in snakes:
        if s['name'] == 'claude-sonnet-4-5-20250929':
            our_snake = s
        else:
            opp_snake = s
    
    print(f"\nTurn {turn}:")
    if our_snake:
        print(f"  Us: length={our_snake['length']}, health={our_snake['health']}, head={our_snake['head']}")
    else:
        print(f"  Us: DEAD")
    
    if opp_snake:
        print(f"  Opp: length={opp_snake['length']}, health={opp_snake['health']}, head={opp_snake['head']}")
    else:
        print(f"  Opp: DEAD")
