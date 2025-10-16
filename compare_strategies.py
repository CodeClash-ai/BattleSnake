import main as main_round4
import main_round3_backup as main_round3

# Test scenario: Food that opponent is closer to
game_state = {
    "game": {"id": "test"},
    "turn": 10,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 8, "y": 5}],  # Food closer to opponent
        "snakes": [
            {
                "id": "me",
                "name": "me",
                "health": 60,
                "body": [{"x": 2, "y": 5}, {"x": 2, "y": 4}, {"x": 2, "y": 3}],
                "length": 3
            },
            {
                "id": "opponent",
                "name": "opponent", 
                "health": 90,
                "body": [{"x": 7, "y": 5}, {"x": 7, "y": 4}, {"x": 7, "y": 3}],
                "length": 3
            }
        ]
    },
    "you": {
        "id": "me",
        "name": "me",
        "health": 60,
        "body": [{"x": 2, "y": 5}, {"x": 2, "y": 4}, {"x": 2, "y": 3}],
        "length": 3
    }
}

print("Scenario: Food at (8,5), we're at (2,5), opponent at (7,5)")
print("Opponent is closer to food (distance 1 vs our distance 6)")
print()

result_r3 = main_round3.move(game_state)
print(f"Round 3 strategy: {result_r3['move']}")

result_r4 = main_round4.move(game_state)
print(f"Round 4 strategy: {result_r4['move']}")

print("\n" + "="*50)

# Test scenario: High health, should avoid edges
game_state2 = {
    "game": {"id": "test"},
    "turn": 20,
    "board": {
        "height": 11,
        "width": 11,
        "food": [{"x": 10, "y": 10}],  # Food in corner
        "snakes": [
            {
                "id": "me",
                "name": "me",
                "health": 95,
                "body": [{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 3}],
                "length": 3
            }
        ]
    },
    "you": {
        "id": "me",
        "name": "me",
        "health": 95,
        "body": [{"x": 5, "y": 5}, {"x": 5, "y": 4}, {"x": 5, "y": 3}],
        "length": 3
    }
}

print("\nScenario: High health (95), food in corner, we're in center")
print()

result_r3_2 = main_round3.move(game_state2)
print(f"Round 3 strategy: {result_r3_2['move']}")

result_r4_2 = main_round4.move(game_state2)
print(f"Round 4 strategy: {result_r4_2['move']}")

print("\nComparison complete!")
