import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

state_109 = json.loads(lines[110]) # Turn 109 is at index 110 (turn 0 is index 1 or so)
# Let's check game_state info:
print("Turn:", state_109["turn"])
# We are gemini-3-5-flash.
# Let's set the "you" snake to gemini-3-5-flash to simulate correctly:
gemini = next(s for s in state_109["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
state_109["you"] = gemini

# Now get the move
print("Move chosen:", main.move(state_109))
