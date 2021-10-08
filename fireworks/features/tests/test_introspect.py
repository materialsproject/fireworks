import unittest

from fireworks.features.introspect import flatten_to_keys, separator_str

__author__ = "Anubhav Jain <ajain@lbl.gov>"


class IntrospectTest(unittest.TestCase):
    def test_flatten_dict(self):
        self.assertEqual(
            set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=1)), {f"d{separator_str}<TRUNCATED_OBJECT>"}
        )
        self.assertEqual(
            set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=2)),
            {f"d.e{separator_str}<TRUNCATED_OBJECT>", f"d.f{separator_str}10"},
        )
        self.assertEqual(
            set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=3)),
            {f"d.e.f{separator_str}4", f"d.f{separator_str}10"},
        )
        self.assertEqual(
            set(flatten_to_keys({"d": [[0, 1], [2, 3]]}, max_recurs=5)), {f"d{separator_str}<TRUNCATED_OBJECT>"}
        )
        self.assertEqual(
            set(flatten_to_keys({"d": [1, 2, 3]}, max_recurs=2)),
            {f"d{separator_str}1", f"d{separator_str}2", f"d{separator_str}3"},
        )
        self.assertEqual(
            set(flatten_to_keys({"d": {"e": [0, 1]}}, max_recurs=2)), {f"d.e{separator_str}0", f"d.e{separator_str}1"}
        )
