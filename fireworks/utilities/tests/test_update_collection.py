import datetime
import os
import unittest

from fireworks import LaunchPad
from fireworks.utilities.update_collection import update_path_in_collection

__author__ = "Alireza Faghaninia, Anubhav Jain"
__email__ = "alireza.faghaninia@gmail.com, ajain@lbl.gov"
__date__ = "Dec 08, 2016"

TESTDB_NAME = "fireworks_unittest"
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class UpdateCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lp = None
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl="ERROR")
            cls.lp.reset(password=None, require_password=False)
        except Exception:
            raise unittest.SkipTest("MongoDB is not running in localhost:27017! Skipping tests.")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def test_update_path(self) -> None:
        self.lp.db.test_coll.insert_one({"foo": "bar", "foo_list": [{"foo1": "bar1"}, {"foo2": "foo/old/path/bar"}]})
        update_path_in_collection(
            self.lp.db,
            collection_name="test_coll",
            replacements={"old/path": "new/path"},
            query=None,
            dry_run=False,
            force_clear=False,
        )
        n_docs = self.lp.db.test_coll.count_documents({})
        assert n_docs == 1
        test_doc = self.lp.db.test_coll.find_one({"foo": "bar"})
        assert test_doc["foo_list"][1]["foo2"] == "foo/new/path/bar"
        test_doc_archived = self.lp.db[f"test_coll_xiv_{datetime.date.today()}"].find_one()
        assert test_doc_archived["foo_list"][1]["foo2"] == "foo/old/path/bar"
