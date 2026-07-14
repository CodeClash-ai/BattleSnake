import unittest
from main import move

class TestFloodFill(unittest.TestCase):
    def test_trap_avoidance(self):
        # Construct a scenario where 'down' leads to a dead end pocket of size 2,
        # but 'right' leads to an open area.
        game_state = {
            "game": {"id": "test", "ruleset": {"name": "standard"}},
            "turn": 10,
            "board": {
                "height": 11,
                "width": 11,
                "snakes": [
                    {
                        "id": "me",
                        "name": "gemini-3-5-flash",
                        "health": 90,
                        "body": [{"x": 1, "y": 2}, {"x": 1, "y": 3}, {"x": 1, "y": 4}],
                        "head": {"x": 1, "y": 2},
                        "length": 3
                    }
                ],
                "food": [{"x": 9, "y": 9}],
                "hazards": []
            },
            "you": {
                "id": "me",
                "name": "gemini-3-5-flash",
                "health": 90,
                "body": [{"x": 1, "y": 2}, {"x": 1, "y": 3}, {"x": 1, "y": 4}],
                "head": {"x": 1, "y": 2},
                "length": 3
            }
        }
        # Obstacles layout to block moves.
        # Let's say:
        # head is at (1,2)
        # down is (1,1). We make a wall of obstacles at y=0, and on sides of x=1 at y=1.
        # So (0,1) and (2,1) are blocked, and (1,0) is blocked.
        # This makes (1,1) a dead end pocket with area = 1 (just (1,1) itself).
        # 'right' is (2,2) which has access to the rest of the board.
        game_state["board"]["snakes"].append({
            "id": "obstacle-snake",
            "name": "obstacle",
            "health": 90,
            "body": [
                {"x": 0, "y": 1},
                {"x": 2, "y": 1},
                {"x": 1, "y": 0}
            ],
            "head": {"x": 0, "y": 1},
            "length": 3
        })
        
        res = move(game_state)
        # Should pick 'right' over 'down'
        self.assertEqual(res["move"], "right")

if __name__ == "__main__":
    unittest.main()
