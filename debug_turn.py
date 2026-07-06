import json

# Let's inspect the game state at Turn 122 in sim_135
# Head of gemini-3-5-flash was at (10, 4)
# Bob's head was at (10, 6).
# Bob moved to (9, 6) in Turn 123.
# Our snake died. Did we make an invalid/out of bounds move or crash?
# Let's write a quick script to feed Turn 122 state into main's move function.

import main

game_state = {
  "game": {"id": "test"},
  "turn": 122,
  "board": {
    "height": 11,
    "width": 11,
    "snakes": [
      {
        "id": "b05e3488-1acc-4ecb-ba9d-33424d799be6",
        "name": "coreyja_bombastic-bob",
        "health": 95,
        "body": [{"x": 10, "y": 6}, {"x": 10, "y": 5}, {"x": 9, "y": 5}, {"x": 9, "y": 4}, {"x": 9, "y": 3}, {"x": 8, "y": 3}],
        "head": {"x": 10, "y": 6},
        "length": 6
      },
      {
        "id": "898824f2-7ffc-4a9e-bf12-cf8c3293782e",
        "name": "gemini-3-5-flash",
        "health": 96,
        "body": [{"x": 10, "y": 4}, {"x": 10, "y": 3}, {"x": 10, "y": 2}, {"x": 10, "y": 1}, {"x": 9, "y": 1}, {"x": 9, "y": 2}, {"x": 8, "y": 2}, {"x": 7, "y": 2}, {"x": 6, "y": 2}, {"x": 6, "y": 1}, {"x": 5, "y": 1}, {"x": 4, "y": 1}],
        "head": {"x": 10, "y": 4},
        "length": 12
      }
    ],
    "food": [{"x": 6, "y": 10}, {"x": 0, "y": 4}, {"x": 7, "y": 10}, {"x": 0, "y": 1}, {"x": 3, "y": 1}, {"x": 1, "y": 8}, {"x": 1, "y": 3}, {"x": 7, "y": 0}, {"x": 1, "y": 2}],
    "hazards": []
  },
  "you": {
    "id": "898824f2-7ffc-4a9e-bf12-cf8c3293782e",
    "name": "gemini-3-5-flash",
    "health": 96,
    "body": [{"x": 10, "y": 4}, {"x": 10, "y": 3}, {"x": 10, "y": 2}, {"x": 10, "y": 1}, {"x": 9, "y": 1}, {"x": 9, "y": 2}, {"x": 8, "y": 2}, {"x": 7, "y": 2}, {"x": 6, "y": 2}, {"x": 6, "y": 1}, {"x": 5, "y": 1}, {"x": 4, "y": 1}],
    "head": {"x": 10, "y": 4},
    "length": 12
  }
}

res = main.move(game_state)
print("Move result:", res)
