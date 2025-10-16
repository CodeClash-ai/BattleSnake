import json
import sys
sys.path.insert(0, '/workspace')
from main import move

# Recreate the game state from turn 41 where we died
game_state = {
    "game": {"id": "test"},
    "turn": 41,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 10, "y": 0}],
        "snakes": [
            {
                "id": "us",
                "name": "claude-sonnet-4-5-20250929",
                "health": 99,
                "body": [
                    {"x": 7, "y": 6},  # head
                    {"x": 7, "y": 7},
                    {"x": 8, "y": 7},
                    {"x": 8, "y": 6},
                    {"x": 8, "y": 5},
                    {"x": 7, "y": 5},
                    {"x": 6, "y": 5}   # tail
                ],
                "head": {"x": 7, "y": 6},
                "length": 7
            },
            {
                "id": "opp",
                "name": "gemini-2.5-pro",
                "health": 88,
                "body": [
                    {"x": 5, "y": 6},  # head
                    {"x": 5, "y": 7},
                    {"x": 4, "y": 7},
                    {"x": 3, "y": 7},
                    {"x": 2, "y": 7},
                    {"x": 1, "y": 7},
                    {"x": 0, "y": 7},
                    {"x": 0, "y": 6},
                    {"x": 0, "y": 5}   # tail
                ],
                "head": {"x": 5, "y": 6},
                "length": 9
            }
        ]
    },
    "you": {
        "id": "us",
        "name": "claude-sonnet-4-5-20250929",
        "health": 99,
        "body": [
            {"x": 7, "y": 6},
            {"x": 7, "y": 7},
            {"x": 8, "y": 7},
            {"x": 8, "y": 6},
            {"x": 8, "y": 5},
            {"x": 7, "y": 5},
            {"x": 6, "y": 5}
        ],
        "head": {"x": 7, "y": 6},
        "length": 7
    }
}

print("Testing move decision for the game state where we died...")
print(f"Our head: (7, 6)")
print(f"Our body: {[(b['x'], b['y']) for b in game_state['you']['body']]}")
print(f"Opponent head: (5, 6)")
print()

result = move(game_state)
print(f"\nChosen move: {result['move']}")
print("\nExpected: 'left' (only safe move)")
