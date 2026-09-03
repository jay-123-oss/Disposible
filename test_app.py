import os
import unittest

class TestCoffeeApplication(unittest.TestCase):
    def test_required_files_exist(self):
        for f in ["index.html", "style.css", "script.js"]:
            self.assertTrue(os.path.exists(f), f"{f} must exist")

    def test_html_content(self):
        with open("index.html", "r", encoding="utf-8") as fp:
            content = fp.read()
        self.assertIn("RoastCraft", content)
        self.assertIn("Ethiopian Yirgacheffe", content)

if __name__ == "__main__":
    unittest.main()