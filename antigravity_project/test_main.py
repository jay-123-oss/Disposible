import unittest
from utils import calculate_metrics

class TestUtils(unittest.TestCase):
    def test_metrics(self):
        res = calculate_metrics([10, 20, 30])
        self.assertEqual(res["total"], 60)
        self.assertEqual(res["avg"], 20.0)

if __name__ == "__main__":
    unittest.main()