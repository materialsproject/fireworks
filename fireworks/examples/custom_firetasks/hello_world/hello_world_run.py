from fireworks import LaunchPad, Firework, Workflow
from fireworks.core.rocket_launcher import launch_rocket
from fireworks.examples.custom_firetasks.hello_world.hello_world_task import HelloTask

if __name__ == "__main__":
    # initialize the database
    lp = LaunchPad()  # you might need to modify the connection settings here
    # lp.reset()  # uncomment this line and set the appropriate parameters if you want to reset the database

    # create the workflow and store it in the database
    my_fw = Firework([HelloTask()])
    my_wflow = Workflow.from_Firework(my_fw)
    lp.add_wf(my_wflow)

    # run the workflow
    launch_rocket(lp)