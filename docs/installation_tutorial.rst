=====================
Installation Tutorial
=====================

This tutorial will guide you through FireWorks installation on the central server and one or more worker nodes. The purpose of this tutorial is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain in things in great detail.

This tutorial can be safely completed from the command line, and requires no programming.

Set up the central server (FireServer)
======================================

The FireWorks central server (FireServer) hosts the FireWorks database. You should choose a central server that has a fixed IP address/hostname. To set up a FireServer:

1. Follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

2. Install `MongoDB <http://www.mongodb.org>`_ on the server.

3. Start MongoDB::

    mongod &

You are now ready to start playing with FireWorks!

Initialize the FireServer
-------------------------

1. Navigate to the FireWorks tutorial directory::

    cd <INSTALL_DIR>/fw_tutorial

where <INSTALL_DIR> is your FireWorks installation directory.
 
2. Initialize the FireWorks database::

    launchpad_run.py initialize <TODAY'S DATE>

where <TODAY'S DATE> is formatted like '2012-12-31' (this is a safeguard to prevent accidentally overwriting an existing database).

.. note:: If you are already curious about the various options that the LaunchPad offers, you can type ``launchpad_run.py -h``.

Add a FireWork to the FireServer database
-----------------------------------------

A FireWork is a workflow. For this tutorial, we will use a FireWork that consists of only a single step. We'll tackle more complex workflows in other tutorials.

1. Staying in the tutorial directory, run the following command::

    launchpad_run.py upsert_fw fw_test.yaml

2. Confirm that the FireWork got added to the database::

    launchpad_run.py get_fw 1

This prints out the FireWork with fw_id=1 (the first FireWork entered into the database).

.. note:: Notice the part of the FireWork that reads: ``echo "howdy, your job launched successfully!" >> howdy.txt"``. When the workflow is run, it will print some text into a file named ``howdy.txt``.

You have now stored a FireWork in the database! It is now ready to be launched.

Launch a Rocket on the FireServer
=================================

A Rocket grabs a FireWork (workflow) from the FireServer database and runs it. Usually, a Rocket would be run on a worker (FireWorker) and through a queuing system. For now, we will run the Rocket on the FireServer itself and without a queue.

1. Navigate to any clean directory. For example::

    cd ~
    mkdir fw_tests
    cd fw_tests
    
2. Execute the following command (once)::

    rocket_run.py
    
The Rocket grabs an available FireWork from the FireServer and runs it.

3. Verify that the desired script ran::

    cat howdy.txt
    
You should see the text ``howdy, your job launched successfully!``

4. Check the status of your FireWork::

    launchpad_run.py get_fw 1
    
You should see additional information indicating that your FireWork was launched.

5. Try launching another rocket (you should get an error)::   

    rocket_run.py

The error indicates that there are no more FireWorks to run. If you wanted, you could go back to the previous section's instructions, add another FireWork, and run ``rocket_run.py`` again in a new directory.

Launch a Rocket on a worker computer (FireWorker)
=================================================

So far, we have added a FireWork (workflow) to the database on the FireServer (central server). We then launched a Rocket that grabbed the FireWork from the database and executed it, all within the same machine.

A more interesting use case of FireWorks is to add FireWorks to the FireServer, but execute them on one or several outside 'worker' computers (FireWorkers), perhaps through a queueing system. We'll step through this use case next.

Install FireWorks on the FireWorker
-----------------------------------

On the worker machine, follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

Reset the FireWorks database
----------------------------

Back at the FireServer,

1. Re-perform the instructions to 'Set up the central server', including re-initializing the database and adding a FireWork.

2. Make sure to keep the FireWorks database running, and do not launch a Rocket yet!

Connect to the FireServer from the FireWorker
---------------------------------------------

The FireWorker needs to know the login information for the FireServer. On the FireWorker,

1. Navigate to the fw_tutorial directory::

    cd <INSTALL_DIR>/fw_tutorial

where <INSTALL_DIR> is your FireWorks installation directory.

2. Modify the file ``launchpad.yaml`` so it points to the credentials of your FireServer. In particular, the ``hostname`` parameter must be changed to the IP address of your FireServer.

3. Confirm that you can query for a FireWork from your FireWorker:

    launchpad_run.py -l launchpad.yaml get_fw 1

This should print out a FireWork.

Configure your FireWorker
-------------------------

Staying in the fw_tutorial directory,

1. Look inside the file ``fworker.yaml`` and change the ``name`` parameter to something that will help you identify the worker, e.g. the name of the worker machine ("hopper").

Launch a Rocket on the FireWorker
--------------------------------

1. Staying in the fw_tutorial directory on your worker node, type::

    rocket_run.py -l launchpad.yaml -w fworker.yaml

This should successfully launch a rocket that finds and runs your FireWork from the central server.

2. Confirm that the FireWork was run::

    launchpad_run.py -l launchpad.yaml get_fw 1

You should notice that the FireWork is listed as being COMPLETED. In addition, the ``name`` parameter under the ``launch_data`` field should match the name that you gave to your FireWorker (worker node).

Launch a Rocket on the FireWorker through a queue =================================================







Start playing with the rocket launcher
--------------------------------------

The rocket launcher creates directories on your file system to contain your runs, and also submits jobs to the queue.

After installing the FireWorks code, the script rocket_launcher_run.py should have been added to your system path. Type this command into your command prompt (from any directory) to ensure that the script is found::

    rocket_launcher_run.py -h

This command should print out more detailed help about the rocket launcher. Take a minute to read it over; it might not all be clear, but we'll step through some of the rocket launcher features next.

Run the rocket launcher in single-shot mode
-------------------------------------------

We are now going to submit a single job to the queue using the rocket launcher. Submitting a job requires interaction with the queue; the details of the interaction are specified through a RocketParams file. For the purposes of this tutorial, we are going to try to use one of the RocketParams files provided with the FireWorks installation.

1. Navigate to a clean testing directory on your worker node.

2. An example of a simple RocketParams file is named rocket_params_pbs_nersc.yaml in the fireworks/user_objects/queue_adapters directory. You can guess that this file is for interaction with PBS queues, both from the name of the file and (if you peek inside) the qa_name parameter which specifies a PBS 'queue adapter'. If you are using a different queuing system than PBS, you should search for a different RocketParams file.

.. important:: If you cannot find an appropriate RocketParams file for your specific queuing system, please contact us for help (see :ref:`contributing-label`). We would like to build support for many queuing systems into the FireWorks package. *TODO: give better instructions on what to do if a plug-and-play RocketParams file is not found.*

4. Copy the appropriate RocketParams file to your current working directory.

5. If you haven't already done so, look inside the RocketParams file to get a sense for the parameters that it sets. As mentioned before, the qa_name parameter is somehow responsible for interaction with your specific queuing system. One thing to note is that 'exe' parameter indicates the executable that will be launched once your job starts running in the queue.

.. important:: Ensure that the 'exe' parameter in the RocketParams file reads: "echo 'howdy, your job launched successfully!' >> howdy.txt"

6. Try submitting a job using the command::

    rocket_launcher_run.py singleshot <JOB_PARAMETERS_FILE>

where the <JOB_PARAMETERS_FILE> points to your RocketParams file, e.g. rocket_params_pbs_nersc.yaml.

7. Ideally, this should have submitted a job to the queue in the current directory. You can read the log files to get more information on what occurred. (The log file location was specified in the RocketParams file)

8. After your queue manager runs your job, you should see the file howdy.txt in the current directory. This indicates that the exe you specified ran correctly.

If you finished this part of the tutorial successfully, congratulations! You've successfully set up a worker node to run FireWorks. You can now continue to test launching jobs in a "rapid-fire" mode.

Run the rocket launcher in rapid-fire mode
------------------------------------------

While launching a single job is nice, a more useful functionality is to maintain a certain number of jobs in the queue. The rocket launcher provides a "rapid-fire" mode that automatically provides this functionality.

To test rapid-fire mode, try the following:

1. Navigate to a clean testing directory on your worker node.

2. Copy the same RocketParams file to this testing directory as you used for single-shot mode.

.. tip:: You don't always have to copy over the RocketParams file. If you'd like, you can keep a single RocketParams file in some known location and just provide the full path to that file when running the rocket_launcher_run.py executable.

3. Try submitting several jobs using the command::

    rocket_launcher_run.py rapidfire -q 3 <JOB_PARAMETERS_FILE>
    
where the <JOB_PARAMETERS_FILE> points to your RocketParams file, e.g. rocket_params_pbs_nersc.yaml.

4. This method should have submitted 3 jobs to the queue at once, all inside of a directory beginning with the tag 'block_'.

5. You can maintain a certain number of jobs in the queue indefinitely by specifying that the rocket launcher loop multiple times (e.g., the example below sets 100 loops)::

    rocket_launcher_run.py rapidfire -q 3 -n 100 <JOB_PARAMETERS_FILE>

.. note:: The script above should maintain 3 jobs in the queue for 100 loops of the rocket launcher. The rocket launcher will sleep for a user-adjustable time after each loop.

.. tip:: the documentation of the rocket launcher contains additional details, as well as the built-in help file obtained by running the rocket launcher with the -h option.
    
Next steps
----------

If you've completed this tutorial, you've successfully set up a worker node that can communicate with the queueing system and submit either a single job or maintain multiple jobs in the queue.

However, so far the jobs have not been very dynamic. The same executable (the one specified in the RocketParams file) has been run for every single job. This is not very useful.

In the next part of the tutorial, we'll set up a central workflow server and add some jobs to it. Then, we'll come back to the workers and walk through how to dynamically run the jobs specified by the workflow server.
