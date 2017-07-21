"""
This code is described in the Introductory tutorial, https://materialsproject.github.io/fireworks/introduction.html
"""

from fireworks import Firework, LaunchPad, ScriptTask
from fireworks.core.rocket_launcher import launch_rocket

if __name__ == "__main__":
    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    # launchpad.reset('', require_password=False)

    # create the Firework consisting of a single task
    firetask = ScriptTask.from_str('echo "howdy, your job launched successfully!"')
    firework = Firework(firetask)

    # store workflow and launch it locally
    launchpad.add_wf(firework)
    launch_rocket(launchpad)