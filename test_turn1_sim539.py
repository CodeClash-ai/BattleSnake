import json
import sys
sys.path.insert(0, '/workspace')
from main import move

# Recreate turn 1 state from sim_539
game_state = {
    "game": {"id": "test"},
    "turn": 1,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 6, "y": 0}, {"x": 0, "y": 6}, {"x": 5, "y": 5}],
        "snakes": [
            {
                "id": "us",
                "name": "claude-sonnet-4-5-20250929",
                "health": 99,
                "body": [{"x": 5, "y": 0}, {"x": 5, "y": 1}, {"x": 5, "y": 1}],
                "head": {"x": 5, "y": 0},
                "length": 3
            },
            {
                "id": "them",
                "name": "gemini-2.5-pro",
                "health": 99,
                "body": [{"x": 1, "y": 6}, {"x": 1, "y": 5}, {"x": 1, "y": 5}],
                "head": {"x": 1, "y": 6},
                "length": 3
            }
        ]
    },
    "you": {
        "id": "us",
        "name": "claude-sonnet-4-5-20250929",
        "health": 99,
        "body": [{"x": 5, "y": 0}, {"x": 5, "y": 1}, {"x": 5, "y": 1}],
        "head": {"x": 5, "y": 0},
        "length": 3
    }
}

result = move(game_state)
print(f"Move chosen: {result['move']}")
