import json

with open("/logs/rounds/0/sim_123.jsonl", "r") as f:
    lines = [json.loads(line) for line in f.readlines() if line.strip()]

# In Battlesnake API, each line starting from index 0 is a turn, but we don't have the API calls our snake returned directly unless we check our code.
# Let's see if we hit a wall in sim_123 on Turn 96:
# On Turn 96, our head was at (0, 10).
# From (0, 10), possible moves are:
# (0, 11) -> Out of bounds (since board height is 11, indices 0..10. Wait, height=11, so y=11 is out of bounds, y=10 is max).
# (-1, 10) -> Out of bounds.
# (1, 10) -> obstacle (our own body segment at (1, 10)).
# (0, 9) -> obstacle (our own body segment at (0, 9)).
# Ah! We were completely boxed in because our head was at (0, 10) and our body was at (1, 10) and (0, 9)!
# Yes, on Turn 96, our body was:
# [{'x': 0, 'y': 10}, {'x': 1, 'y': 10}, {'x': 2, 'y': 10}, {'x': 3, 'y': 10}, {'x': 3, 'y': 9}, {'x': 2, 'y': 9}, {'x': 1, 'y': 9}, {'x': 0, 'y': 9}, ...]
# So we moved to (0, 10) which had NO escape! Why did we move to (0, 10)?
# Let's check Turn 95:
# Head was at (1, 10).
# From (1, 10), our safe moves were:
# (0, 10) -> free
# (2, 10) -> occupied by body segment {'x': 2, 'y': 10}
# (1, 9) -> occupied by body segment {'x': 1, 'y': 9}
# (1, 11) -> Out of bounds.
# So from (1, 10), the ONLY available move was (0, 10)!
# Why did we go to (1, 10) on Turn 94?
# On Turn 94, head was at (2, 10).
# Body was:
# [{'x': 2, 'y': 10}, {'x': 3, 'y': 10}, {'x': 3, 'y': 9}, {'x': 2, 'y': 9}, {'x': 1, 'y': 9}, {'x': 0, 'y': 9}, {'x': 0, 'y': 8}, {'x': 1, 'y': 8}, {'x': 2, 'y': 8}, {'x': 3, 'y': 8}, {'x': 4, 'y': 8}, {'x': 4, 'y': 9}]
# From (2, 10), options:
# (1, 10) -> free
# (3, 10) -> occupied
# (2, 9) -> occupied
# (2, 11) -> out of bounds
# So we were forced to go to (1, 10) then (0, 10)!
# Wait, why did we go to (2, 10) on Turn 93?
# Let's look at Turn 93 body or write a script to look at Turn 90 to 95.
