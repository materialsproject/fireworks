from unittest import TestCase
import pickle

from fireworks import Workflow


class TestLinks(TestCase):
    def test_pickle(self):
        links1 = Workflow.Links({1: 2, 3: [5, 7, 8]})
        s = pickle.dumps(links1)
        links2 = pickle.loads(s)
        self.assertEqual(str(links1), str(links2))
