import json

with open("/logs/rounds/0/sim_10.jsonl") as f:
    lines = [json.loads(line) for line in f if line.strip()]

board_lines = [line for line in lines if "board" in line]

# Let's find where gemini-3-5-flash was in line 169 and what moves were available
# Turn 169 details:
# Head was at (7, 10). Width, height = 11, 11
# Body elements of gemini:
# [{'x': 7, 'y': 10}, {'x': 7, 'y': 9}, {'x': 7, 'y': 8}, {'x': 7, 'y': 7}, {'x': 7, 'y': 6}, {'x': 7, 'y': 5}, {'x': 6, 'y': 5}, {'x': 6, 'y': 6}, {'x': 6, 'y': 7}, {'x': 6, 'y': 8}, {'x': 6, 'y': 9}, {'x': 6, 'y': 10}, {'x': 5, 'y': 10}, {'x': 5, 'y': 9}, {'x': 5, 'y': 8}, {'x': 5, 'y': 7}, {'x': 5, 'y': 6}, {'x': 5, 'y': 5}, {'x': 5, 'y': 4}, {'x': 4, 'y': 4}, {'x': 4, 'y': 5}, {'x': 4, 'y': 6}]
# The head was at (7, 10). Neighbors:
# - Up: (7, 11) -> Out of bounds
# - Down: (7, 9) -> occupied by self body
# - Right: (8, 10) -> occupied by opponent body [{'x': 8, 'y': 10}, ...]
# - Left: (6, 10) -> occupied by self body [{'x': 6, 'y': 10}, ...] but wait!
# Wait! In turn 170, gemini-3-5-flash is shown with head: {'x': 6, 'y': 10}.
# Wait! How could gemini-3-5-flash move to (6, 10) if (6, 10) was occupied by its own body?
# Ah! Let's check the body list in Turn 169.
# body[11] is {'x': 6, 'y': 10}.
# Yes, it is occupied by its own body! But wait, in standard battlesnake, you can't collide with your own body unless it's the tail and it's moving out? But body[11] is in the middle of the body, not the tail!
# Wait, let's see why gemini-3-5-flash died in Turn 170.
# In Turn 170, the board snakes list only has coreyja__amphibious-arthur! gemini-3-5-flash was eliminated!
# In the Turn 170 "you" section of the jsonl, it shows gemini-3-5-flash with head {'x': 6, 'y': 10}, but it's not in the board snakes list anymore! It was eliminated in Turn 170 because of its move in Turn 169!
# Yes! It moved to (6, 10) on Turn 169, which caused a body collision with itself or opponent, and was eliminated.
# Why did it choose to move to (6, 10) which was self-collision?
# Let's check other directions:
# Up: (7, 11) (out of bounds)
# Down: (7, 9) (body[1])
# Right: (8, 10) (opponent body)
# Left: (6, 10) (body[11])
# All 4 directions were blocked!
# If all 4 directions are blocked, it is guaranteed to die. But how did it get trapped like this? Let's trace back from turn 160.
