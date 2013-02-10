===============================
FireWorks Installation Tutorial
===============================

This tutorial will guide you through FireWorks installation on the central server and one or more worker nodes. The purpose of this tutorial is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail.

This tutorial can be safely completed from the command line, and requires no programming.

Set up the central server (FireServer)
======================================

The FireWorks central server (FireServer) hosts the FireWorks database. You should choose a central server that has a fixed IP address/hostname so that you can connect to it from other machines. To set up a FireServer:

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

This prints out the FireWork with fw_id=1 (the first FireWork entered into the database). Notice the part of the FireWork that reads: ``echo "howdy, your job launched successfully!" >> howdy.txt"``. When the workflow is run, this is the command that will be executed (print some text into a file named ``howdy.txt``).

You have now stored a FireWork in the database! It is now ready to be launched.

Launch a Rocket on the FireServer
=================================

A Rocket fetches a FireWork (workflow) from the FireServer database and runs it. Usually, a Rocket would be run on a separate machine (FireWorker) and through a queuing system. For now, we will run the Rocket on the FireServer itself and without a queue.

1. Navigate to any clean directory. For example::

    mkdir ~/fw_tests
    cd ~/fw_tests
    
2. Execute the following command (once)::

    rocket_run.py
    
The Rocket fetches an available FireWork from the FireServer and runs it.

3. Verify that the desired script ran::

    cat howdy.txt
    
You should see the text ``howdy, your job launched successfully!``

4. Check the status of your FireWork::

    launchpad_run.py get_fw 1
    
You should see additional information indicating that your FireWork was launched.

5. Try launching another rocket (you should get an error)::   

    rocket_run.py

The error ``No FireWorks are ready to run and match query!`` indicates that the Rocket tried to fetch a FireWork from the database, but none could be found. Indeed, we had previously run the only FireWork that was in the database. If you wanted, you could go back, add another FireWork, and run ``rocket_run.py`` again in a new directory.

Launch a Rocket on a worker machine (FireWorker)
=================================================

So far, we have added a FireWork (workflow) to the database on the FireServer (central server). We then launched a Rocket that fetched the FireWork from the database and executed it, all within the same machine.

A more interesting use case of FireWorks is to add FireWorks to the FireServer, but execute them on one or several outside 'worker' machine (FireWorkers), perhaps through a queueing system. We'll next configure a worker machine.

Install FireWorks on the FireWorker
-----------------------------------

On the worker machine, follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

Reset the FireWorks database
----------------------------

1. Back at the FireServer, let's reset our database add a new FireWork::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py upsert_fw fw_test.yaml

Make sure to keep the FireWorks database running, and do not launch a Rocket yet!

Connect to the FireServer from the FireWorker
---------------------------------------------

The FireWorker needs to know the login information for the FireServer. On the FireWorker,

1. Navigate to the tutorial directory::

    cd <INSTALL_DIR>/fw_tutorial/installation

where <INSTALL_DIR> is your FireWorks installation directory.

2. Copy the LaunchPad file to a new name::

    cp launchpad.yaml my_launchpad.yaml
    
3. Modify your ``my_launchpad.yaml`` to contain the credentials of your FireServer. In particular, the ``hostname`` parameter must be changed to the IP address of your FireServer.

3. Confirm that you can access the FireServer from your FireWorker::

    launchpad_run.py -l my_launchpad.yaml get_fw 1

This should print out a FireWork.

Configure your FireWorker
-------------------------

Staying in the installation tutorial directory on the FireWorker,

1. Copy the FireWorker file to a new name::

    cp fworker.yaml my_fworker.yaml

2. Modify your ``my_fworker.yaml`` by changing the ``name`` parameter to something that identifies the worker, e.g. the name of the worker machine ("hopper"). This will help you identify the worker that ran your FireWork later on.

Launch a Rocket on the FireWorker
---------------------------------

1. Staying in the installation tutorial directory on your FireWorker, type::

    rocket_run.py -l my_launchpad.yaml -w my_fworker.yaml

This should successfully launch a rocket that finds and runs your FireWork from the central server.

2. Confirm that the FireWork was run::

    launchpad_run.py -l my_launchpad.yaml get_fw 1

You should notice that the FireWork is listed as being COMPLETED. In addition, the ``name`` parameter under the ``launch_data`` field should match the name that you gave to your FireWorker in ``my_fworker.yaml``.


Launch a Rocket on the FireWorker through a queue
=================================================

If your FireWorker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't want to launch Rockets directly. Instead, you'll submit Rockets through an existing queueing system allocates computer time. The RocketLauncher helps launch Rockets through a queue.

Configure the RocketLauncher
----------------------------

The RocketLauncher needs to know how to communicate with your queue system and the executable to submit to the queue (in our case, a Rocket). These parameters are defined through the RocketParams file.

1. Staying in the installation tutorial directory on your FireWorker, locate an appropriate RocketParams file. The files are usually named ``rocketparams_<QUEUE>.yaml`` where <QUEUE> is the supported queue system.

.. note:: If you cannot find a working RocketParams file for your specific queuing system, please contact us for help! (see :ref:`contributing-label`) Don't be shy, we want to help you get set up.

2. Copy your chosen RocketParams file to a new name::

    cp rocketparams_<QUEUE>.yaml my_rocketparams.yaml
    
3. Open ``my_rocketparams.yaml`` and modify it as follows:

   a. In the part that specifies running ``rocket_run.py``, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine.

   b. On the same line, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine.
   
   c. For the logging_dir parameter, modify the ``path/to/logging`` text to contain the **absolute path** of where you would like FireWorks logs to go. For example, you might create a ``fw_logs`` directory inside your home directory, and point the logging_dir parameter there.
   
   .. note:: Be sure to indicate the full, absolute path name; do not use BASH shortcuts like '.', '..', or '~', and do not indicate a relative path.

4. Try submitting a job using the command::

    rocket_launcher_run.py singleshot my_rocketparams.yaml

7. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

8. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

If everything ran successfully, congratulations! You just executed a complicated sequence of instructions:

   a. The RocketLauncher submitted a script containing a Rocket to your queue manager
   b. Your queue manager executed the Rocket when resources were ready
   c. The Rocket fetched a FireWork from the FireServer and ran the specification inside
   

Adding more power: using rapid-fire mode
========================================

While launching a single job to a queue is nice, a more powerful use case is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. The RocketLauncher can be run in a "rapid-fire" mode that provides these features.

Reset the FireWorks database
----------------------------

1. Back at the FireServer, let's reset our database add **three** new FireWorks::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py upsert_fw fw_test.yaml
    launchpad_run.py upsert_fw fw_test.yaml
    launchpad_run.py upsert_fw fw_test.yaml

2. Confirm that you have three FireWorks total::

    launchpad_run.py get_fw_ids
    
You should get back an array containing three FireWork ids.

Unleash rapid-fire mode
-----------------------

Switching to your FireWorker,

1. Navigate to a clean testing directory on the FireWorker::

    mkdir ~/rapidfire_tests
    cd ~/rapidfire_tests
    
2. Copy your RocketParams file to this testing directory::

    cp <PATH_TO_MY_ROCKET_PARAMS> .

where <PATH_TO_MY_ROCKET_PARAMS> is the path to ``my_rocketparams.yaml`` file that you created in the previous section.

3. Looking inside ``my_rocketparams.yaml``, confirm that the path to my_fworker.yaml and my_launchpad.yaml are still valid. (They should be, unless you moved or deleted these files)

4. Submit several jobs with a single command::

    rocket_launcher_run.py rapidfire -q 3 my_rocketparams.yaml

   .. important:: The RocketLauncher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue. If you had some jobs existing in the queue before running this command, you might need to increase the ``-q`` parameter.
   
5. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command!

.. note:: For more tips on the RocketLauncher, such as how to maintain a certain number of jobs in the queue, read its built-in help: ``rocketlauncher_run.py rapidfire -h``
    
Next steps
==========

If you've completed this tutorial, your FireServer and a single FireWorker are ready for business! If you'd like, you can now configure more FireWorkers. However, you're most likely interested in learning how to define more complicated and dynamic workflows. We'll cover the basics of workflow creation and execution in the next part of the tutorial.
