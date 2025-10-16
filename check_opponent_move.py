import json

filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find turns 41 and 42
for i, line in enumerate(lines[1:-1], 1):
    state = json.loads(line)
    if state['turn'] == 41:
        print("=== Turn 41 ===")
        for s in state['board']['snakes']:
            print(f"{s['name']}: head at ({s['head']['x']}, {s['head']['y']})")
    
    if state['turn'] == 42:
        print("\n=== Turn 42 ===")
        for s in state['board']['snakes']:
            print(f"{s['name']}: head at ({s['head']['x']}, {s['head']['y']})")
        
        print("\n=== Movement analysis ===")
        prev_state = json.loads(lines[i-1])
        for s in state['board']['snakes']:
            for ps in prev_state['board']['snakes']:
                if s['id'] == ps['id']:
                    prev_head = (ps['head']['x'], ps['head']['y'])
                    curr_head = (s['head']['x'], s['head']['y'])
                    dx = curr_head[0] - prev_head[0]
                    dy = curr_head[1] - prev_head[1]
                    direction = ""
                    if dx == 1: direction = "right"
                    elif dx == -1: direction = "left"
                    elif dy == 1: direction = "up"
                    elif dy == -1: direction = "down"
                    print(f"{s['name']}: {prev_head} -> {curr_head} ({direction})")
