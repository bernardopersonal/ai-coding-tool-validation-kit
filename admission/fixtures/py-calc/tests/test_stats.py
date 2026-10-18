import unittest

from calc.stats import mean, median


class MeanTests(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean([1, 2, 3, 4]), 2.5)

    def test_mean_empty(self):
        with self.assertRaises(ValueError):
            mean([])


class MedianTests(unittest.TestCase):
    def test_median_odd_length(self):
        self.assertEqual(median([3, 1, 2]), 2)

    def test_median_even_length(self):
        self.assertEqual(median([4, 1, 3, 2]), 2.5)

    def test_median_unsorted_input_not_modified(self):
        data = [5, 3, 1]
        median(data)
        self.assertEqual(data, [5, 3, 1])

    def test_median_empty(self):
        with self.assertRaises(ValueError):
            median([])


if __name__ == "__main__":
    unittest.main()
