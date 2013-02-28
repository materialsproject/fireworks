==============================
Launch Rockets through a queue
==============================

If your FireWorker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't be able to launch Rockets directly. Instead, you'll submit Rockets through an existing queueing system that allocates computer time.


Launch a single job through a queue
===================================

To get warmed up, let's set things up so we can launch a single Rocket through a queueing system. The Queue Launcher helps launch Rockets through a queue.

Configure the Queue Launcher
---------------------------

The Queue Launcher needs to know how to communicate with your queue system and the executable to submit to the queue (in our case, a Rocket). These parameters are defined through a QueueParams file.

1. Move to the ``queue`` tutorial directory on your FireWorker::

    cd <INSTALL_DIR>/fw_tutorials/queue

2. Locate an appropriate QueueParams file. The files are usually named ``queueparams_<QUEUE>.yaml`` where ``<QUEUE>`` is the supported queue system.

.. note:: If you cannot find a working QueueParams file for your specific queuing system, please contact us for help! (see :ref:`contributing-label`) We would like to support more queueing systems in FireWorks.

3. Copy your chosen QueueParams file to a new name::

    cp queueparams_<QUEUE>.yaml my_qp.yaml

4. Open ``my_qp.yaml`` and modify it as follows:

   a. In the part that specifies running ``rlauncher_run.py``, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine. If you completed the previous tutorial, this is probably: ``<INSTALL_DIR>/fw_tutorials/installation_pt2/my_fworker.yaml``

   b. On the same line, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine. This is probably: ``<INSTALL_DIR>/fw_tutorials/installation_pt2/my_launchpad.yaml``

   c. For the logging_dir parameter, modify the ``path/to/logging`` text to contain the **absolute path** of where you would like FireWorks logs to go. For example, you might create a ``fw_logs`` directory inside your home directory, and point the logging_dir parameter there.

   .. note:: Be sure to indicate the full, absolute path name; do not use BASH shortcuts like '.', '..', or '~', and do not indicate a relative path. (also, do not pass Go!)

Add some FireWorks
------------------

Let's reset our database and add a new FireWork, all from our FireWorker this time::

    lp_run.py -l <PATH_TO_LAUNCHPAD> reset <TODAY'S DATE>
    lp_run.py -l <PATH_TO_LAUNCHPAD> add_wf fw_test.yaml

where ``<PATH_TO_LAUNCHPAD>`` is the location of your ``my_launchpad.yaml`` file.

Submit a job
------------

1. Try submitting a job using the command::

    qlauncher_run.py singleshot my_qp.yaml

2. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

3. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

If everything ran successfully, congratulations! You just executed a complicated sequence of instructions:

   a. The Queue Launcher submitted a Rocket to your queue manager
   b. Your queue manager executed the Rocket when resources were ready
   c. The Rocket fetched a FireWork from the FireServer and ran the specification inside


Adding more power: using rapid-fire mode
========================================

While launching a single job to a queue is nice, a more powerful use case is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. Like the Rocket Launcher, the Queue Launcher can be run in a "rapid-fire" mode that provides these features.

Add some FireWorks
------------------

Let's reset our database and add three new FireWorks, all from our FireWorker::

    lp_run.py -l <PATH_TO_LAUNCHPAD> reset <TODAY'S DATE>
    lp_run.py -l <PATH_TO_LAUNCHPAD> add_wf fw_test.yaml
    lp_run.py -l <PATH_TO_LAUNCHPAD> add_wf fw_test.yaml
    lp_run.py -l <PATH_TO_LAUNCHPAD> add_wf fw_test.yaml

where ``<PATH_TO_LAUNCHPAD>`` is the location of your ``my_launchpad.yaml`` file.

Unleash rapid-fire mode
-----------------------

1. Navigate to a clean testing directory on the FireWorker::

    mkdir ~/rapidfire_tests
    cd ~/rapidfire_tests

2. Copy your QueueParams file to this testing directory::

    cp <PATH_TO_MY_QUEUE_PARAMS> .

where <PATH_TO_MY_QUEUE_PARAMS> is the path to ``my_qp.yaml`` file that you created in the previous section.

3. Looking inside ``my_qp.yaml``, confirm that the path to my_fworker.yaml and my_launchpad.yaml are still valid. (They should be, unless you moved or deleted these files)

4. Submit several jobs with a single command::

    qlauncher_run.py rapidfire -q 3 my_qp.yaml

   .. important:: The Queue Launcher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue. If you had some jobs existing in the queue before running this command, you might need to increase the ``-q`` parameter.

5. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command!

.. note:: For more tips on the Queue Launcher, such as how to maintain a certain number of jobs in the queue, read its built-in help: ``qlauncher_run.py rapidfire -h``

Next steps
==========

If you've completed this tutorial, your FireServer and a single FireWorker are ready for business! If you'd like, you can now configure more FireWorkers. However, you're most likely interested in running more complex jobs and creating multi-step workflows. We'll continue the tutorial with :doc:`defining jobs using FireTasks </firetask_tutorial>`.