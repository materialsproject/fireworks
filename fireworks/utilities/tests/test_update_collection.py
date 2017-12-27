import unittest
import os
import datetime
from fireworks import LaunchPad
from fireworks.utilities.update_collection import update_path_in_collection

__author__ = 'Alireza Faghaninia, Anubhav Jain'
__email__ = 'alireza.faghaninia@gmail.com, ajain@lbl.gov'
__date__ = 'Dec 08, 2016'

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

class UpdateCollectionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lp = None
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:27017! Skipping tests.')

    @classmethod
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def test_update_path(cls):
        cls.lp.db.test_coll.insert({"foo": "bar", "foo_list": [{"foo1": "bar1"}, {"foo2": "foo/old/path/bar"}]})
        update_path_in_collection(cls.lp.db, collection_name="test_coll", replacements={"old/path": "new/path"},
                                              query=None, dry_run=False, force_clear=False)
        ndocs = cls.lp.db.test_coll.count()
        cls.assertEqual(ndocs, 1)
        test_doc = cls.lp.db.test_coll.find_one({"foo": "bar"})
        cls.assertEqual(test_doc["foo_list"][1]["foo2"], "foo/new/path/bar")
        test_doc_archived = cls.lp.db["{}_xiv_{}".format("test_coll", datetime.date.today())].find_one()
        cls.assertEqual(test_doc_archived["foo_list"][1]["foo2"], "foo/old/path/bar")

if __name__ == "__main__":
    unittest.main()