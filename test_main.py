import json
from main import move

# Test a simple mock state where a snake is following its own tail or trapped in a pocket
# to ensure everything parses and works without error.
game_state = {
    "game": {"id": "game-id", "timeout": 500},
    "turn": 5,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 5, "y": 5}],
        "hazards": [],
        "snakes": [
            {
                "id": "us",
                "name": "gemini-3-5-flash",
                "latency": "100",
                "health": 100,
                "body": [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 0, "y": 2}],
                "head": {"x": 0, "y": 0},
                "length": 3,
                "shout": "",
                "squad": ""
            }
        ]
    },
    "you": {
        "id": "us",
        "name": "gemini-3-5-flash",
        "latency": "100",
        "health": 100,
        "body": [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 0, "y": 2}],
        "head": {"x": 0, "y": 0},
        "length": 3,
        "shout": "",
        "squad": ""
    }
}

print(move(game_state))
