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

1. Navigate to the FireWorks installation tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/installation

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

1. Navigate to the tutorial directory::

    cd <INSTALL_DIR>/fw_tutorial/installation

where <INSTALL_DIR> is your FireWorks installation directory.

2. Copy the LaunchPad file to a new name::

    cp launchpad.yaml my_launchpad.yaml
    
3. Modify your ``my_launchpad.yaml`` so it points to the credentials of your FireServer. In particular, the ``hostname`` parameter must be changed to the IP address of your FireServer.

3. Confirm that you can query for a FireWork from your FireWorker:

    launchpad_run.py -l my_launchpad.yaml get_fw 1

This should print out a FireWork.

Configure your FireWorker
-------------------------

Staying in the tutorial directory,

1. Copy the FireWorker file to a new name::

    cp fworker.yaml my_fworker.yaml

2. Modify your ``my_fworker.yaml`` by changing the ``name`` parameter to something that will help you identify the worker, e.g. the name of the worker machine ("hopper").

Launch a Rocket on the FireWorker
---------------------------------

1. Staying in the tutorial directory on your FireWorker, type::

    rocket_run.py -l my_launchpad.yaml -w my_fworker.yaml

This should successfully launch a rocket that finds and runs your FireWork from the central server.

2. Confirm that the FireWork was run::

    launchpad_run.py -l my_launchpad.yaml get_fw 1

You should notice that the FireWork is listed as being COMPLETED. In addition, the ``name`` parameter under the ``launch_data`` field should match the name that you gave to your FireWorker (worker node).


Launch a Rocket on the FireWorker through a queue
=================================================

If your worker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't want to launch Rockets directly on the worker. Instead, you'll need to submit Rockets through a queueing system allocates computer time.

In this section, we'll introduce the RocketLauncher, which helps launch Rockets through a queue and organizes launches into separate directories.

Configure the RocketLauncher
----------------------------

The RocketLauncher needs to know how to communicate with your queue system and the executable to submit to the queue (in our case, a Rocket). These parameters defined through the RocketParams file.

1. Staying in the tutorial directory on your FireWorker, locate an appropriate RocketParams file. The files are usually named ``rocketparams_<QUEUE>`` where <QUEUE> is the supported queue system.

.. note:: If you cannot find a working RocketParams file for your specific queuing system, please contact us for help (see :ref:`contributing-label`)! We would like to build support for many queuing systems into the FireWorks package, and generally respond quickly to such requests.

2. Copy your RocketParams file to a new name::

    cp rocketparams_<QUEUE> my_rocketparams.yaml
    
3. Open ``my_rocketparams.yaml`` and modify it as follows:

   a. In the part where it specifies running rocket_run.py, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine.

   b. In the part where it specifies running rocket_run.py, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine.
   
   .. note:: Be sure not to indicate relative paths, and do not use BASH shortcuts like '~'.

4. Try submitting a job using the command::

    rocket_launcher_run.py singleshot my_rocketparams.yaml

7. This should have submitted a job to the queue in the current directory. You can read the log files in this directory to get more information on what occurred.

8. After your queue manager runs your job, you should see the file howdy.txt in the current directory. This indicates that a Rocket was successfully launched through the queue.

Run the rocket launcher in rapid-fire mode
------------------------------------------

While launching a single job is nice, a more useful functionality is to maintain a certain number of jobs in the queue. The rocket launcher provides a "rapid-fire" mode that automatically provides this functionality.

To test rapid-fire mode, try the following:

1. Navigate to a clean testing directory on your worker node.

2. Copy the same RocketParams file to this testing directory as you used for single-shot mode.

.. tip:: You don't always have to copy over the RocketParams file. If you'd like, you can keep a single RocketParams file in some known location and just provide the full path to that file when running the rocket_launcher_run.py executable.

3. Try submitting several jobs using the command::

    rocket_launcher_run.py rapidfire -q 3 <ROCKET_PARAMS_FILE>
    
where the <ROCKET_PARAMS_FILE> points to your RocketParams file, e.g. rocket_params_pbs_nersc.yaml.

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
