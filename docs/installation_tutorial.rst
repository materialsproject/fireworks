==========================================
Installation Tutorial (part 1: the Server)
==========================================

This tutorial will guide you through FireWorks installation on the central server. The purpose of this tutorial is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail.

This tutorial can be safely completed from the command line, and requires no programming.

Set up the central server (FireServer)
======================================

The FireWorks central server (FireServer) hosts the FireWorks database. For production, you should choose a central server that has a fixed IP address/hostname so that you can connect to it from other machines reliably. For initially testing the installation, it should be OK to use a laptop or workstation with a dynamic IP. To set up a FireServer:

1. Follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

2. Install `MongoDB <http://www.mongodb.org>`_ on the server.

3. Start MongoDB::

    mongod &

You are now ready to start playing with FireWorks!

Initialize the FireServer
-------------------------

1. Navigate to the FireWorks installation tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/installation

where <INSTALL_DIR> is your FireWorks installation directory.
 
2. Initialize the FireWorks database::

    launchpad_run.py initialize <TODAY'S DATE>

where <TODAY'S DATE> is formatted like '2012-12-31' (this serves as a safeguard to accidentally overwriting an existing database).

.. note:: If you are already curious about the various options that the LaunchPad offers, you can type ``launchpad_run.py -h``.

Add a FireWork to the FireServer database
-----------------------------------------

A FireWork is a computing job. For this tutorial, we will use a FireWork that consists of only a single step. We'll tackle more complex workflows in other tutorials.

1. Staying in the tutorial directory, run the following command::

    launchpad_run.py insert_single_fw fw_test.yaml

2. Confirm that the FireWork got added to the database::

    launchpad_run.py get_fw 1

This prints out the FireWork with ``fw_id`` = 1 (the first FireWork entered into the database)::

 {
    "fw_id": 1,
    "launch_data": [],
    "spec": {
        "_tasks": [
            {
                "_fw_name": "Subprocess Task",
                "parameters": {
                    "use_shell": true,
                    "script": "echo \"howdy, your job launched successfully!\" >> howdy.txt"
                }
            }
        ]
    },
    "state": "READY"
}

Our ``fw_test.yaml`` file had specified a negative ``fw_id`` of -1; a negative ``fw_id`` means that the database will assign the id for us, starting from ``fw_id`` = 1.

Notice the part of the FireWork that reads: ``echo "howdy, your job launched successfully!" >> howdy.txt"``. When the job is run, this is the command that will be executed (print some text into a file named ``howdy.txt``). The ``use_shell`` parameter indicates that the command will be interpreted through the shell.

You have now stored a FireWork in the database! It is now ready to be launched (state = ``READY``).

.. note:: More details on using the ``SubProcessTask`` are presented in the later tutorials.

Launch a Rocket on the FireServer
=================================

A Rocket fetches a FireWork from the FireServer database and runs it. A Rocket might be run on a separate machine (FireWorker) and through a queuing system. For now, we will run the Rocket on the FireServer itself and without a queue.

1. Navigate to any clean directory. For example::

    mkdir ~/fw_tests
    cd ~/fw_tests
    
2. Execute the following command (once)::

    rocket_run.py
    
The Rocket fetches an available FireWork from the FireServer and runs it.

3. Verify that the desired task ran::

    cat howdy.txt
    
You should see the text: ``howdy, your job launched successfully!``

.. note:: In addition to ``howdy.txt``, you should also see a file called ``fw.json``. This contains a JSON representation of the FireWork that the Rocket ran.

4. Check the status of your FireWork::

    launchpad_run.py get_fw 1
    
You will now see lots of information about your Rocket launch, such as the time and directory of the launch. You should also notice that the state of the FireWork is now ``COMPLETED``.

5. Try launching another rocket (you should get an error)::   

    rocket_run.py

The error ``No FireWorks are ready to run and match query!`` indicates that the Rocket tried to fetch a FireWork from the database, but none could be found. Indeed, we had previously run the only FireWork that was in the database.

Launch many Rockets (loop mode)
=================================

If you just want to run lots of Rockets on the central server itself, the simplest way is to run in "loop mode". Let's try this feature:

1. Staying in your working directory from last time, clean up your output files::

    rm fw.json howdy.txt

2. Let's reset the database and insert 3 identical FireWorks::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_single_fw fw_test.yaml
    launchpad_run.py insert_single_fw fw_test.yaml
    launchpad_run.py insert_single_fw fw_test.yaml

3. Confirm that the three FireWorks got added to the database::

    launchpad_run.py get_fw_ids

4. Let's run launch Rockets in "loop" mode, which will keep repeating until we run out of FireWorks and get the ``No FireWorks are ready to run and match query!`` error::

    rocket_run.py --loop

You should see three directories starting with the tag ``launcher_``. Inside each of these directories, you'll find the results of one of your FireWorks.

5. Finally, let's check the launch state of your third FireWork::

    launchpad_run.py get_fw 3

You'll see the launch information on that FireWork, including the directory where it ran.

Next steps
==========

At this point, you've successfully stored a simple job in a database and run it later on command. You even executed multiple jobs with a single command: ``rocket_run.py --loop``. This should give a basic feeling of how you can automate many jobs with FireWorks. It might be a good time to get a snack!

Your next step depends on your application. If you want to stick with our simple script and automate it on at least one worker node (perhaps through a queuing system), forge on to the next tutorial in the series: :doc:`Installation (part 2) </installation_tutorial_pt2>`. This is the path we recommend for most users, except in the simplest of circumstances in which you don't expect to ever have any worker nodes.

If you don't want to set up worker nodes and instead want to learn how more complex jobs are defined, you can skip ahead to :doc:`defining jobs using FireTasks </firetask_tutorial>`.