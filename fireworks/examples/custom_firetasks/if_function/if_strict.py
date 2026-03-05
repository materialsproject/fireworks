"""implementation of a strict if function."""

from fireworks import FiretaskBase, Firework, FWAction, LaunchPad, Workflow, explicit_serialize
from fireworks.core.rocket_launcher import launch_rocket
from fireworks.fw_config import LAUNCHPAD_LOC


@explicit_serialize
class SummationTask(FiretaskBase):
    required_params = ["inputs", "output"]

    def run_task(self, fw_spec):
        inp = [fw_spec[i] for i in self["inputs"]]
        return FWAction(update_spec={self["output"]: sum(inp)})


@explicit_serialize
class IfTask(FiretaskBase):
    required_params = ["condition", "input_1", "input_2", "output"]

    def run_task(self, fw_spec):
        ret = fw_spec[self["input_1"]] if fw_spec[self["condition"]] else fw_spec[self["input_2"]]
        return FWAction(update_spec={self["output"]: ret})


if __name__ == "__main__":
    fw_0 = Firework(tasks=SummationTask(inputs=["a"], output="a"), spec={"a": 1})
    fw_1 = Firework(tasks=SummationTask(inputs=["b"], output="b"), spec={"b": 2})
    fw_2 = Firework(tasks=IfTask(condition="x", input_1="a", input_2="b", output="c"), spec={"x": True})
    wf = Workflow(fireworks=[fw_0, fw_1, fw_2], links_dict={fw_1: [fw_2], fw_0: [fw_2]})
    lpad = LaunchPad.from_file(LAUNCHPAD_LOC)
    lpad.add_wf(wf)

    run = True
    while run:
        run = launch_rocket(lpad)

    launch_rocket(lpad)
    launch_rocket(lpad)
    launch_rocket(lpad)

    launch_id = lpad.get_fw_by_id(fw_2.fw_id).launches[-1].launch_id
    result = lpad.launches.find_one({"launch_id": launch_id})["action"]["update_spec"]
    print(result)
    assert result == {"c": 1}
