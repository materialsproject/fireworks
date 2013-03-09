=========================================
Reserving FireWorks upon queue submission
=========================================

Before we begin - if you're here and haven't completed the :doc:`first tutorial on queue submission </queue_tutorial>`, you should go back and complete that first. This tutorial assumes that you already have queue submission working and just need to overcome some of the limitations of simple queue submission.

In this tutorial, we'll introduce the notion of *reserving* FireWorks on queue submission. Some differences between the simple method of the previous tutorial and the reservation method are outlined below:

===============================  ======================================  =============================================
Situation                               Simple Queue Launching              Reservation Queue Launching
===============================  ======================================  =============================================
write/submit queue script        write generic script using QueueParams  | 1. **reserve** a FW from the database
                                 file alone                              | 2. use FW's spec to modify queue script
queue manager runs queue script  determine a FW to run and run it        run the **reserved** FW
job is deleted from queue        no action needed by the user            any affected **reserved** jobs must be
                                                                         unreserved by user manually
===============================  ======================================  =============================================

Reserving jobs allows for more flexibility, but also adds maintenance overhead when queues go down or jobs in the queue are cancelled. Hence, there are some advantages to sticking with Simple Queue Launching. With that out of the way, let's explore the reservation method of queue submission!

Reserving FireWorks
===================

1. Begin in your working directory from the :doc:`previous tutorial </queue_tutorial>`. You should have four files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``.

   .. note:: Because we are using standard filenames for the LaunchPad and FireWorker, we will omit the ``-l`` and ``-w`` parameters when running scripts for the remainder of this tutorial.

#. Let's reset our database and add a FireWork for testing::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_test.yaml

#. Reserving a FireWork is as simple as adding the ``-r`` option to the Queue Launcher. Let's queue up a reserved FireWork and immediately check its state::


    qlauncher_run.py -r singleshot my_qp.yaml
    lp_run.py get_fw 1

#. When you get the FireWork, you should notice that its state is *RESERVED*. No other Rocket Launchers will run that FireWork; it is now bound to your queue. Some details of the reservation are given in the ``launches`` key of the FireWork.

#. When your queue runs and completes your job, you should see that the state is updated to *COMPLETED*::

    lp_run.py get_fw 1

Preventing too many jobs in the queue
=====================================

One nice feature of reserving FireWorks is that you are automatically prevented from submitting more jobs to the queue than exist FireWorks in the database. Let's try to submit too many jobs and see what happens.

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qp.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Reset the database and add a FireWork for testing::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_test.yaml

#. We have only one FireWork in the database, so we should only be able to submit one job to the queue. Let's try submitting two::

    qlauncher_run.py -r singleshot my_qp.yaml
    qlauncher_run.py -r singleshot my_qp.yaml

#. You should see that the first submission went OK, but the second one told us ``No jobs exist in the LaunchPad for submission to queue!``. If we repeated this sequence without the ``-r`` option, we would submit too many jobs to the queue.

   .. note:: Once the job starts *running* or *completes*, both the Simple version of the queue launcher and the Reservation version will stop you from submitting jobs. However, only the Reservation version will identify that a job is already queued.

Overriding Queue Parameters within the FireWork
===============================================

