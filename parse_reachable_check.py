import json

# Let's inspect turn 138. Head was at (5, 5).
# Available non-colliding moves were up: (5, 6) and down: (5, 4).
# Why did it choose down: (5, 4)?
# Let's write a quick script simulating the get_reachable_area at turn 138.
with open("/logs/rounds/0/sim_104.jsonl") as f:
    lines = f.readlines()

data = json.loads(lines[139]) # Turn 138
board = data["board"]
width, height = board["width"], board["height"]
obstacle_positions = set()
for s in board["snakes"]:
    for seg in s["body"]:
        obstacle_positions.add((seg["x"], seg["y"]))

def get_reachable_area(start_pos):
    queue = [start_pos]
    visited = {start_pos}
    count = 0
    while queue:
        curr = queue.pop(0)
        count += 1
        if count > 30:  # Cap the BFS to keep it fast
            break
        for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
            nx, ny = curr[0] + dx, curr[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in obstacle_positions and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return count

print("Reachable from (5, 6) [up]:", get_reachable_area((5, 6)))
print("Reachable from (5, 4) [down]:", get_reachable_area((5, 4)))
