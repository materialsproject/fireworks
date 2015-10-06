import unittest
from fireworks.features.introspect import flatten_to_keys, separator_str

__author__ = 'Anubhav Jain <ajain@lbl.gov>'



class IntrospectTest(unittest.TestCase):

    def test_flatten_dict(self):
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=1), ['d{}<TRUNCATED_OBJECT>'.format(separator_str)])
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=2), ['d.e{}<TRUNCATED_OBJECT>'.format(separator_str), 'd.f{}10'.format(separator_str)])
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=3), ['d.e.f{}4'.format(separator_str), 'd.f{}10'.format(separator_str)])
        self.assertEqual(flatten_to_keys({"d": [[0, 1], [2, 3]]}, max_recurs=5), ['d{}<TRUNCATED_OBJECT>'.format(separator_str)])
        self.assertEqual(flatten_to_keys({"d": [1, 2, 3]}, max_recurs=2), ['d{}1'.format(separator_str), 'd{}2'.format(separator_str), 'd{}3'.format(separator_str)])
        self.assertEqual(flatten_to_keys({"d": {"e": [0, 1]}}, max_recurs=2), ['d.e{}0'.format(separator_str), 'd.e{}1'.format(separator_str)])