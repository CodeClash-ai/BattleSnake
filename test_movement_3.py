import json
import main

# Let's mock a game_state where we are coiling and check our choices
game_state = {
  "board": {
    "height": 11,
    "width": 11,
    "snakes": [
      {
        "id": "us",
        "name": "gemini-3-5-flash",
        "latency": "1",
        "health": 100,
        "body": [
          {"x": 1, "y": 1},
          {"x": 1, "y": 2},
          {"x": 2, "y": 2},
          {"x": 2, "y": 1},
          {"x": 2, "y": 0}
        ],
        "head": {"x": 1, "y": 1},
        "length": 5
      }
    ],
    "food": [{"x": 9, "y": 9}]
  },
  "you": {
    "id": "us",
    "name": "gemini-3-5-flash",
    "latency": "1",
    "health": 100,
    "body": [
      {"x": 1, "y": 1},
      {"x": 1, "y": 2},
      {"x": 2, "y": 2},
      {"x": 2, "y": 1},
      {"x": 2, "y": 0}
    ],
    "head": {"x": 1, "y": 1},
    "length": 5,
    "health": 100
  }
}

print(main.move(game_state))
