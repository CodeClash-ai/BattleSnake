import json
import os

tie_games = []
for i in range(1000):
    filepath = f'/logs/rounds/3/sim_{i}.jsonl'
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if lines:
                # Check last line for game outcome
                for line in reversed(lines):
                    data = json.loads(line)
                    if 'game' in data and 'turn' in data:
                        # Check if both snakes are eliminated
                        snakes = data['board']['snakes']
                        if len(snakes) == 0:
                            tie_games.append(i)
                            print(f"Game {i}: Tie - Turn {data['turn']}, No snakes remaining")
                            break
                        elif len(snakes) == 2 and data['turn'] > 100:
                            # Both survived long game
                            print(f"Game {i}: Both survived - Turn {data['turn']}")
                        break

print(f"\nTotal tie games found: {len(tie_games)}")
