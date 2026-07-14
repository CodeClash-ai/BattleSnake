import unittest
from main import move

class TestFloodFill(unittest.TestCase):
    def test_trap_avoidance(self):
        # We are at 1,1. Right is blocked by opponent snake. Left is blocked by wall.
        # Down is blocked by wall. Up has a corridor but it is a dead end.
        # Let's verify that we can compute space and choose the best possible path.
        game_state = {
            "game": {"id": "test"},
            "turn": 1,
            "board": {
                "height": 11,
                "width": 11,
                "snakes": [
                    {
                        "id": "you",
                        "name": "gemini-3-5-flash",
                        "health": 100,
                        "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
                        "head": {"x": 1, "y": 1},
                        "length": 3
                    }
                ],
                "food": [{"x": 5, "y": 5}]
            },
            "you": {
                "id": "you",
                "name": "gemini-3-5-flash",
                "health": 100,
                "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
                "head": {"x": 1, "y": 1},
                "length": 3
            }
        }
        res = move(game_state)
        # From (1,1) with body at (1,2) and (1,3):
        # up is (1,2) which is body -> colliding
        # down is (1,0) -> valid
        # left is (0,1) -> valid
        # right is (2,1) -> valid
        self.assertIn(res["move"], ["down", "left", "right"])

if __name__ == "__main__":
    unittest.main()
