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

To get warmed up, let's set up a *Queue Launcher* to launch a single Rocket through a queueing system.

Configure the Queue Launcher
---------------------------

The Queue Launcher needs to write and submit a queue script that contains an executable (in our case, a Rocket Launcher). This is achieved through a QueueParams file.

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

  .. tip:: Similar to the Rocket Launcher, if you use the names ``my_launchpad.yaml`` and ``my_fworker.yaml``, then you don't need to specify the ``-l`` and ``-w`` options explicitly. FireWorks will automatically search for these files in the current directory. For this tutorial, we'll include the full command and avoid shortcuts.

#. This should have submitted a job to the queue in the current directory. You can read the log files in the logging directory, and/or check the status of your queue to ensure your job appeared.

#. After your queue manager runs your job, you should see the file ``howdy.txt`` in the current directory.

   .. note:: In some cases, firewall issues on shared resources prevent your compute node from accessing your FireServer database. You should confirm that your compute nodes can access external database servers. You might try to submit an *interactive job* to your queue that allows you to type shell commands inside a running job. Once on the compute node, you can try connecting to your FireServer database: ``lp_run.py -l my_launchpad.yaml get_fw 1``. If you cannot connect to the FireServer database from your compute node, you might contact a system administrator for assistance.

If everything ran successfully, congratulations! You just executed a complicated sequence of instructions:

   a. The Queue Launcher submitted a Rocket Launcher to your queue manager
   b. Your queue manager executed the Rocket Launcher when resources were ready
   c. The Rocket Launcher launched a Rocket
   d. The Rocket     fetched a FireWork from the FireServer and ran the specification inside


Adding more power: using rapid-fire mode
========================================

While launching a single job to a queue is nice, a more powerful use case is to submit a large number of jobs at once, or to maintain a certain number of jobs in the queue. Like the Rocket Launcher, the Queue Launcher can be run in a "rapid-fire" mode that provides these features.

1. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Let's reset our database and add three new FireWorks, all from our FireWorker::

    lp_run.py -l my_launchpad.yaml reset <TODAY'S DATE>
    lp_run.py -l my_launchpad.yaml add fw_test.yaml
    lp_run.py -l my_launchpad.yaml add fw_test.yaml
    lp_run.py -l my_launchpad.yaml add fw_test.yaml

#. Submit several jobs with a single command::

    qlauncher_run.py -l my_launchpad.yaml -w my_fworker.yaml rapidfire -q 3 my_qp.yaml

   .. note:: You may have noticed that the paths to ``my_fworker.yaml`` and ``my_launchpad.yaml`` are needed in two places. The first place is when specifying the ``-l`` and ``-w`` arguments to ``qlauncher_run.py``.The second place is inside the ``my_qp.yaml`` file.  The locations when specifying arguments to ``qlauncher_run.py`` are read by the head node during submission of your jobs to the queue manager. The locations inside ``my_qp.yaml``are read by the compute nodes that run your job. These locations can be different or the same, but we suggest that they be the same unless your compute nodes cannot access the same filesystem as your head nodes.

   .. important:: The Queue Launcher sleeps between each job submission to give time for the queue manager to 'breathe'. It might take a few minutes to submit all the jobs.

   .. important:: The command above submits jobs until you have at most 3 jobs in the queue under your username. If you had some jobs existing in the queue before running this command, you might need to increase the ``-q`` parameter.

#. The rapid-fire command should have created a directory beginning with the tag ``block_``. Navigate inside this directory, and confirm that three directories starting with the tag ``launch`` were created. The ``launch`` directories contain your individual jobs.

You've now launched multiple Rockets with a single command!

Continually submit jobs
========================

You might want to set up your worker so that it maintains a certain number of jobs in the queue indefinitely. That way, it will continuously pull FireWorks from the FireServer. Let's set this up.

1. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Let's reset our database and add four new FireWorks this time::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_test.yaml
    lp_run.py add fw_test.yaml
    lp_run.py add fw_test.yaml
    lp_run.py add fw_test.yaml

   .. note:: We have omitted the ``-l`` parameter. You can use this shortcut when using the standard file name (``my_launchpad.yaml``) for the LaunchPad.

#. Run the queue launcher in infinite mode::

    qlauncher_run.py rapidfire -q 2 --infinite my_qp.yaml

   .. note:: We have used the shortcut of omitting the ``-l`` parameter and ``-w`` parameter when using standard file names.

#. This command will always maintain 2 jobs in the queue. When a job finishes, another will be submitted to take its place!

#. As with all FireWorks scripts, you can run the built-in help for more information::

    qlauncher_run.py -h
    qlauncher_run.py singleshot -h
    qlauncher_run.py rapidfire -h

Next steps
==========

If you've completed this tutorial, you're ready to unleash your FireWorks on a large shared resource!

The information in this tutorial might be all you need to automate your application. However, as we noted before, there are some limitations to running in a model where FireWorks is completely unaware of the existence of queues. If you're interested in learning about another mode of the Queue Launcher, in which FireWorks is alerted to the queue, forge on to the next tutorial: :doc:`Reserving FireWorks upon queue submission </queue_tutorial_pt2>`!

.. note:: If you are planning to complete the next tutorial, you might save your working directory with the files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``. We'll use it in the next tutorial.

