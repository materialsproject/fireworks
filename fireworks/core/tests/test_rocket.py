import os
import unittest

from fireworks import Firework, FWorker, LaunchPad
from fireworks.core.rocket_launcher import launch_rocket
from fireworks.core.tests.tasks import ExceptionTestTask, MalformedAdditionTask

TESTDB_NAME = "fireworks_unittest"
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class RocketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl="ERROR")
            cls.lp.reset(password=None, require_password=False)
        except Exception:
            raise unittest.SkipTest("MongoDB is not running in localhost:27017! Skipping tests.")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        self.lp.reset(password=None, require_password=False)
        # Delete launch locations
        if os.path.exists(os.path.join("FW.json")):
            os.remove("FW.json")

    def test_serializable_exception(self) -> None:
        error_test_dict = {"error": "description", "error_code": 1}
        fw = Firework(ExceptionTestTask(exc_details=error_test_dict))
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)

        # Check data in the exception
        fw = self.lp.get_fw_by_id(1)
        launches = fw.launches
        assert launches[0].action.stored_data["_exception"]["_details"] == error_test_dict

    def test_postproc_exception(self) -> None:
        fw = Firework(MalformedAdditionTask())
        self.lp.add_wf(fw)
        launch_rocket(self.lp, self.fworker)
        fw = self.lp.get_fw_by_id(1)

        assert fw.state == "FIZZLED"
