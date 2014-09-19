============================================
Advanced queue submission (reservation mode)
============================================

Before we begin - if you're here and haven't completed the :doc:`first tutorial on queue submission </queue_tutorial>`, you should go back and complete that first. This tutorial assumes that you already have queue submission working and just need to overcome some of the limitations of simple queue submission.

In this tutorial, we'll introduce the notion of *reserving* FireWorks on queue submission. Some differences between the simple method of the previous tutorial and the reservation method are outlined below:

===============================  =======================================  =============================================
Situation                               Simple Queue Launching              Reservation Queue Launching
===============================  =======================================  =============================================
write/submit queue script        write generic script using QueueAdapter  | 1. **reserve** a FW from the database
                                 file alone                               | 2. use FW's spec to modify queue script
queue manager runs queue script  determine a FW to run and run it         run the **reserved** FW
job is deleted from queue        no action needed by the user             any affected **reserved** jobs must be
                                                                          unreserved by user using detect_unreserved
run multiple FWs in one script   supported                                currently unsupported
offline mode                     unsupported                              supported
===============================  =======================================  =============================================

Reserving jobs allows for more flexibility, but also adds maintenance overhead when queues go down or jobs in the queue are cancelled. Hence, there are some advantages to sticking with Simple Queue Launching. With that out of the way, let's explore the reservation method of queue submission!

Reserving FireWorks
===================

1. Begin in your working directory from the :doc:`previous tutorial </queue_tutorial>`. You should have four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``.

#. Let's reset our database and add a Firework for testing::

    lpad reset
    lpad add fw_test.yaml

#. Reserving a Firework is as simple as adding the ``-r`` option to the Queue Launcher. Let's queue up a reserved Firework and immediately check its state::


    qlaunch -r singleshot
    lpad get_fws -i 1 -d all

#. When you get the Firework, you should notice that its state is *RESERVED*. No other Rocket Launchers will run that Firework; it is now bound to your queue. Some details of the reservation are given in the **launches** key of the Firework. In addition, the **state_history** key should contain the reservation id of your submitted job.

#. There are few different commands you can use to leverage the reservation id (often shortened as *qid*) of your job::

    lpad get_qid -i 1  # gets the queue id of FW 1
    lpad get_fws --qid 1234  # gets the Firework with queue id 1234
    lpad cancel_qid --qid 1234  # cancels reservation 1234. WARNING: the user must remove the job from the queue manually before executing this command.

#. When your queue runs and completes your job, you should see that the state is updated to *COMPLETED*::

    lpad get_fws -i 1 -d more

Preventing too many jobs in the queue
=====================================

One nice feature of reserving FireWorks is that you are automatically prevented from submitting more jobs to the queue than exist FireWorks in the database. Let's try to submit too many jobs and see what happens.

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Reset the database and add a Firework for testing::

    lpad reset
    lpad add fw_test.yaml

#. We have only one Firework in the database, so we should only be able to submit one job to the queue. Let's try submitting two::

    qlaunch -r singleshot
    qlaunch -r singleshot

#. You should see that the first submission went OK, but the second one told us ``No jobs exist in the LaunchPad for submission to queue!``. If we repeated this sequence without the ``-r`` option, we would submit too many jobs to the queue.

   .. note:: Once the job starts *running* or *completes*, both the simple version of the QueueLauncher and the reservation mode will stop you from submitting jobs. However, only the reservation mode will identify that a job is already queued.

Overriding Queue Parameters within the Firework
===============================================

Another key feature of reserving FireWorks before queue submission is that the Firework can override queue parameters. This is done by specifying the ``_queueadapter`` reserved key in the ``spec``. For example, let's override the walltime parameter.

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Look in the file ``my_qadapter.yaml``. You should have walltime parameter listed, perhaps set to 2 minutes. By default, all jobs submitted by this Queue Launcher would have a 2-minute walltime.

#. Let's copy over the ``fw_walltime.yaml`` file from the tutorials dir::

    cp <INSTALL_DIR>/fw_tutorials/queue_pt2/fw_walltime.yaml .

#. Look inside ``fw_walltime.yaml``. You will see a ``_queueadapter`` key in the spec that specifies a ``walltime`` of 10 minutes. Anything in the ``_queueadapter`` key will override the corresponding parameter in ``my_qadapter.yaml`` when the Queue Launcher is run in reservation mode. So now, the Firework itself is determining key properties of the queue submission.

#. Let's add and run this Firework::

    lpad reset
    lpad add fw_walltime.yaml
    qlaunch -r singleshot

#. You might check the walltime that your job was submitted with using your queue manager's built-in commands (e.g., *qstat* or *mstat*). You can also see the queue submission script by looking inside the file ``FW_submit.script``. Inside, you'll see the job was submitted with the walltime specified by your Firework, not the default walltime from ``my_qadapter.yaml``.

#. Your job should complete successfully as before. You could also try to override other queue parameters such as the number of cores for running the job or the account which is charged for running the job. In this way, your queue submission can be tailored on a per-job basis!

Limitations: dealing with failure
=================================

One limitation of reserving FireWorks is that the Firework's fate is tied to that of the queue submission. If the place in the queue is deleted, that Firework is stuck in limbo unless you reset its state from *RESERVED* back to *READY*. Let's try to simulate this:

#. Clean your working directory of everything but four files: ``fw_test.yaml``, ``my_qadapter.yaml``, ``my_fworker.yaml``, and ``my_launchpad.yaml``

#. Let's add and run this Firework. Before the job starts running, delete it from the queue (if you're too slow, repeat this entire step)::

    lpad reset
    lpad add fw_test.yaml
    qlaunch -r singleshot
    qdel <JOB_ID>

   .. note:: The job id should have been printed by the Queue Launcher, or you can check your queue manager. The ``qdel`` command might need to be modified, depending on the type of queue manager you use.

#. Now we have no jobs in the queue. But our Firework still shows up as *RESERVED*::

    lpad get_fws -i 1 -d more

#. Because our Firework is *RESERVED*, we cannot run it::

    qlaunch -r singleshot

   tells us that ``No jobs exist in the LaunchPad for submission to queue!``. FireWorks thinks that our old queue submission (the one that we deleted) is going to run this Firework and is not letting us submit another queue script for the same job.

#. The way to fix this is to find all reservations that have been stuck in a queue for a long time, and then cancel the reservation ("qdel") them. The following command unreserves all FireWorks that have been stuck in a queue for 1 second or more (basically all FireWorks)::

    lpad detect_unreserved --time 1 --rerun

   .. note:: In production, you will want to increase the ``--time`` parameter considerably. The default value is 2 weeks (``--time 1209600``).

#. Now the Firework should be in the *READY* state::

    lpad get_fws -i 1 -d more

#. And we can run it again::

    qlaunch -r singleshot

.. note:: If you un-reserve a Firework that is still in a queue and hasn't crashed, the consequences are not so bad. FireWorks might submit a second job to the queue that reserves this same Firework. The first queue script to run will run the Firework properly. The second job to run will not find a Firework to run and simply exit.

Conclusion
==========

As we demonstrated, reserving jobs in the queue has several advantages, but also adds the complication that queue failure can hold up a Firework until you run a command to free up broken reservations. Is is up to you which mode you prefer for your application. However, we suggest that you use only one of the two methods throughout your application. In particular, do not use the Simple Queue Launcher if you are defining the ``_queueadapter`` parameter in your ``spec``.

If you are using the QueueLauncher in reservation mode, we suggest that you look at the tutorial on maintaining your FireWorks database (future). This will show you how to automatically clear out bad reservations periodically without needing human intervention.