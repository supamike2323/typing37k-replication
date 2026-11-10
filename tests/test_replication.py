import unittest

import numpy as np

from typing37k.replication import _cohen_d, _comparison_tests


class ReplicationTests(unittest.TestCase):
    def test_holm_is_applied_within_each_test_family(self):
        samples = {
            "a": np.array([1, 2, 3, 4, 5]),
            "b": np.array([4, 5, 6, 7, 8]),
            "c": np.array([7, 8, 9, 10, 11]),
            "d": np.array([9, 10, 11, 12, 13]),
        }
        _, pairs = _comparison_tests({"one": samples, "two": {"a": samples["a"], "d": samples["d"]}})
        primary = pairs.loc[pairs.family == "one"].sort_values("p_raw")
        expected = np.minimum(1, np.maximum.accumulate(primary.p_raw.to_numpy() * np.arange(6, 0, -1)))
        np.testing.assert_allclose(primary.p_holm, expected)
        secondary = pairs.loc[pairs.family == "two"].iloc[0]
        self.assertEqual(secondary.p_holm, secondary.p_raw)

    def test_signed_cohen_d_uses_pooled_sample_sd(self):
        first = np.array([1, 3, 5])
        second = np.array([5, 7, 9])
        self.assertAlmostEqual(_cohen_d(first, second), -2.0)
        self.assertAlmostEqual(_cohen_d(second, first), 2.0)
