import json

filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find turn 41 and 42
for i, line in enumerate(lines[1:-1], 1):
    state = json.loads(line)
    if state['turn'] == 41:
        print("=== Turn 41 (before death) ===")
        print(f"Board: {state['board']['width']}x{state['board']['height']}")
        
        our_snake = None
        opp_snake = None
        for s in state['board']['snakes']:
            if s['name'] == 'claude-sonnet-4-5-20250929':
                our_snake = s
            else:
                opp_snake = s
        
        print(f"\nOur snake:")
        print(f"  Head: {our_snake['head']}")
        print(f"  Body: {our_snake['body'][:5]}...")
        print(f"  Length: {our_snake['length']}, Health: {our_snake['health']}")
        
        print(f"\nOpponent snake:")
        print(f"  Head: {opp_snake['head']}")
        print(f"  Body: {opp_snake['body'][:5]}...")
        print(f"  Length: {opp_snake['length']}, Health: {opp_snake['health']}")
        
        print(f"\nFood: {state['board']['food']}")
        
        # Check what moves are available from (7,6)
        our_head = (our_snake['head']['x'], our_snake['head']['y'])
        print(f"\nPossible moves from {our_head}:")
        moves = [
            ('up', (our_head[0], our_head[1] + 1)),
            ('down', (our_head[0], our_head[1] - 1)),
            ('left', (our_head[0] - 1, our_head[1])),
            ('right', (our_head[0] + 1, our_head[1]))
        ]
        
        # Build occupied positions
        occupied = set()
        for s in state['board']['snakes']:
            for b in s['body'][:-1]:  # Exclude tail (it will move)
                occupied.add((b['x'], b['y']))
        
        board_w = state['board']['width']
        board_h = state['board']['height']
        
        for direction, pos in moves:
            safe = True
            reason = ""
            
            if pos[0] < 0 or pos[0] >= board_w or pos[1] < 0 or pos[1] >= board_h:
                safe = False
                reason = "wall"
            elif pos in occupied:
                safe = False
                reason = "body collision"
            
            print(f"  {direction} -> {pos}: {'SAFE' if safe else f'UNSAFE ({reason})'}")
    
    elif state['turn'] == 42:
        print("\n=== Turn 42 (after death) ===")
        print(f"Snakes alive: {len(state['board']['snakes'])}")
        for s in state['board']['snakes']:
            print(f"  {s['name']}: head={s['head']}")
