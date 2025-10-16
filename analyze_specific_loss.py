import json

game_file = "/logs/rounds/7/sim_1.jsonl"
our_name = "claude-sonnet-4-5-20250929"

with open(game_file, 'r') as f:
    lines = f.readlines()

# Find death turn
for j in range(len(lines)-2, -1, -1):
    state = json.loads(lines[j])
    if 'board' not in state:
        continue
        
    snakes = state['board']['snakes']
    our_snake = [s for s in snakes if s['name'] == our_name]
    
    if not our_snake:
        death_turn = state['turn']
        print(f"We died on turn {death_turn}")
        
        # Show last 3 turns before death
        for k in range(max(0, j-3), j):
            prev_state = json.loads(lines[k])
            if 'board' not in prev_state:
                continue
            turn = prev_state['turn']
            board = prev_state['board']
            snakes = board['snakes']
            our = [s for s in snakes if s['name'] == our_name][0]
            
            print(f"\nTurn {turn}:")
            print(f"  Our head: {our['head']}, length: {our['length']}, health: {our['health']}")
            print(f"  Our body: {our['body'][:5]}...")
            print(f"  Food: {board['food']}")
            
            # Show board state
            width = board['width']
            height = board['height']
            grid = [['.' for _ in range(width)] for _ in range(height)]
            
            # Mark our body
            for i, pos in enumerate(our['body']):
                if i == 0:
                    grid[height-1-pos['y']][pos['x']] = 'H'
                else:
                    grid[height-1-pos['y']][pos['x']] = 'o'
            
            # Mark opponent
            opp = [s for s in snakes if s['name'] != our_name]
            if opp:
                for i, pos in enumerate(opp[0]['body']):
                    if i == 0:
                        grid[height-1-pos['y']][pos['x']] = 'E'
                    else:
                        grid[height-1-pos['y']][pos['x']] = 'e'
            
            # Mark food
            for food in board['food']:
                if grid[height-1-food['y']][food['x']] == '.':
                    grid[height-1-food['y']][food['x']] = 'F'
            
            print("  Board:")
            for row in grid:
                print("    " + ''.join(row))
        break
