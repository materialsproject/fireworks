==============================
Launch Rockets through a queue
==============================

If your FireWorker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't be able to launch Rockets directly. Instead, you'll submit Rockets through an existing queueing system that allocates computer resources.

The simplest way to submit jobs through a queue is to submit scripts to your queue manager that run ``rlauncher_run.py``. This method is just like typing ``rlauncher_run.py`` into a Terminal window like in the core tutorials, except that now we are submitting a queue script that does the typing for us (it's very low-tech!). In particular, FireWorks is *completely unaware* that you are running through a queue!

The jobs we will submit to the queue are basically placeholder jobs that are asleep until the job starts running. When the job is actually assigned computer resources and runs, the script "wakes" up and figures out what FireWork to run.

The advantage of this low-tech system is that it is quite durable; if your queue system goes down or you delete a job from the queue, there are zero repercussions. You don't have to tell FireWorks to run those jobs somewhere else, because FireWorks never knew about your queue in the first place. In addition, if you are running on multiple machines and the queue becomes backlogged on one of them, it does not matter at all. Your job stuck in the queue is not preventing high-priority jobs from running on other machines.

There are also some disadvantages to this simple system, and we'll discuss a more advanced system in which FireWorks is aware of your queue in a future tutorial. However, we suggest that you get things working simply first.

Launch a single job through a queue
===================================

To get warmed up, let's set things up a *Queue Launcher* to launch a single Rocket through a queueing system.

Configure the Queue Launcher
---------------------------

The Queue Launcher needs to know how to communicate with your queue system and the executable to submit to the queue (in our case, a Rocket). These parameters are defined through a QueueParams file.

1. Move to the ``queue`` tutorial directory on your FireWorker::

    cd <INSTALL_DIR>/fw_tutorials/queue

#. Locate an appropriate QueueParams file. The files are usually named ``queueparams_<QUEUE>.yaml`` where ``<QUEUE>`` is the supported queue system.

.. note:: If you cannot find a working QueueParams file for your specific queuing system, please contact us for help! (see :ref:`contributing-label`) We would like to support more queueing systems in FireWorks.

#. Copy your chosen QueueParams file to a new name::

    cp queueparams_<QUEUE>.yaml my_qp.yaml

#. Navigate to clean working directory on the FireWorker. For example::

    mkdir ~/queue_tests
    cd ~/queue_tests

#. Copy over your queue file and the test FW to this directory::

    cp <INSTALL_DIR>/fw_tutorials/queue/my_qp.yaml .
    cp <INSTALL_DIR>/fw_tutorials/queue/fw_test.yaml .

#. Copy over your LaunchPad and FireWorker files from the second installation tutorial::

    cp <INSTALL_DIR>/fw_tutorials/installation_pt2/my_fworker.yaml .
    cp <INSTALL_DIR>/fw_tutorials/installation_pt2/my_launchpad.yaml .

   .. note:: If you do not have these files, please go back and regenerate them according to the instructions :doc:`here </installation_tutorial_pt2>`.

#. Open ``my_qp.yaml`` and modify it as follows:

   a. In the part that specifies running ``rlauncher_run.py``, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine.

   b. On the same line, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine.

   c. For the logging_dir parameter, modify the ``path/to/logging`` text to contain the **absolute path** of where you would like FireWorks logs to go. For example, you might create a ``fw_logs`` directory inside your home directory, and point the logging_dir parameter there.

   .. note:: Be sure to indicate the full, absolute path name; do not use BASH shortcuts like '.', '..', or '~', and do not indicate a relative path.

You are now ready to begin!

Add some FireWorks
------------------

Staying in your testing directory, let's reset our database and add a new FireWork, all from our FireWorker::

    lp_run.py -l my_launchpad.yaml reset <TODAY'S DATE>
    lp_run.py -l my_launchpad.yaml add fw_test.yaml

Submit a job
------------

1. Try submitting a job using the command::

    qlauncher_run.py -l my_launchpad.yaml -w my_fworker.yaml singleshot my_qp.yaml

   .. note:: The LaunchPad and FireWorker are not always used when running the Queue Launcher (this is the case here). But, it is good practice to always specify them.

#. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

#. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

   .. note:: In some cases, firewall issues on shared resources prevent your compute node from accessing your FireServer database. If you think this might be responsible for your problem, you might try to submit an interactive job to your queue. Once on the compute node, you can try connecting to your FireServer database through Mongo: ``mongo <hostname>:<port>/fireworks -u <USERNAME> -p <PASSWORD>``. (You could also try running ``lp_run.py -l my_launchpad.yaml get_fw 1`` to test the DB connection, but make sure you do this from a compute node). If you cannot connect to the FireServer database from your compute node, you might contact a system administrator for assistance.

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

    lp_run.py -l my_launchpad.yaml reset <TODAY'S DATE>
    lp_run.py -l my_launchpad.yaml add fw_test.yaml
    lp_run.py -l my_launchpad.yaml add fw_test.yaml
    lp_run.py -l my_launchpad.yaml add fw_test.yaml

Unleash rapid-fire mode
-----------------------

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Submit several jobs with a single command::

    qlauncher_run.py -l my_launchpad.yaml -w my_fworker.yaml rapidfire -q 3 my_qp.yaml

   .. note:: You may have noticed that the paths to ``my_fworker.yaml`` and ``my_launchpad.yaml`` are needed in two places. The first place is when specifying the ``-l`` and ``-w`` arguments to ``qlauncher_run.py``.The second place is inside the ``my_qp.yaml`` file.  The locations when specifying arguments to ``qlauncher_run.py`` are read by the head node during submission of your jobs to the queue manager. The locations inside ``my_qp.yaml``are read by the compute nodes that run your job. These locations can be different or the same, but we suggest that they be the same unless your compute nodes cannot access the same filesystem as your head nodes.

   .. important:: The Queue Launcher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue. If you had some jobs existing in the queue before running this command, you might need to increase the ``-q`` parameter.

5. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command!

.. note:: For more tips on the Queue Launcher, such as how to maintain a certain number of jobs in the queue indefinitely, read its built-in help: ``qlauncher_run.py rapidfire -h``