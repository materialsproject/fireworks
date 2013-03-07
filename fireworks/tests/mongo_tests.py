import unittest
from fireworks.core.firework import FireWork
from fireworks.core.launchpad import LaunchPad
from fireworks.user_objects.firetasks.script_task import ScriptTask

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Mar 06, 2013'

TESTDB_NAME = 'fireworks_unittest'

class MongoTests(unittest.TestCase):

    def setUp(self):
        self.lp = None
        try:
            self.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            self.lp.reset(password=None, require_password=False)
        except:
            raise unittest.SkipTest('MongoDB is not running in localhost:27017! Skipping tests.')

    def test_basic_fw(self):

        fw = FireWork(ScriptTask.from_str('echo "hello"'))
        self.lp.add_wf(fw)
        






    def tearDown(self):
        self.lp.connection.drop_database(TESTDB_NAME)

if __name__ == "__main__":
    unittest.main()