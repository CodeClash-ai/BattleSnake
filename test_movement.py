import json
from main import move

# Let's mock Turn 206 and call move to see what choices it evaluated and why it chose 'up' (which moves to 8, 5, colliding with its own body segment at 8, 5)
game_state = {
  "turn": 206,
  "board": {
    "height": 11,
    "width": 11,
    "snakes": [
      {
        "id": "99bb7d5a-bd16-43e2-bfc4-25353cc7c46f",
        "name": "gemini-3-5-flash",
        "health": 93,
        "body": [
          {"x": 8, "y": 4},
          {"x": 8, "y": 5},
          {"x": 8, "y": 6},
          {"x": 8, "y": 7},
          {"x": 9, "y": 7},
          {"x": 10, "y": 7},
          {"x": 10, "y": 6},
          {"x": 9, "y": 6},
          {"x": 9, "y": 5},
          {"x": 9, "y": 4},
          {"x": 10, "y": 4},
          {"x": 10, "y": 3},
          {"x": 9, "y": 3},
          {"x": 8, "y": 3},
          {"x": 7, "y": 3},
          {"x": 6, "y": 3},
          {"x": 5, "y": 3},
          {"x": 4, "y": 3},
          {"x": 3, "y": 3},
          {"x": 2, "y": 3},
          {"x": 1, "y": 3},
          {"x": 0, "y": 3},
          {"x": 0, "y": 4},
          {"x": 0, "y": 5},
          {"x": 0, "y": 6},
          {"x": 0, "y": 7},
          {"x": 0, "y": 8},
          {"x": 0, "y": 9},
          {"x": 0, "y": 10},
          {"x": 1, "y": 10},
          {"x": 2, "y": 10},
          {"x": 3, "y": 10},
          {"x": 4, "y": 10}
        ],
        "head": {"x": 8, "y": 4},
        "length": 33
      },
      {
        "id": "a20a37c2-d466-4b26-af18-885eca38e8ca",
        "name": "MorganConrad__tantilla",
        "health": 68,
        "body": [
          {"x": 6, "y": 4},
          {"x": 7, "y": 4},
          {"x": 7, "y": 5},
          {"x": 6, "y": 5},
          {"x": 6, "y": 6}
        ],
        "head": {"x": 6, "y": 4},
        "length": 5
      }
    ],
    "food": [
      {"x": 10, "y": 2},
      {"x": 5, "y": 2},
      {"x": 1, "y": 5}
    ]
  },
  "you": {
    "id": "99bb7d5a-bd16-43e2-bfc4-25353cc7c46f",
    "name": "gemini-3-5-flash",
    "health": 93,
    "body": [
      {"x": 8, "y": 4},
      {"x": 8, "y": 5},
      {"x": 8, "y": 6},
      {"x": 8, "y": 7},
      {"x": 9, "y": 7},
      {"x": 10, "y": 7},
      {"x": 10, "y": 6},
      {"x": 9, "y": 6},
      {"x": 9, "y": 5},
      {"x": 9, "y": 4},
      {"x": 10, "y": 4},
      {"x": 10, "y": 3},
      {"x": 9, "y": 3},
      {"x": 8, "y": 3},
      {"x": 7, "y": 3},
      {"x": 6, "y": 3},
      {"x": 5, "y": 3},
      {"x": 4, "y": 3},
      {"x": 3, "y": 3},
      {"x": 2, "y": 3},
      {"x": 1, "y": 3},
      {"x": 0, "y": 3},
      {"x": 0, "y": 4},
      {"x": 0, "y": 5},
      {"x": 0, "y": 6},
      {"x": 0, "y": 7},
      {"x": 0, "y": 8},
      {"x": 0, "y": 9},
      {"x": 0, "y": 10},
      {"x": 1, "y": 10},
      {"x": 2, "y": 10},
      {"x": 3, "y": 10},
      {"x": 4, "y": 10}
    ],
    "head": {"x": 8, "y": 4},
    "length": 33
  }
}

print(move(game_state))

# Let's inspect the options and obstacles logic on turn 206
board = game_state["board"]
obstacles = set()
for snake in board["snakes"]:
    for seg in snake["body"]:
        obstacles.add((seg["x"], seg["y"]))

print("My head:", (8, 4))
print("Obstacles contains (7, 4):", (7, 4) in obstacles)
print("Obstacles contains (9, 4):", (9, 4) in obstacles)
print("Obstacles contains (8, 3):", (8, 3) in obstacles)
print("Obstacles contains (8, 5):", (8, 5) in obstacles)

# Let's see directions
directions = {
    "left": (-1, 0),
    "right": (1, 0),
    "down": (0, -1),
    "up": (0, 1)
}
possible_moves = []
for d, (dx, dy) in directions.items():
    nx, ny = 8 + dx, 4 + dy
    if 0 <= nx < 11 and 0 <= ny < 11:
        np = (nx, ny)
        if np not in obstacles:
            possible_moves.append((d, np))
print("Possible moves inside code logic:", possible_moves)

# Let's inspect the exact positions of obstacles around our head
# We know the snake's tail moves, so let's see which occupied segments will vacate.
# Specifically, we have body segments at (8,3), (9,4), (8,5), (7,4).
# Let's check where they are in the body list:
body = game_state["you"]["body"]
for i, seg in enumerate(body):
    pos = (seg["x"], seg["y"])
    if pos in [(8,3), (9,4), (8,5), (7,4)]:
        print(f"Our segment {pos} is at index {i} in our body (length {len(body)}). Steps to vacate: {len(body) - i}")

opp_body = board["snakes"][1]["body"]
for i, seg in enumerate(opp_body):
    pos = (seg["x"], seg["y"])
    if pos in [(8,3), (9,4), (8,5), (7,4)]:
        print(f"Opponent segment {pos} is at index {i} in opponent body (length {len(opp_body)}). Steps to vacate: {len(opp_body) - i}")
