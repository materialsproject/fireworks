from fireworks import LaunchPad, explicit_serialize, FiretaskBase, FWAction, Firework, Workflow
from fireworks.core.rocket_launcher import rapidfire

__author__ = 'Anubhav Jain <ajain@lbl.gov>'

"""
A workflow where 2 parent Fireworks (A and B) merge into a common child C.
"""

@explicit_serialize
class TaskA(FiretaskBase):

    def run_task(self, fw_spec):
        print("This is task A")
        return FWAction(update_spec={"param_A": 10})


@explicit_serialize
class TaskB(FiretaskBase):

    def run_task(self, fw_spec):
        print("This is task B")
        return FWAction(update_spec={"param_B": 20})

@explicit_serialize
class TaskC(FiretaskBase):

    def run_task(self, fw_spec):
        print("This is task C.")
        print("Task A gave me: {}".format(fw_spec["param_A"]))
        print("Task B gave me: {}".format(fw_spec["param_B"]))

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    fw_A = Firework([TaskA()])
    fw_B = Firework([TaskB()])
    fw_C = Firework([TaskC()], parents=[fw_A, fw_B])

    # assemble Workflow from FireWorks and their connections by id
    workflow = Workflow([fw_A, fw_B, fw_C])

    # store workflow and launch it locally
    launchpad.add_wf(workflow)
    rapidfire(launchpad)