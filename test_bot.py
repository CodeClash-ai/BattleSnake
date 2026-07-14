import unittest
from main import move

class TestBot(unittest.TestCase):
    def test_basic_move(self):
        # A simple state where we are in the center and can go any direction
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
                        "body": [{"x": 5, "y": 5}, {"x": 5, "y": 6}, {"x": 5, "y": 7}],
                        "head": {"x": 5, "y": 5},
                        "length": 3
                    }
                ],
                "food": [{"x": 5, "y": 4}]
            },
            "you": {
                "id": "you",
                "name": "gemini-3-5-flash",
                "health": 100,
                "body": [{"x": 5, "y": 5}, {"x": 5, "y": 6}, {"x": 5, "y": 7}],
                "head": {"x": 5, "y": 5},
                "length": 3
            }
        }
        res = move(game_state)
        self.assertIn(res["move"], ["up", "down", "left", "right"])

if __name__ == "__main__":
    unittest.main()
