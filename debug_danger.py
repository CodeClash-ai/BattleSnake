import json
from main import move

# Let's inspect some of the round 2 failures
# and see why it chose a dangerous option or got eliminated.
# We will read Round 2, sim_111.jsonl or sim_10.jsonl or others.

with open("/logs/rounds/2/sim_10.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

# Find last few turns
for turn_idx in range(len(lines)-5, len(lines)):
    data = lines[turn_idx]
    if "turn" in data and data["turn"] is not None:
        print(f"Turn {data['turn']}, snakes left: {[s['name'] for s in data['board']['snakes']]}")
        # if gemini is in it, let's see what it returned
        gemini_snake = next((s for s in data['board']['snakes'] if "gemini" in s["name"]), None)
        if gemini_snake:
            print(f"  Gemini head: {gemini_snake['head']}, length: {gemini_snake['length']}, health: {gemini_snake['health']}")
            # let's run move on this game_state if we set "you" to gemini
            data["you"] = gemini_snake
            print(f"  Gemini move returned: {move(data)}")
