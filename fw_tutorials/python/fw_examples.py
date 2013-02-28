from fireworks.core.firework import FireWork
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket, rapidfire
from fireworks.user_objects.firetasks.script_task import ScriptTask

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 28, 2013'


# All examples assume you have MongoDB running on port 27017!

def setup():
    launchpad = LaunchPad(name='fireworks_test')
    launchpad.reset('', require_password=False)
    return launchpad


def basic_fw_ex():
    # setup
    launchpad = setup()

    # add FireWork
    firetask = ScriptTask.from_str('echo "howdy, your job launched successfully!" >> howdy.txt')
    firework = FireWork(firetask)
    launchpad.add_wf(firework)

    # launch Rocket
    launch_rocket(launchpad)


def rapid_fire_ex():
    # setup
    launchpad = setup()

    # add FireWorks
    firetask = ScriptTask.from_str('echo "howdy, your job launched successfully!" >> howdy.txt')
    fw1 = FireWork(firetask)
    launchpad.add_wf(fw1)

    # re-add multiple times
    fw2 = FireWork(firetask)
    launchpad.add_wf(fw2)
    fw3 = FireWork(firetask)
    launchpad.add_wf(fw3)

    # launch Rocket
    rapidfire(launchpad)

if __name__ == '__main__':
    rapid_fire_ex()


