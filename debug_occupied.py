import main
from debug_turn import game_state

board = game_state["board"]
width, height = board["width"], board["height"]
my_snake = game_state["you"]
my_body = my_snake["body"]
head = (my_body[0]["x"], my_body[0]["y"])

occupied = set()
for snake in board.get("snakes", []):
    body = snake["body"]
    is_growing = snake["health"] == 100
    
    # Add all body segments except the tail (if it's not growing and length > 1)
    for i, seg in enumerate(body):
        if i == len(body) - 1 and not is_growing and len(body) > 1:
            continue
        occupied.add((seg["x"], seg["y"]))

print("Occupied cells:", sorted(list(occupied)))
print("Head:", head)

# What are the directions?
directions = {
    "up": (head[0], head[1] + 1),
    "down": (head[0], head[1] - 1),
    "left": (head[0] - 1, head[1]),
    "right": (head[0] + 1, head[1])
}
for d, pos in directions.items():
    in_bounds = (0 <= pos[0] < width and 0 <= pos[1] < height)
    is_occ = pos in occupied
    print(f"Dir: {d}, Pos: {pos}, In-bounds: {in_bounds}, Occupied: {is_occ}")
