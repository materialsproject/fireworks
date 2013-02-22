==============================
Launch Rockets through a queue
==============================

If your FireWorker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't want to launch Rockets directly. Instead, you'll submit Rockets through an existing queueing system allocates computer time. The RocketLauncher helps launch Rockets through a queue.

Configure the QueueLauncher
============================

The QueueLauncher needs to know how to communicate with your queue system and the executable to submit to the queue (in our case, a Rocket). These parameters are defined through the RocketParams file.

1. Staying in the ``installation_pt2`` tutorial directory on your FireWorker, locate an appropriate RocketParams file. The files are usually named ``rocketparams_<QUEUE>.yaml`` where <QUEUE> is the supported queue system.

.. note:: If you cannot find a working RocketParams file for your specific queuing system, please contact us for help! (see :ref:`contributing-label`) Don't be shy, we want to help you get set up.

2. Copy your chosen RocketParams file to a new name::

    cp rocketparams_<QUEUE>.yaml my_rocketparams.yaml

3. Open ``my_rocketparams.yaml`` and modify it as follows:

   a. In the part that specifies running ``rocket_run.py``, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine.

   b. On the same line, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine.

   c. For the logging_dir parameter, modify the ``path/to/logging`` text to contain the **absolute path** of where you would like FireWorks logs to go. For example, you might create a ``fw_logs`` directory inside your home directory, and point the logging_dir parameter there.

   .. note:: Be sure to indicate the full, absolute path name; do not use BASH shortcuts like '.', '..', or '~', and do not indicate a relative path.

4. Try submitting a job using the command::

    queue_launcher_run.py singleshot my_rocketparams.yaml

7. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

8. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

If everything ran successfully, congratulations! You just executed a complicated sequence of instructions:

   a. The QueueLauncher submitted a Rocket to your queue manager
   b. Your queue manager executed the Rocket when resources were ready
   c. The Rocket fetched a FireWork from the FireServer and ran the specification inside


Adding more power: using rapid-fire mode
========================================

While launching a single job to a queue is nice, a more powerful use case is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. The QueueLauncher can be run in a "rapid-fire" mode that provides these features.

Reset the FireWorks database
----------------------------

1. Back at the FireServer, let's reset our database add **three** new FireWorks::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_single_fw fw_test.yaml
    launchpad_run.py insert_single_fw fw_test.yaml
    launchpad_run.py insert_single_fw fw_test.yaml

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

    queue_launcher_run.py rapidfire -q 3 my_rocketparams.yaml

   .. important:: The QueueLauncher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue. If you had some jobs existing in the queue before running this command, you might need to increase the ``-q`` parameter.

5. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command!

.. note:: For more tips on the QueueLauncher, such as how to maintain a certain number of jobs in the queue, read its built-in help: ``queue_launcher_run.py rapidfire -h``

Next steps
==========

If you've completed this tutorial, your FireServer and a single FireWorker are ready for business! If you'd like, you can now configure more FireWorkers. However, you're most likely interested in running more complex jobs and creating multi-step workflows. We'll continue the tutorial with how to :doc:`defining jobs using FireTasks </task_tutorial>`.
