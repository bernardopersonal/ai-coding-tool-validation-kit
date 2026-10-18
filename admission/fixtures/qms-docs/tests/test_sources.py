import os
import unittest

from doctools.sources import list_sources

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SourcesTests(unittest.TestCase):
    def test_lists_the_three_sources(self):
        self.assertEqual(list_sources(ROOT), [
            "docs/sources/change-control.md",
            "docs/sources/records-retention.md",
            "docs/sources/training.md",
        ])


if __name__ == "__main__":
    unittest.main()
