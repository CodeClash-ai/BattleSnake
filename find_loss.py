import json
import os

log_dir = '/logs/rounds/9/'

for filename in os.listdir(log_dir):
    if filename.startswith('sim_') and filename.endswith('.jsonl'):
        filepath = os.path.join(log_dir, filename)
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if not lines:
                continue
            last_line = lines[-1]
            try:
                game_end_state = json.loads(last_line)
                if 'eliminated' in game_end_state and game_end_state['eliminated']:
                    for snake in game_end_state['eliminated']:
                        if snake['name'] == 'gemini-2.5-pro':
                            print(f"Found a loss in {filename}")
                            print(f"Cause: {snake.get('cause', 'Unknown')}")
                            # Exit after finding the first loss to keep the output concise
                            exit(0)
            except json.JSONDecodeError:
                continue
