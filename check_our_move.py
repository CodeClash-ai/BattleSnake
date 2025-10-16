import json

filepath = '/logs/rounds/13/sim_1.jsonl'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find turns 40, 41, 42
for i, line in enumerate(lines[1:-1], 1):
    state = json.loads(line)
    if state['turn'] in [40, 41, 42]:
        print(f"\n=== Turn {state['turn']} ===")
        
        our_snake = None
        opp_snake = None
        for s in state['board']['snakes']:
            if s['name'] == 'claude-sonnet-4-5-20250929':
                our_snake = s
            else:
                opp_snake = s
        
        if our_snake:
            print(f"Our head: {our_snake['head']}, body length: {our_snake['length']}")
            print(f"Our body: {our_snake['body']}")
        else:
            print("We are DEAD")
        
        if opp_snake:
            print(f"Opp head: {opp_snake['head']}, body length: {opp_snake['length']}")

# Let's trace our path
print("\n=== Tracing our movement ===")
prev_head = None
for i, line in enumerate(lines[1:-1], 1):
    state = json.loads(line)
    if state['turn'] >= 38 and state['turn'] <= 42:
        for s in state['board']['snakes']:
            if s['name'] == 'claude-sonnet-4-5-20250929':
                curr_head = (s['head']['x'], s['head']['y'])
                if prev_head:
                    dx = curr_head[0] - prev_head[0]
                    dy = curr_head[1] - prev_head[1]
                    direction = ""
                    if dx == 1: direction = "right"
                    elif dx == -1: direction = "left"
                    elif dy == 1: direction = "up"
                    elif dy == -1: direction = "down"
                    print(f"Turn {state['turn']}: {prev_head} -> {curr_head} ({direction})")
                prev_head = curr_head
                break
        else:
            if prev_head:
                print(f"Turn {state['turn']}: DIED (was at {prev_head})")
            break
