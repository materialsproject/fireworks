import pickle
from unittest import TestCase
import unittest
from fireworks.core.firework import Workflow

__author__ = 'xiaohuiqu'


class TestLinks(TestCase):
    def test_pickle(self):
        links1 = Workflow.Links({1: 2, 3: [5, 7, 8]})
        s = pickle.dumps(links1)
        links2 = pickle.loads(s)
        self.assertEqual(str(links1), str(links2))


if __name__ == '__main__':
    unittest.main()