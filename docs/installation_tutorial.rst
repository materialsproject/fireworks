===============================
FireWorks Installation Tutorial
===============================

This tutorial will guide you through FireWorks installation on the central server and one or more worker nodes. The purpose of this tutorial is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail.

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

    mkdir ~/fw_tests
    cd ~/fw_tests
    
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

7. This should have submitted a job to the queue in the current directory. You can read the log files in this directory to get more information on what occurred. You might also now check the status of your queue to make sure your job appeared.

8. After your queue manager runs your job, you should see the file howdy.txt in the current directory. 

9. If everything ran successfully, congratulations! You just executed a complicated sequence of instructions:

   a. The RocketLauncher submitted a script containing a Rocket to your queue manager
   b. Your queue manager executed the Rocket when resources were ready
   c. The Rocket fetched a FireWork from the FireServer and ran the specification inside
   

Adding more power: using rapid-fire mode
========================================

While launching a single job is nice, a more useful functionality is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. The rocket launcher can be run in a "rapid-fire" mode that provides these features.

Reset the FireWorks database
----------------------------

Back at the FireServer,

1. Re-perform the instructions to 'Set up the central server', including re-initializing the database and adding a FireWork.

2. Add two more (identical) FireWorks to the system::

    launchpad_run.py upsert_fw fw_test.yaml
    launchpad_run.py upsert_fw fw_test.yaml

3. Confirm that you have three FireWorks total::

    launchpad_run.py get_fw_ids
    
You should get back an array containing three FireWork ids.

Unleash rapid-fire mode
-----------------------

Switching to your FireWorker,

1. Navigate to a clean testing directory on the FireWorker::

    mkdir ~/rapidfire_tests
    cd ~/rapidfire_tests
    
2. Copy the your RocketParams file to this testing directory::

    cp <PATH_TO_MY_ROCKET_PARAMS> .

where <PATH_TO_MY_ROCKET_PARAMS> is the path to ``my_rocketparams.yaml`` file that you created in the previous section.

3. Looking inside ``my_rocketparams.yaml``, confirm that the path to my_fworker.yaml and my_launchpad.yaml are still valid. (They should be, unless you moved or deleted these files)

4. Try submitting several jobs using the command::

    rocket_launcher_run.py rapidfire -q 3 my_rocketparams.yaml

   .. important:: The RocketLauncher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

5. This method should have submitted 3 jobs to the queue at once, all inside of a directory beginning with the tag ``block_``. Navigate inside this directory and confirm that you've launched multiple Rockets with a single command!

.. tip:: For more tips on the RocketLauncher, such as how to maintain a certain number of jobs in the queue, check out its built-in help: ``rocketlauncher_run.py rapidfire -h``
    
Next steps
==========

If you've completed this tutorial, your FireServer and a single FireWorker are fully set up and ready for business! If you'd like, you can now configure more FireWorkers. However, you're most likely interested in setting up more complicated and dynamic workflows in the FireServer. We'll cover the basics of workflow creation and execution in the next part of the tutorial.