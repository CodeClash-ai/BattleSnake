import json

file_path = "/logs/rounds/0/sim_128.jsonl"
with open(file_path, "r") as f:
    lines = f.readlines()

# Turn 110 state:
# gemini-3-5-flash head: (0, 0), body: [(0,0), (1,0), (1,1), (0,1), (0,2), (0,3), (0,4)]
# directions from (0,0):
# up: (0,1) -> occupied by body segment 3.
# down: (0,-1) -> out of bounds.
# left: (-1,0) -> out of bounds.
# right: (1,0) -> occupied by body segment 1.
# So all choices are out-of-bounds or self-collision!
# Let's see what the move function returned at Turn 110, or what options it had.
# Turn 111 shows gemini-3-5-flash head went to (0,1), which caused a self-collision (since (0,1) was occupied by index 3 of body).
# Wait, let's see why it went to (0,0) in Turn 110.
# At Turn 109: head was at (1,0). Body: [(1,0), (1,1), (0,1), (0,2), (0,3), (0,4), (0,5)]
# From (1,0):
# up: (1,1) -> occupied by body segment 1
# down: (1,-1) -> out of bounds
# left: (0,0) -> empty!
# right: (2,0) -> empty!
# Wait! At Turn 109, we moved left to (0,0) instead of right to (2,0).
# Let's see if right (2,0) was blocked or why left (0,0) was chosen.
# Let's inspect the game board at Turn 109!
# Board is 11x11.
# ccSnake2018_ccsnake head was at (3,0).
# If we moved to (2,0), that would put us 1 step away from ccSnake2018_ccsnake's head (3,0).
# Since they have length 16 and we have length 7, (2,0) was marked as "is_dangerous" (head-to-head collision risk).
# Wait, let's see what else.
# Let's trace why we chose (0,0) over other cells or what the options were.
