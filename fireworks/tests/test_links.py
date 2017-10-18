from unittest import TestCase
import pickle

from fireworks import Firework, Workflow


class TestLinks(TestCase):
    def setUp(self):
        self.links = Workflow.Links({1: 2, 3: [5, 7, 8], 4: 5})

    def test_pickle(self):
        s = pickle.dumps(self.links)
        links2 = pickle.loads(s)
        self.assertEqual(str(self.links), str(links2))

    def test_nodes(self):
        self.assertEqual(self.links.nodes, [1, 2, 3, 4, 5, 7, 8])

    def test_parent_links(self):
        self.assertEqual(self.links.parent_links,
                         {2: [1], 5: [3, 4], 7: [3], 8: [3]})

    def test_firework_keys(self):
        # test setting with Fireworks as keys still works
        fw1 = Firework([], fw_id=1)
        l = Workflow.Links({fw1: 2, 3: [5, 7, 8]})
        self.assertEqual(1 in l.keys(), True)

    def test_firework_values(self):
        # test setting with Fireworks amongst values
        fw3 = Firework([], fw_id=3)
        fw4 = Firework([], fw_id=4)
        l = Workflow.Links({1: 2,  6: [fw3, fw4, 5]})

        self.assertEqual(l[6], [3, 4, 5])

    def test_to_dict(self):
        self.assertEqual(self.links.to_dict(),
                         {'1': [2],
                          '3': [5, 7, 8],
                          '4': [5]})

    def test_to_db_dict(self):
        self.assertEqual(self.links.to_db_dict(),
                         {'links': {'1': [2], '3': [5, 7, 8], '4': [5]},
                          'nodes': [1, 2, 3, 4, 5, 7, 8],
                          'parent_links': {'2': [1], '5': [3, 4], '7': [3],
                                           '8': [3]}})

    def test_from_dict(self):
        l = Workflow.Links.from_dict({1: [5, 6]})
        self.assertEqual(l, Workflow.Links({1: [5, 6]}))

    def test_getitem(self):
        self.assertEqual(self.links[1], [2])
        self.assertEqual(self.links[3], [5, 7, 8])
        self.assertEqual(self.links[4], [5])

    def test_delitems(self):
        del self.links[4]
        self.assertEqual(self.links.nodes, [1, 2, 3, 5, 7, 8])

    def test_items(self):
        self.assertEqual(list(self.links.items()),
                         [(1, [2]),
                          (3, [5, 7, 8]),
                          (4, [5])])
