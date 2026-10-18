import re
import unittest

from calc.version import VERSION


class VersionTests(unittest.TestCase):
    def test_semantic_version(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
