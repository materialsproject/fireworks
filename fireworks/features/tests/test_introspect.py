import unittest
from fireworks.features.introspect import flatten_to_keys, separator_str

__author__ = 'Anubhav Jain <ajain@lbl.gov>'



class IntrospectTest(unittest.TestCase):

    def test_flatten_dict(self):
        self.assertEqual(set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=1)), set(['d{}<TRUNCATED_OBJECT>'.format(separator_str)]))
        self.assertEqual(set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=2)), set(['d.e{}<TRUNCATED_OBJECT>'.format(separator_str), 'd.f{}10'.format(separator_str)]))
        self.assertEqual(set(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=3)), set(['d.e.f{}4'.format(separator_str), 'd.f{}10'.format(separator_str)]))
        self.assertEqual(set(flatten_to_keys({"d": [[0, 1], [2, 3]]}, max_recurs=5)), set(['d{}<TRUNCATED_OBJECT>'.format(separator_str)]))
        self.assertEqual(set(flatten_to_keys({"d": [1, 2, 3]}, max_recurs=2)), set(['d{}1'.format(separator_str), 'd{}2'.format(separator_str), 'd{}3'.format(separator_str)]))
        self.assertEqual(set(flatten_to_keys({"d": {"e": [0, 1]}}, max_recurs=2)), set(['d.e{}0'.format(separator_str), 'd.e{}1'.format(separator_str)]))