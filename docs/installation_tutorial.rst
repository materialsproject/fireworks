==========================================
Installation Tutorial (part 1: the Server)
==========================================

This tutorial will guide you through FireWorks installation on the central server. The purpose of this tutorial is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail.

This tutorial can be safely completed from the command line, and requires no programming.

Set up the central server (FireServer)
======================================

The FireWorks central server (FireServer) hosts the FireWorks database. For production, you should choose a central server that has a fixed IP address/hostname so that you can connect to it from other machines reliably. For initially testing the installation, it should be OK to use a laptop or workstation with a dynamic IP. To set up a FireServer:

#. Follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

#. Install `MongoDB <http://www.mongodb.org>`_ on the server.

#. Start MongoDB::

    mongod &

You are now ready to start playing with FireWorks!

.. note:: If MongoDB is outputting a lot of text, you might want to start it in a dedicated Terminal window or use the ``--quiet`` option. In addition, if you are running it on a shared machine, make sure that the ``--dbpath`` variable is set to a directory that you can access.

Reset the FireServer
--------------------

#. Navigate to the FireWorks installation tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/installation

   where <INSTALL_DIR> is your FireWorks installation directory.
 
#. Reset the FireWorks database (the LaunchPad)::

    lpad reset <TODAY'S DATE>

   where <TODAY'S DATE> is formatted like '2012-01-31' (this serves as a safeguard to accidentally overwriting an existing database). You should receive confirmation that the LaunchPad was reset.

.. note:: If you are already curious about the various options that the LaunchPad offers, you can type ``lpad -h``. The ``-h`` help option is available for all of the scripts in FireWorks.

Add a FireWork to the FireServer database
-----------------------------------------

A FireWork contains the computing job to be performed. For this tutorial, we will use a FireWork that consists of only a single step. We'll tackle more complex workflows in other tutorials.

#. Staying in the tutorial directory, run the following command::

    lpad add fw_test.yaml

   .. note:: You can look inside the file ``fw_test.yaml`` with a text editor if you'd like; we'll explain its components shortly.

#. You should have received confirmation that the FireWork got added. You can query the database for this FireWork as follows::

    lpad get_fw 1

   This prints out the FireWork with ``fw_id`` = 1 (the first FireWork entered into the database)::

    {
        "fw_id": 1,
        "spec": {
            "_tasks": [
                {
                    "_fw_name": "Script Task",
                    "script": "echo \"howdy, your job launched successfully!\" >> howdy.txt"
                }
            ]
        },
        "created_on": "2013-04-05T22:53:24.552834",
        "state": "READY"
    }

#. Some of the FireWork is straightforward, but a few sections deserve further explanation:

* The **spec** of the FireWork contains *all* the information about what job to run and the parameters needed to run it.
* Within the **spec**, the **_tasks** section tells you what jobs will run. The ``Script Task`` is a particular type of task that runs commands through the shell. Other sections of the **spec** can be also be defined, but for now we'll stick to just **_tasks**. Later on, we'll describe how to run multiple **_tasks** or customized **_tasks**.
* This FireWork runs the script ``echo "howdy, your job launched successfully!" >> howdy.txt"``, which prints text to a file named ``howdy.txt``.
* The **state** of *READY* means the FireWork is ready to be run.

You have now stored a FireWork in the LaunchPad, and it's ready to run!

.. note:: More details on using the ``ScriptTask`` are presented in the later tutorials.

Launch a Rocket on the FireServer
=================================

A Rocket fetches a FireWork from the LaunchPad and runs it. A Rocket might be run on a separate machine (FireWorker) or through a queuing system. For now, we will run the Rocket on the FireServer itself and without a queue.

1. We can launch Rockets using the Rocket Launcher. Execute the following command (once)::

    rlaunch singleshot
    
   The Rocket fetches an available FireWork from the FireServer and runs it.

#. Verify that the desired task ran::

    cat howdy.txt
    
   You should see the text: ``howdy, your job launched successfully!``

.. note:: In addition to ``howdy.txt``, you should also see a file called ``FW.json``. This contains a JSON representation of the FireWork that the Rocket ran and can be useful later for tracking down a launch or debugging.

#. Check the status of your FireWork::

    lpad get_fw 1
    
   You will now see lots of information about your Rocket launch, such as the time and directory of the launch. A lot of it is probably unclear, but you should notice that the state of the FireWork is now ``COMPLETED``.

#. Try launching another rocket (you should get an error)::

    rlaunch singleshot

   The error ``No FireWorks are ready to run and match query!`` indicates that the Rocket tried to fetch a FireWork from the database, but none could be found. Indeed, we had previously run the only FireWork that was in the database.

Launch many Rockets (rapidfire mode)
====================================

If you just want to run many jobs on the central server itself, the simplest way is to run the Rocket Launcher in "rapidfire mode". Let's try this feature:

#. Staying in the same directory, clean up your output files::

    rm FW.json howdy.txt

#. Let's add 3 identical FireWorks::

    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml

#. Confirm that the three FireWorks got added to the database, in addition to the one from before (4 total)::

    lpad get_fw_ids

#. We could also just get the ``fw_id`` of jobs that are ready to run (our 3 new FireWorks)::

    lpad get_fw_ids -q '{"state":"READY"}'

#. Let's run launch Rockets in "rapidfire" mode, which will keep repeating until we run out of FireWorks to run::

    rlaunch rapidfire

#. You should see three directories starting with the tag ``launcher_``. Inside each of these directories, you'll find the results of one of your FireWorks (a file named ``howdy.txt``)::

    cat launch*/howdy.txt

Running FireWorks automatically
===============================

We can set our Rocket Launcher to continuously look for new FireWorks to run. Let's try this feature.

#. Staying in the same directory, clean up your previous output files::

    rm -r launcher_*

#. Start the Rocket Launcher so that it looks for new FireWorks every 10 seconds::

    rlaunch rapidfire --nlaunches infinite --sleep 10

#. **In a new terminal window**, navigate back to your working directory containing ``fw_test.yaml``. Let's insert two FireWorks::

    lpad add fw_test.yaml
    lpad add fw_test.yaml

#. After a few seconds, the Rocket Launcher should have picked up the new jobs and run them. Confirm this is the case::

    cat launch*/howdy.txt

   You should see two outputs, one for each FireWork we inserted.

#. You can continue adding FireWorks as desired; the Rocket Launcher will run them automatically and create a new directory for each job. When you are finished, you can exit out of the Rocket Launcher terminal window and clean up your working directory.

#. As with all FireWorks scripts, you can run the built-in help for more information::

    rlaunch -h
    rlaunch singleshot -h
    rlaunch rapidfire -h

What just happened?
===================

It's important to understand that when you add a FireWork to the LaunchPad using the ``lpad`` script, the job just sits in the database and waits. The LaunchPad does not submit jobs to a computing resource when a new FireWork is added to the LaunchPad. Rather, a computing resource must *request* a computing task by running the Rocket Launcher. By running the Rocket Launcher from different locations, you can have different computing resources run your jobs.

When we ran the Rocket Launcher in rapid-fire mode, the Rocket Launcher requests a new task from the LaunchPad immediately after completing its current task. It stops requesting tasks when none are left in the database. It might *appear* like the LaunchPad is feeding FireWorks to the Rocket Launcher, but in reality the Rocket Launcher must initiate the request for a FireWork. You might have noticed this when we ran the Rocket Launcher in infinite mode with a sleep time of 10. In this mode, we are requesting a new task every 10 seconds after completing the previous set of tasks. When you add a new FireWork to the LaunchPad, it does not start running automatically. We must wait up to 10 seconds for the Rocket Launcher to request it!


Next steps
==========

At this point, you've successfully stored a simple job in a database and run it later on command. You even executed multiple jobs with a single command: ``rlaunch rapidfire``, and looked for new jobs automatically using the **infinite** Rocket Launcher. This should give a basic feeling of how you can automate many jobs using FireWorks.

Your next step depends on your application. If you want to stick with our simple script and automate it on at least one worker node, forge on to the next tutorial in the series: :doc:`Installation Tutorial (part 2: the Worker) </installation_tutorial_pt2>`. This is the path we recommend for most users, except in the simplest of circumstances in which you only want to run jobs on the FireServer itself.

If you are only running on the FireServer, you can skip ahead to :doc:`defining jobs using FireTasks </firetask_tutorial>`.