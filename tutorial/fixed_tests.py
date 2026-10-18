"""Fixed grading tests. Injected only into the separate grader container."""

import unittest

from project import sum_even


class RepairTests(unittest.TestCase):
    def test_mixed(self):
        self.assertEqual(sum_even([1, 2, 3, 4]), 6)

    def test_empty(self):
        self.assertEqual(sum_even([]), 0)

    def test_all_odd(self):
        self.assertEqual(sum_even([1, 3, 5]), 0)

    def test_negative_and_zero(self):
        self.assertEqual(sum_even([-3, -2, 0, 4]), 2)

    def test_does_not_mutate(self):
        numbers = [3, 2, 4]
        self.assertEqual(sum_even(numbers), 6)
        self.assertEqual(numbers, [3, 2, 4])
