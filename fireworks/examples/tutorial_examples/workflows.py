"""
This code is described in the Workflow tutorial, http://pythonhosted.org/FireWorks/workflow_tutorial.html
"""

from fireworks import Firework, Workflow, FWorker, LaunchPad, ScriptTask
from fireworks.core.rocket_launcher import rapidfire

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    # define four individual FireWorks used in the Workflow
    task1 = ScriptTask.from_str('echo "Ingrid is the CEO."')
    task2 = ScriptTask.from_str('echo "Jill is a manager."')
    task3 = ScriptTask.from_str('echo "Jack is a manager."')
    task4 = ScriptTask.from_str('echo "Kip is an intern."')

    fw1 = Firework(task1)
    fw2 = Firework(task2)
    fw3 = Firework(task3)
    fw4 = Firework(task4)

    # assemble Workflow from FireWorks and their connections by id
    workflow = Workflow([fw1, fw2, fw3, fw4], {fw1: [fw2, fw3], fw2: [fw4], fw3: [fw4]})

    # store workflow and launch it locally
    launchpad.add_wf(workflow)
    rapidfire(launchpad, FWorker())
