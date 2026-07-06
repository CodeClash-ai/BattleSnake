import json
import main

# Let's see what gemini-3-5-flash was doing when health was low.
# Food list on turn 107:
filepath = "/logs/rounds/1/sim_113.jsonl"
turns = []
with open(filepath) as f:
    for line in f:
        if line.strip():
            turns.append(json.loads(line))

turn_107 = next(turn for turn in turns if turn.get("turn") == 107)
print("Food positions on turn 107:", turn_107["board"]["food"])
# Let's run move for gemini-3-5-flash on turn 107
print("Result of move on turn 107:", main.move(turn_107))
