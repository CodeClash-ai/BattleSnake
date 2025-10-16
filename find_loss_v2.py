import json
import os
import sys

log_dir = '/logs/rounds/9/'

for filename in os.listdir(log_dir):
    if filename.startswith('sim_') and filename.endswith('.jsonl'):
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                continue

            last_line = lines[-1]
            second_last_line = lines[-2]

            try:
                game_result = json.loads(last_line)
                if game_result.get('winnerName') != 'gemini-2.5-pro':
                    print(f"Found a loss in {filename}")
                    final_state = json.loads(second_last_line)
                    snakes = final_state.get('board', {}).get('snakes', [])
                    for snake in snakes:
                        if snake.get('name') == 'gemini-2.5-pro' and 'death' in snake:
                             print(f"Cause: {snake['death']['cause']}")
                             sys.exit(0) # exit after finding the first loss.

                    # If our snake is not in the final state, it was eliminated.
                    # We need to find the turn it was eliminated.
                    # This is a bit more complex, let's just find a game where it died first.
                    # If the above loop does not find the cause, we can check the 'eliminated' field
                    # in the final state of the game, if available in any of the last few lines.
                    # For now, let's assume the snake is in the final state if it died on the last turn.
                    
                    # Let's search backwards from the second to last line for our snake's elimination
                    for i in range(len(lines) - 2, -1, -1):
                        try:
                            state = json.loads(lines[i])
                            if 'board' in state:
                                eliminated_snakes = [s for s in state['board']['snakes'] if s.get('name') == 'gemini-2.5-pro']
                                if not eliminated_snakes:
                                    # our snake is not in the board, so it was eliminated in a previous turn
                                    # let's find the elimination reason in the next turn
                                    next_state = json.loads(lines[i+1])
                                    if 'board' in next_state:
                                        prev_snakes = {s['id']: s for s in state['board']['snakes']}
                                        curr_snakes = {s['id']: s for s in next_state['board']['snakes']}
                                        eliminated_ids = set(prev_snakes.keys()) - set(curr_snakes.keys())
                                        for snake_id in eliminated_ids:
                                            if prev_snakes[snake_id]['name'] == 'gemini-2.5-pro':
                                                # This is complex, let's try a simpler approach first
                                                # The previous script was looking for 'eliminated' key, let's try that.
                                                pass

                        except json.JSONDecodeError:
                            continue


            except (json.JSONDecodeError, IndexError):
                continue
# A fallback to the old script logic, in case my new logic is flawed.
for filename in os.listdir(log_dir):
    if filename.startswith('sim_') and filename.endswith('.jsonl'):
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if not lines:
                continue
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    if 'eliminated' in data: # this key might not exist
                        for snake in data['eliminated']:
                            if snake['name'] == 'gemini-2.5-pro':
                                print(f"Found a loss in {filename} (using fallback method)")
                                print(f"Cause: {snake.get('cause', 'Unknown')}")
                                sys.exit(0)
                    if 'board' in data:
                        for snake in data['board']['snakes']:
                            if snake.get('name') == 'gemini-2.5-pro' and 'death' in snake and snake['death']:
                                print(f"Found a loss in {filename} (using death field)")
                                print(f"Cause: {snake['death']['cause']}")
                                sys.exit(0)

                except (json.JSONDecodeError, KeyError):
                    continue
