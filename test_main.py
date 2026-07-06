import unittest
from main import move, info

class TestMain(unittest.TestCase):
    def test_basic_move(self):
        game_state = {
            "game": {"id": "game-id", "ruleset": {"name": "standard"}, "timeout": 500},
            "turn": 1,
            "board": {
                "height": 11,
                "width": 11,
                "food": [{"x": 5, "y": 5}],
                "hazards": [],
                "snakes": [
                    {
                        "id": "my-id",
                        "name": "My Snake",
                        "latency": "10",
                        "health": 90,
                        "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
                        "head": {"x": 1, "y": 1},
                        "length": 3,
                        "shout": "",
                        "squad": ""
                    }
                ]
            },
            "you": {
                "id": "my-id",
                "name": "My Snake",
                "latency": "10",
                "health": 90,
                "body": [{"x": 1, "y": 1}, {"x": 1, "y": 2}, {"x": 1, "y": 3}],
                "head": {"x": 1, "y": 1},
                "length": 3,
                "shout": "",
                "squad": ""
            }
        }
        res = move(game_state)
        print("Test Move Result:", res)
        self.assertIn(res["move"], ["up", "down", "left", "right"])

if __name__ == "__main__":
    unittest.main()
