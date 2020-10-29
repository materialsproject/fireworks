import dataclasses

from fireworks import FiretaskBase


@dataclasses.dataclass
class DummyTask1(FiretaskBase):
    hello: str

    def run_task(self, fw_spec):
        return self.hello


@dataclasses.dataclass
class DummyTask2(FiretaskBase):
    _fw_name = "DummyTask"
    param1: int
    param2: int = None


@dataclasses.dataclass
class DummyTask3(FiretaskBase):
    hello: str

    def run_task(self, fw_spec):
        return self["hello"]


class DummyTask4(FiretaskBase):

    required_params = ["hello"]

    def run_task(self, fw_spec):
        return self.hello

