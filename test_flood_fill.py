import main

# Test flood fill with a simple scenario
game_state = {
    'board': {
        'width': 11,
        'height': 11,
        'snakes': [
            {
                'id': 'me',
                'body': [
                    {'x': 5, 'y': 5},
                    {'x': 5, 'y': 4},
                    {'x': 5, 'y': 3}
                ]
            }
        ],
        'food': []
    },
    'you': {
        'id': 'me',
        'body': [
            {'x': 5, 'y': 5},
            {'x': 5, 'y': 4},
            {'x': 5, 'y': 3}
        ],
        'head': {'x': 5, 'y': 5},
        'length': 3,
        'health': 100
    }
}

# Test flood fill from head position
start_pos = {'x': 5, 'y': 5}
space = main.flood_fill_count(start_pos, game_state, max_depth=20)
print(f"Space available from (5,5): {space}")

# Test from a position to the right
start_pos = {'x': 6, 'y': 5}
space = main.flood_fill_count(start_pos, game_state, max_depth=20)
print(f"Space available from (6,5): {space}")

print("Flood fill test passed!")
