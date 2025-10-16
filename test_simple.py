# Test basic functionality
import main

# Simulate a simple game state
game_state = {
    "game": {"id": "test"},
    "turn": 1,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 5, "y": 5}],
        "snakes": [
            {
                "id": "me",
                "name": "claude-sonnet-4-5-20250929",
                "health": 100,
                "body": [{"x": 1, "y": 1}, {"x": 1, "y": 1}, {"x": 1, "y": 1}],
                "head": {"x": 1, "y": 1},
                "length": 3
            }
        ]
    },
    "you": {
        "id": "me",
        "name": "claude-sonnet-4-5-20250929",
        "health": 100,
        "body": [{"x": 1, "y": 1}, {"x": 1, "y": 1}, {"x": 1, "y": 1}],
        "head": {"x": 1, "y": 1},
        "length": 3
    }
}

result = main.move(game_state)
print(f"Move result: {result}")
