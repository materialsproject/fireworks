==============================
Launch Rockets through a queue
==============================

If your FireWorker is a large, shared resource (such as a computing cluster or supercomputing center), you probably won't be able to launch Rockets directly. Instead, you'll submit Rockets through an existing queueing system that allocates computer resources.

The simplest way to execute jobs through a queue is to submit scripts to your queue manager that run ``rlaunch``. This method is just like typing ``rlaunch`` into a Terminal window like in the core tutorials, except that now we are submitting a queue script that does the typing for us (it's very low-tech!). In particular, FireWorks is *completely unaware* that you are running through a queue!

The jobs we will submit to the queue are basically placeholder jobs that are asleep until the job starts running. When the job is actually assigned computer resources and runs, the script "wakes" up and runs the Rocket Launcher, which then figures out what FireWork to run.

The advantage of this low-tech system is that it is quite durable; if your queue system goes down or you delete a job from the queue, there are zero repercussions. You don't have to tell FireWorks to run those jobs somewhere else, because FireWorks never knew about your queue in the first place. In addition, if you are running on multiple machines and the queue becomes backlogged on one of them, it does not matter at all. Your job stuck in the queue is not preventing high-priority jobs from running on other machines.

There are also some disadvantages to this simple system, which we'll discuss at the end of the tutorial. We'll also direct you on how to overcome these limitations in a subsequent tutorial. For now, we suggest that you get things working simply.

Launch a single job through a queue
===================================

To get warmed up, let's set up a *Queue Launcher* to run a single FireWork through a queueing system.

Configure the Queue Launcher
----------------------------

The Queue Launcher needs to write and submit a queue script that contains an executable (in our case, a Rocket Launcher). This is achieved through a QueueAdapter file.

1. Move to the ``queue`` tutorial directory on your FireWorker::

    cd <INSTALL_DIR>/fw_tutorials/queue

#. Locate an appropriate QueueAdapter file. The files are usually named ``qadapter_<QUEUE>.yaml`` where ``<QUEUE>`` is the supported queue system.

.. note:: If you cannot find a working QueueAdapter file for your specific queuing system, please contact us for help! (see :ref:`contributing-label`) We would like to support more queueing systems in FireWorks.

#. Copy your chosen QueueAdapter file to a new name::

    cp qadapter_<QUEUE>.yaml my_qadapter.yaml

#. Navigate to clean working directory on the FireWorker. For example::

    mkdir ~/queue_tests
    cd ~/queue_tests

#. Copy over your queue file and the test FW to this directory::

    cp <INSTALL_DIR>/fw_tutorials/queue/my_qadapter.yaml .
    cp <INSTALL_DIR>/fw_tutorials/queue/fw_test.yaml .

#. Copy over your LaunchPad and FireWorker files from the worker tutorial::

    cp <INSTALL_DIR>/fw_tutorials/worker/my_fworker.yaml .
    cp <INSTALL_DIR>/fw_tutorials/worker/my_launchpad.yaml .

   .. note:: If you do not have these files, please go back and regenerate them according to the instructions :doc:`here </worker_tutorial>`.

#. Open ``my_qadapter.yaml`` and modify it as follows:

   a. In the part that specifies running ``rlaunch``, modify the ``path/to/my_fworker.yaml`` to contain the **absolute path** of the ``my_fworker.yaml`` file on your machine.

   b. On the same line, modify the ``path/to/my_launchpad.yaml`` to contain the **absolute path** of the ``my_launchpad.yaml`` file on your machine.

   c. For the logdir parameter, modify the ``path/to/logging`` text to contain the **absolute path** of where you would like FireWorks logs to go. For example, you might create a ``fw_logs`` directory inside your home directory, and point the logdir parameter there.

   .. note:: Be sure to indicate the full, absolute path name; do not use BASH shortcuts like '.', '..', or '~', and do not indicate a relative path.

You are now ready to begin!

Add some FireWorks
------------------

Staying in your testing directory, let's reset our database and add a new FireWork, all from our FireWorker::

    lpad reset <TODAY'S DATE>
    lpad add fw_test.yaml

Submit a job
------------

1. Try submitting a job using the command::

    qlaunch singleshot

  .. tip:: Similar to the Rocket Launcher, if you use the names ``my_launchpad.yaml``, ``my_fworker.yaml``, and ``my_qadapter.yaml``, then you don't need to specify the ``-l``, ``-w``, and ``-q`` options explicitly. FireWorks will automatically search for these files in the current directory, or in a configuration directory that you specify with a single ``-c`` parameter, or in the directories specified by your :doc:`FWConfig file <config_tutorial>`.

#. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

#. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

   .. note:: In some cases, firewall issues on shared resources prevent your compute node from accessing your FireServer database. You should confirm that your compute nodes can access external database servers. You might try to submit an *interactive job* to your queue that allows you to type shell commands inside a running job. Once on the compute node, you can try connecting to your FireServer database: ``lpad -l my_launchpad.yaml get_fw 1``. If you cannot connect to the FireServer database from your compute node, you might contact a system administrator for assistance.

If everything ran successfully, congratulations! You just executed a FireWork through a queue!

Adding more power: using rapid-fire mode
========================================

While launching a single job to a queue is nice, a more powerful use case is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. Like the Rocket Launcher, the Queue Launcher can be run in a "rapid-fire" mode that provides these features.

1. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Let's reset our database and add three new FireWorks, all from our FireWorker::

    lpad reset <TODAY'S DATE>
    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml

#. Submit several jobs with a single command::

    qlaunch rapidfire -m 3

   .. important:: The Queue Launcher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue under your username. If you had some jobs existing in the queue before running this command, you might need to increase the ``-m`` parameter.

#. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command, all through a queueing system!

Continually submit jobs to the queue
====================================

You might want to set up your worker so that it maintains a certain number of jobs in the queue indefinitely. That way, it will continuously pull FireWorks from the FireServer. Let's set this up.

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``.

#. Let's reset our database and add four new FireWorks this time::

    lpad reset <TODAY'S DATE>
    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml

   .. note:: We have omitted the ``-l`` parameter. You can use this shortcut when using the standard file name (``my_launchpad.yaml``) for the LaunchPad.

#. Run the queue launcher in **infinite** mode::

    qlaunch rapidfire -m 2 --nlaunches infinite

#. This command will always maintain 2 jobs in the queue. When a job finishes, another will be submitted to take its place!

Running multiple Rockets per queue job
======================================

So far, each queue script we submitted has only one job. We can also submit multiple jobs per queue script by running the ``rapidfire`` option of the *Rocket Launcher* inside the Queue Launcher. Then, a single queue script will run multiple Rockets.

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``.

#. Copy your QueueAdapter file to ``my_qp_multi.yaml``::

    cp my_qadapter.yaml my_qp_multi.yaml

#. Edit ``my_qp_multi.yaml`` as follows:

    a. In the part that specifies running ``rlaunch``, modify the ``singleshot`` text to read ``rapidfire``.

#. Let's add three FireWorks to the LaunchPad and submit a *single* queue script::

    lpad reset <TODAY'S DATE>
    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml
    qlaunch -q my_qp_multi.yaml singleshot

#. You should confirm that only a single job got submitted to the queue. However, when the job starts running, you'll see that all three of your jobs completed in separate ``launcher_`` directories!

.. warning:: Currently, we do not recommend running in this mode unless you are confident that all jobs can finish before the walltime expires. Otherwise, you might run into a situation where the walltime kills one of your jobs mid-run. In future tutorials and FireWorks versions, we'll demonstrate how to handle this case cleanly. For now, we suggest you stick to one FireWork per queue script unless you know what you are doing!


More information
================

#. As with all FireWorks scripts, you can run the built-in help for more information::

    qlaunch -h
    qlaunch singleshot -h
    qlaunch rapidfire -h

Limitations and Next Steps
==========================

The information in this tutorial might be all you need to automate your application. However, as we noted previously, there are some limitations to running under a model in which FireWorks is completely unaware of the existence of queues. Some limitations include:

1. **You can't track how many of your jobs are queued**

Since FireWorks is unaware of your queue, there's no way to track how many of your jobs are queued up on various machines. You'll have to wait until they start running before their presence is reported to FireWorks.

2. **You might submit too many jobs to the queue**

It's possible to submit more queue scripts than exist jobs in the database. Before submitting a queue script, the Queue Launcher checks that at least one unstarted job exists in the database. However, let's take an example where you have one FireWork in the database that's ready to run. Nothing in the current system prevents you from using the Queue Launcher to rapid-fire 20 jobs to the queue.  You won't be prevented from submitting queue scripts until that FireWork has actually started running.

If the number of jobs in your database is kept much higher than the number of jobs you keep in your queues, then you shouldn't run into this problem at all; all your submitted queue scripts will always find a job to run. Even if this is not the case, the additional queue scripts should pose only a minor penalty. Any extra queue scripts will wake up, find nothing to do, and exit without wasting more than few seconds of computer time. If you are using rapid-fire mode, you'll also end up with an additional ``launcher_`` directory.

3. **You can't easily tailor queue parameters (e.g. walltime) individually for each the job**

Perhaps the most severe limitation is that the Queue Launcher submits queue scripts with identical queue parameters (e.g., all jobs will have the same walltime, use the same number of cores, etc.)

If you have just two or three sets of queue parameters for your different job types, you can work around this limitation. First, recall that you can use the FireWorker file to restrict which jobs get run (see tutorial). If you have two types of jobs, you can run *two* Queue Launchers. Each of these Queue Launchers use different queue parameters, corresponding to the two types of jobs you'd like to run. In addition, each Queue Launcher should be run with a corresponding FireWorker that restricts that jobs for that launcher to the desired job type.

While this solution works for a few different job types, it is not practical if you have many job types. In addition, it requires some coordination between FireWork categories, FireWorkers, and Queue Launchers. Therefore, if setting multiple sets of queue parameters is needed for your application, we suggest that you read on for a solution.

Next step: reserving FireWorks to overcome limitations
------------------------------------------------------

If you feel these limitations severely impact your workflow, you should forge on to the next tutorial: :doc:`Reserving FireWorks upon queue submission </queue_tutorial_pt2>`. We'll explain how *reserving* FireWorks upon queue submission can solve the limitations of simple queue submission, at the expense of added complexity.

.. note:: If you are planning to complete the next tutorial, you should save your working directory with the files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``. We'll use it in the next tutorial.