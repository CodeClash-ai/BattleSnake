#!/usr/bin/env python3
"""
Simple test to verify bot logic works correctly.
"""

import main

# Create a simple test game state
test_game_state = {
    "game": {"id": "test"},
    "turn": 5,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 5, "y": 5}],
        "snakes": [
            {
                "id": "test-snake",
                "name": "test-snake",
                "health": 80,
                "body": [
                    {"x": 3, "y": 3},
                    {"x": 3, "y": 2},
                    {"x": 3, "y": 1}
                ],
                "head": {"x": 3, "y": 3},
                "length": 3
            }
        ]
    },
    "you": {
        "id": "test-snake",
        "name": "test-snake",
        "health": 80,
        "body": [
            {"x": 3, "y": 3},
            {"x": 3, "y": 2},
            {"x": 3, "y": 1}
        ],
        "head": {"x": 3, "y": 3},
        "length": 3
    }
}

print("Testing bot with sample game state...")
try:
    result = main.move(test_game_state)
    print(f"Bot returned move: {result}")
    print("✓ Bot test passed!")
except Exception as e:
    print(f"✗ Bot test failed with error: {e}")
    import traceback
    traceback.print_exc()
