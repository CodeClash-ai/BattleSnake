import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

state_108 = json.loads(lines[109]) # Turn 108
print("Turn:", state_108["turn"])
gemini = next(s for s in state_108["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
state_108["you"] = gemini

print("Move chosen:", main.move(state_108))
