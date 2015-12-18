"""
This code is described in the Dynamic Workflow tutorial, http://pythonhosted.org/FireWorks/dynamic_wf_tutorial.html
"""

from fireworks import Firework, FWorker, LaunchPad
from fireworks.core.rocket_launcher import rapidfire
from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    # create the Firework consisting of a custom "Fibonacci" task
    firework = Firework(FibonacciAdderTask(), spec={"smaller": 0, "larger": 1, "stop_point": 100})

    # store workflow and launch it locally
    launchpad.add_wf(firework)
    rapidfire(launchpad, FWorker())

