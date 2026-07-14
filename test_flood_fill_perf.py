import time
import main

# Let's mock a game state with a very long snake to see how fast we can run under extreme conditions.
# Board is 11x11.
body = [{"x": x % 11, "y": x // 11} for x in range(100)]
game_state = {
    "board": {
        "width": 11,
        "height": 11,
        "food": [{"x": 5, "y": 5}],
        "snakes": [
            {
                "id": "me",
                "name": "gemini-3-5-flash",
                "health": 90,
                "body": body,
                "latency": "0"
            }
        ]
    },
    "you": {
        "id": "me",
        "name": "gemini-3-5-flash",
        "health": 90,
        "body": body
    }
}

t0 = time.perf_counter()
for _ in range(1000):
    res = main.move(game_state)
t1 = time.perf_counter()
print(f"Time for 1000 moves: {t1 - t0:.4f}s (Average: {(t1 - t0)/1000 * 1000:.4f}ms)")
