import json

filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find turn 41
for line in lines[1:-1]:
    state = json.loads(line)
    if state['turn'] == 41:
        print("=== Turn 41 - All occupied positions ===")
        
        occupied = set()
        for s in state['board']['snakes']:
            print(f"\n{s['name']} body:")
            for i, b in enumerate(s['body']):
                pos = (b['x'], b['y'])
                occupied.add(pos)
                print(f"  {i}: {pos}")
        
        print(f"\nIs (6,6) occupied? {(6,6) in occupied}")
        print(f"Is (6,7) occupied? {(6,7) in occupied}")
        
        # Check all positions around (7,6)
        print("\nPositions around (7,6):")
        for dx, dy, name in [(0,1,'up'), (0,-1,'down'), (-1,0,'left'), (1,0,'right')]:
            pos = (7+dx, 6+dy)
            print(f"  {name} {pos}: {'OCCUPIED' if pos in occupied else 'FREE'}")
        
        break
