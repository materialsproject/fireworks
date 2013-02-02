=====================
Installation Tutorial
=====================

This tutorial will guide you through FireWorks installation on the central server and one or more worker nodes. The purpose of this tutorial is simply to get you set up as quickly as possible, and is not intended to demonstrate the features or explain the implementation of FireWorks.

*TODO: provide more detailed tutorials about how things are working.*

*TODO: provide an overview picture, probably on some other page.*

Set up worker nodes
===================

Install FireWorks on the worker
-------------------------------
To install FireWorks on the worker, please follow the instructions listed at :doc:`Installation on a machine </installation>`.

Start playing with the rocket launcher
--------------------------------------

The rocket launcher creates directories on your file system to contain your runs, and also submits jobs to the queue.

After installing the FireWorks code, the script rocket_launcher_run.py should have been added to your system path. Type this command into your command prompt (from any directory) to ensure that the script is found::

    rocket_launcher_run.py -h

This command should print out more detailed help about the rocket launcher. Take a minute to read it over; it might not all be clear, but we'll step through some of the rocket launcher features next.

Run the rocket launcher in single-shot mode
-------------------------------------------

We are now going to submit a single job to the queue using the rocket launcher. Submitting a job requires interaction with the queue; the details of the interaction are specified through a JobParameters file. For the purposes of this tutorial, we are going to try to use one of the JobParameters files provided with the FireWorks installation.

1. Navigate to a clean testing directory on your worker node.

2. An example of a simple JobParameters file is named job_params_pbs_nersc.yaml in the fireworks/user_objects/queue_adapters directory. You can guess that this file is for interaction with PBS queues, both from the name of the file and (if you peek inside) the qa_name parameter which specifies a PBS 'queue adapter'. If you are using a different queuing system than PBS, you should search for a different JobParameters file.

.. important:: If you cannot find an appropriate JobParameters file for your specific queuing system, please contact us for help (see :ref:`contributing-label`). We would like to build support for many queuing systems into the FireWorks package. *TODO: give better instructions on what to do if a plug-and-play JobParameters file is not found.*

4. Copy the appropriate JobParameters file to your current working directory.

5. If you haven't already done so, look inside the JobParameters file to get a sense for the parameters that it sets. As mentioned before, the qa_name parameter is somehow responsible for interaction with your specific queuing system. One thing to note is that 'exe' parameter indicates the executable that will be launched once your job starts running in the queue.

.. important:: Ensure that the 'exe' parameter in the JobParameters file reads: "echo 'howdy, your job launched successfully!' >> howdy.txt"

6. Try submitting a job using the command::

    rocket_launcher_run.py <JOB_PARAMETERS_FILE>

where the <JOB_PARAMETERS_FILE> points to your JobParameters file, e.g. job_params_pbs_nersc.yaml.

7. Ideally, this should have submitted a job to the queue in the current directory. You can read the log files to get more information on what occurred. (The log file location was specified in the JobParameters file)

8. After your queue manager runs your job, you should see the file howdy.txt in the current directory. This indicates that the exe you specified ran correctly.

If you finished this part of the tutorial successfully, congratulations! You've successfully set up a worker node to run FireWorks. You can now continue to test launching jobs in a "rapid-fire" mode.

Run the rocket launcher in rapid-fire mode
------------------------------------------

While launching a single job is nice, a more useful functionality is to maintain a certain number of jobs in the queue. The rocket launcher provides a "rapid-fire" mode that automatically provides this functionality.

To test rapid-fire mode, try the following:

1. Navigate to a clean testing directory on your worker node.

2. Copy the same JobParameters file to this testing directory as you used for single-shot mode.

.. tip:: You don't always have to copy over the JobParameters file. If you'd like, you can keep a single JobParameters file in some known location and just provide the full path to that file when running the rocket_launcher_run.py executable.

3. Try submitting several jobs using the command::

    rocket_launcher_run.py --rapidfire -q 3 <JOB_PARAMETERS_FILE>
    
where the <JOB_PARAMETERS_FILE> points to your JobParameters file, e.g. job_params_pbs_nersc.yaml.

4. This method should have submitted 3 jobs to the queue at once, all inside of a directory beginning with the tag 'block_'.

5. You can maintain a certain number of jobs in the queue indefinitely by specifying that the rocket launcher loop multiple times (e.g., the example below sets 100 loops)::

    rocket_launcher_run.py --rapidfire -q 3 -n 100 <JOB_PARAMETERS_FILE>

.. note:: The script above should maintain 3 jobs in the queue for 100 loops of the rocket launcher. The rocket launcher will sleep for a user-adjustable time after each loop.

.. tip:: the documentation of the rocket launcher contains additional details, as well as the built-in help file obtained by running the rocket launcher with the -h option.
    
Next steps
----------

If you've completed this tutorial, you've successfully set up a worker node that can communicate with the queueing system and submit either a single job or maintain multiple jobs in the queue.

However, so far the jobs have not been very dynamic. The same executable (the one specified in the JobParameters file) has been run for every single job. This is not very useful.

In the next part of the tutorial, we'll set up a central workflow server and add some jobs to it. Then, we'll come back to the workers and walk through how to dynamically run the jobs specified by the workflow server.
