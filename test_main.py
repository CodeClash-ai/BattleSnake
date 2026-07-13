import unittest
from main import _time_aware_flood_fill, _voronoi_territory

class TestMain(unittest.TestCase):
    def test_flood_fill(self):
        # basic validation
        snakes = [{"body": [{"x": 1, "y": 0}, {"x": 2, "y": 0}]}]
        res = _time_aware_flood_fill((0, 0), 3, 3, snakes)
        self.assertGreater(res, 0)

if __name__ == "__main__":
    unittest.main()
