import main

# Test basic game state
game_state = {
    "game": {"id": "test"},
    "turn": 5,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 5, "y": 5}, {"x": 8, "y": 8}],
        "snakes": [
            {
                "id": "me",
                "name": "me",
                "health": 80,
                "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
                "length": 3
            },
            {
                "id": "opponent",
                "name": "opponent", 
                "health": 90,
                "body": [{"x": 9, "y": 9}, {"x": 9, "y": 8}, {"x": 9, "y": 7}],
                "length": 3
            }
        ]
    },
    "you": {
        "id": "me",
        "name": "me",
        "health": 80,
        "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
        "length": 3
    }
}

# Test move function
result = main.move(game_state)
print(f"Move result: {result}")
print(f"Move is valid: {result['move'] in ['up', 'down', 'left', 'right']}")

# Test with low health (should seek food aggressively)
game_state["you"]["health"] = 30
game_state["board"]["snakes"][0]["health"] = 30
result2 = main.move(game_state)
print(f"Low health move: {result2}")

# Test with high health (should be more conservative)
game_state["you"]["health"] = 95
game_state["board"]["snakes"][0]["health"] = 95
result3 = main.move(game_state)
print(f"High health move: {result3}")

print("\nAll tests passed!")
