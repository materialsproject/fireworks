from fireworks.core.firework import Firework, Workflow
from fireworks.core.fworker import FWorker
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
    launchpad = LaunchPad(name='fireworks_test', strm_lvl='ERROR')
    launchpad.reset('', require_password=False)
    return launchpad


def basic_fw_ex():
    print('--- BASIC FIREWORK EXAMPLE ---')

    # setup
    launchpad = setup()

    # add Firework
    firetask = ScriptTask.from_str('echo "howdy, your job launched successfully!"')
    firework = Firework(firetask)
    launchpad.add_wf(firework)

    # launch Rocket
    launch_rocket(launchpad, FWorker())


def rapid_fire_ex():
    print('--- RAPIDFIRE EXAMPLE ---')

    # setup
    launchpad = setup()

    # add FireWorks
    firetask = ScriptTask.from_str('echo "howdy, your job launched successfully!"')
    fw1 = Firework(firetask)
    launchpad.add_wf(fw1)

    # re-add multiple times
    fw2 = Firework(firetask)
    launchpad.add_wf(fw2)
    fw3 = Firework(firetask)
    launchpad.add_wf(fw3)

    # launch Rocket
    rapidfire(launchpad, FWorker())


def multiple_tasks_ex():
    print('--- MULTIPLE FIRETASKS EXAMPLE ---')

    # setup
    launchpad = setup()

    # add FireWorks
    firetask1 = ScriptTask.from_str('echo "This is TASK #1"')
    firetask2 = ScriptTask.from_str('echo "This is TASK #2"')
    firetask3 = ScriptTask.from_str('echo "This is TASK #3"')
    fw = Firework([firetask1, firetask2, firetask3])
    launchpad.add_wf(fw)

    # launch Rocket
    rapidfire(launchpad, FWorker())


def basic_wf_ex():
    print('--- BASIC WORKFLOW EXAMPLE ---')

    # setup
    launchpad = setup()

    # add FireWorks
    task1 = ScriptTask.from_str('echo "Ingrid is the CEO."')
    task2 = ScriptTask.from_str('echo "Jill is a manager."')
    task3 = ScriptTask.from_str('echo "Jack is a manager."')
    task4 = ScriptTask.from_str('echo "Kip is an intern."')

    fw1 = Firework(task1, fw_id=1)
    fw2 = Firework(task2, fw_id=2)
    fw3 = Firework(task3, fw_id=3)
    fw4 = Firework(task4, fw_id=4)

    # make workflow
    workflow = Workflow([fw1, fw2, fw3, fw4], {1: [2, 3], 2: [4], 3: [4]})
    launchpad.add_wf(workflow)

    # launch Rocket
    rapidfire(launchpad, FWorker())

if __name__ == '__main__':
    basic_fw_ex()
    rapid_fire_ex()
    multiple_tasks_ex()
    basic_wf_ex()


