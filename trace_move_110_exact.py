import json
import main

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

state_110 = json.loads(lines[111]) # Turn 110
print("Turn:", state_110["turn"])
gemini = next(s for s in state_110["board"]["snakes"] if s["name"] == "gemini-3-5-flash")
state_110["you"] = gemini

print("Move chosen:", main.move(state_110))
