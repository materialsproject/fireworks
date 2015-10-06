import unittest
from fireworks.features.introspect import flatten_to_keys

__author__ = 'Anubhav Jain <ajain@lbl.gov>'



class IntrospectTest(unittest.TestCase):

    def test_flatten_dict(self):
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=1), ['d:<TRUNCATED_OBJECT>'])
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=2), ['d.e:<TRUNCATED_OBJECT>', 'd.f:10'])
        self.assertEqual(flatten_to_keys({"d": {"e": {"f": 4}, "f": 10}}, max_recurs=3), ['d.e.f:4', 'd.f:10'])
        self.assertEqual(flatten_to_keys({"d": [[0, 1], [2, 3]]}, max_recurs=5), ['d:<TRUNCATED_OBJECT>'])
        self.assertEqual(flatten_to_keys({"d": [1, 2, 3]}, max_recurs=2), ['d:1', 'd:2', 'd:3'])
        self.assertEqual(flatten_to_keys({"d": {"e": [0, 1]}}, max_recurs=2), ['d.e:0', 'd.e:1'])