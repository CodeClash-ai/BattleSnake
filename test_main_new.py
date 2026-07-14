import unittest
from main import move

class TestMainNew(unittest.TestCase):
    def test_trivial(self):
        # We can construct a simple test game state and run move to verify no runtime crash.
        game_state = {
            "game": {"id": "test-game", "ruleset": {"name": "standard"}},
            "turn": 5,
            "board": {
                "height": 11,
                "width": 11,
                "snakes": [
                    {
                        "id": "me",
                        "name": "gemini-3-5-flash",
                        "health": 90,
                        "body": [{"x": 2, "y": 2}, {"x": 2, "y": 3}, {"x": 2, "y": 4}],
                        "head": {"x": 2, "y": 2},
                        "length": 3
                    },
                    {
                        "id": "opponent",
                        "name": "opponent",
                        "health": 90,
                        "body": [{"x": 8, "y": 8}, {"x": 8, "y": 7}],
                        "head": {"x": 8, "y": 8},
                        "length": 2
                    }
                ],
                "food": [{"x": 1, "y": 2}],
                "hazards": []
            },
            "you": {
                "id": "me",
                "name": "gemini-3-5-flash",
                "health": 90,
                "body": [{"x": 2, "y": 2}, {"x": 2, "y": 3}, {"x": 2, "y": 4}],
                "head": {"x": 2, "y": 2},
                "length": 3
            }
        }
        res = move(game_state)
        self.assertIn("move", res)
        self.assertIn(res["move"], ["up", "down", "left", "right"])

if __name__ == "__main__":
    unittest.main()
