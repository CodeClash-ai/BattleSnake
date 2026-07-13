import json
from main import move

# Let's see turn 205
with open("/logs/rounds/0/sim_0.jsonl", "r") as f:
    lines = f.readlines()

print("Turn 205:")
turn_data = json.loads(lines[-4])
print("My head:", turn_data["you"]["head"])
# Let's call move on turn 205 game_state to see why it went to (8, 4) instead of somewhere else
print("Move chosen:", move(turn_data))
# Let's inspect options and scores for Turn 205
board = turn_data["board"]
width, height = board["width"], board["height"]
you = turn_data["you"]
my_head = (you["body"][0]["x"], you["body"][0]["y"])

obstacles = set()
opp_heads = []
for snake in board["snakes"]:
    for seg in snake["body"]:
        obstacles.add((seg["x"], seg["y"]))
    if snake["id"] != you["id"]:
        opp_head = snake["body"][0]
        opp_heads.append((opp_head["x"], opp_head["y"]))

directions = {
    "left": (-1, 0),
    "right": (1, 0),
    "down": (0, -1),
    "up": (0, 1)
}

print("Options from", my_head)
for d, (dx, dy) in directions.items():
    nx, ny = my_head[0] + dx, my_head[1] + dy
    np = (nx, ny)
    is_obstacle = np in obstacles
    print(f"  {d}: {np}, is_obstacle: {is_obstacle}")
    if not is_obstacle:
        from main import _time_aware_flood_fill, _voronoi_territory, _manhattan
        space = _time_aware_flood_fill(np, width, height, board["snakes"])
        voronoi_space = _voronoi_territory(np, opp_heads, width, height, obstacles)
        print(f"    space: {space}, voronoi: {voronoi_space}")
