#!/usr/bin/env python3
"""
Test edge cases for the bot.
"""

import main

# Test case 1: Snake near wall
test_near_wall = {
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
                "health": 50,
                "body": [
                    {"x": 0, "y": 0},
                    {"x": 0, "y": 1},
                    {"x": 0, "y": 2}
                ],
                "head": {"x": 0, "y": 0},
                "length": 3
            }
        ]
    },
    "you": {
        "id": "test-snake",
        "name": "test-snake",
        "health": 50,
        "body": [
            {"x": 0, "y": 0},
            {"x": 0, "y": 1},
            {"x": 0, "y": 2}
        ],
        "head": {"x": 0, "y": 0},
        "length": 3
    }
}

# Test case 2: Low health
test_low_health = {
    "game": {"id": "test"},
    "turn": 10,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 5, "y": 5}],
        "snakes": [
            {
                "id": "test-snake",
                "name": "test-snake",
                "health": 20,
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
        "health": 20,
        "body": [
            {"x": 3, "y": 3},
            {"x": 3, "y": 2},
            {"x": 3, "y": 1}
        ],
        "head": {"x": 3, "y": 3},
        "length": 3
    }
}

print("Test 1: Snake near wall")
try:
    result = main.move(test_near_wall)
    print(f"✓ Returned: {result['move']}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")

print("Test 2: Low health (should seek food)")
try:
    result = main.move(test_low_health)
    print(f"✓ Returned: {result['move']}\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")

print("All edge case tests completed!")
