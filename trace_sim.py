import json
import main

path = '/logs/rounds/1/sim_113.jsonl'
with open(path) as file:
    lines = [json.loads(line) for line in file if line.strip()]

# Turn 52 state
for i, line in enumerate(lines):
    if line.get('turn') == 52:
        game_state = line
        # The log file has you: ... but sometimes we need to make sure 'you' is gemini-3-5-flash
        # Let's override 'you' to be gemini-3-5-flash to trace correctly.
        for s in game_state['board']['snakes']:
            if s['name'] == 'gemini-3-5-flash':
                game_state['you'] = s
        
        print("Tracing turn 52:")
        result = main.move(game_state)
        print("Move chosen:", result)
        
        # Let's also print choices manually
        board = game_state["board"]
        width, height = board["width"], board["height"]
        head_seg = game_state["you"]["body"][0]
        head = (head_seg["x"], head_seg["y"])
        print("Head:", head)
        possible_moves = {
            "up": (head[0], head[1] + 1),
            "down": (head[0], head[1] - 1),
            "left": (head[0] - 1, head[1]),
            "right": (head[0] + 1, head[1])
        }
        print("Possible moves:", possible_moves)
        break
