"""
This code is described in the Dynamic Workflow tutorial, https://materialsproject.github.io/fireworks/dynamic_wf_tutorial.html
"""

from fireworks import ScriptTask
from fireworks.core.firework import Firework, Workflow
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import rapidfire

from fw_tutorials.dynamic_wf.printjob_task import PrintJobTask

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    # create the Workflow that passes job info
    fw1 = Firework([ScriptTask.from_str('echo "This is the first FireWork"')], spec={"_pass_job_info": True}, fw_id=1)
    fw2 = Firework([PrintJobTask()], parents=[fw1], fw_id=2)
    wf = Workflow([fw1, fw2])

    # store workflow and launch it locally
    launchpad.add_wf(wf)
    rapidfire(launchpad)
