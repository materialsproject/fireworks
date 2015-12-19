"""
This code is described in the FireTasks tutorial, http://pythonhosted.org/FireWorks/firetask_tutorial.html
"""

from fireworks import Firework, FWorker, LaunchPad
from fireworks.core.rocket_launcher import launch_rocket
from fw_tutorials.firetask.addition_task import AdditionTask

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    # create the Firework consisting of a custom "Addition" task
    firework = Firework(AdditionTask(), spec={"input_array": [1, 2]})

    # store workflow and launch it locally
    launchpad.add_wf(firework)
    launch_rocket(launchpad, FWorker())