"""
Example of how to use dataclass Firetasks.

Note: Dataclass Fireworks require python 3.6+.
"""

from dataclasses import dataclass

from fireworks import FiretaskBase, explicit_serialize


@dataclass(repr=False)
@explicit_serialize
class DataclassTask(FiretaskBase):
    param: str
    param_a: int = 0

    def run_task(self, fw_spec):
        # You can interact with dataclass Firetasks like you would a dict or like
        # would an object with attributes.
        print(self.param, self["param"])
        print(self.get("param_a"), self.get("param_a", 0))

        # We can also access the optional parameters in the same way, as we have
        # already defined the default values
        print(self.param_a, self["param_a"])


@explicit_serialize
class NonDataclassTask(FiretaskBase):
    required_params = ["param"]
    optional_params = ["param_a"]

    def run_task(self, fw_spec):
        # You can interact with dataclass Firetasks like you would a dict or like
        # would an object with attributes.
        print(self.param, self["param"])
        print(self.get("param_a"), self.get("param_a", 0))

        # However, be aware that self.param_a or self["param_a"] will fail for the non
        # dataclass Firetask as a default value has not been defined. Instead `get`
        # has to be used.
        # print(self.param_a, self["param_a"])  <-- This will not work


task_a = DataclassTask(param="123")
task_b = NonDataclassTask(param="123")
