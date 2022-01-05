import time
from unittest import SkipTest

from fireworks import FiretaskBase, Firework, FWAction
from fireworks.utilities.fw_utilities import explicit_serialize


class SerializableException(Exception):
    def __init__(self, exc_details):
        self.exc_details = exc_details

    def to_dict(self):
        return self.exc_details


@explicit_serialize
class ExceptionTestTask(FiretaskBase):
    exec_counter = 0

    def run_task(self, fw_spec):
        ExceptionTestTask.exec_counter += 1
        if not fw_spec.get("skip_exception", False):
            raise SerializableException(self["exc_details"])


@explicit_serialize
class ExecutionCounterTask(FiretaskBase):
    exec_counter = 0

    def run_task(self, fw_spec):
        ExecutionCounterTask.exec_counter += 1


@explicit_serialize
class MalformedAdditionTask(FiretaskBase):
    def run_task(self, fw_spec):
        return FWAction(additions=TodictErrorTask())


@explicit_serialize
class TodictErrorTask(FiretaskBase):
    def to_dict(self):
        raise RuntimeError("to_dict error")

    def run_task(self, fw_spec):
        return FWAction()


@explicit_serialize
class SlowAdditionTask(FiretaskBase):
    def run_task(self, fw_spec):
        time.sleep(5)
        return FWAction(
            additions=Firework(SlowTodictTask(seconds=fw_spec.get("seconds", 10))), update_spec={"SlowAdditionTask": 1}
        )


@explicit_serialize
class SlowTodictTask(FiretaskBase):
    def to_dict(self):
        time.sleep(self.get("seconds", 10))
        return super().to_dict()

    def run_task(self, fw_spec):
        return FWAction()


@explicit_serialize
class WaitWFLockTask(FiretaskBase):
    def run_task(self, fw_spec):
        if "_add_launchpad_and_fw_id" not in fw_spec:
            raise SkipTest("Couldn't load lunchpad")

        timeout = 20
        while not self.launchpad.workflows.find_one({"locked": {"$exists": True}, "nodes": self.fw_id}) and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if timeout == 0:
            raise SkipTest("The WF wasn't locked")

        if fw_spec.get("fizzle", False):
            raise ValueError("Testing; this error is normal.")

        return FWAction(update_spec={"WaitWFLockTask": 1})


@explicit_serialize
class DoNothingTask(FiretaskBase):
    def run_task(self, fw_spec):
        pass


@explicit_serialize
class DetoursTask(FiretaskBase):
    optional_params = ["n_detours", "data_per_detour"]

    def run_task(self, fw_spec):
        data_per_detour = self.get("data_per_detour", None)
        n_detours = self.get("n_detours", 10)
        fws = []
        for _ in range(n_detours):
            fws.append(Firework([DoNothingTask(data=data_per_detour)]))

        return FWAction(detours=fws)
