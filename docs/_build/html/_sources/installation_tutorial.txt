=====================
Installation Tutorial
=====================

This tutorial will guide you through FireWorks installation on worker nodes, test communication with the queue, and submit some placeholder jobs.

Set up worker nodes
===================

Install FireWorks on the worker
-------------------------------
To install FireWorks on the worker, please follow the instructions listed at :doc:`Installation on a machine </installation>`.

Start playing with the rocket launcher
--------------------------------------

After installation, the script rocket_launcher_run.py should have been added to your system path. The rocket launcher creates directories on your file system to contain your runs, and also submits jobs to the queue.

You should now be able to run the rocket launcher command as an executable. Type this command into your command prompt (from any directory) to ensure that the script is found::

    rocket_launcher_run.py -h
    
This command should print out more detailed help about the rocket launcher. Take a minute to read it over; it might not all be clear, but we'll step through some of the rocket launcher features next.

Run the rocket launcher in single-shot mode
-------------------------------------------

We now want to test interaction of our worker computer with the queue.

1. Navigate to a clean testing directory on your worker node.

2. Take a look in the :doc:`queue_adapters </fireworks.user_objects.queue_adapters>` package to see if an appropriate :doc:`QueueAdapterBase </fireworks.core>` already exists for your queueing system. For example, the implementation :doc:`PBSAdapterNERSC </fireworks.user_objects.queue_adapters>` is documented to work with the PBS queueing system, so if you are using PBS you might want to try this module first.

.. important:: If your queuing system does not have built-in support, do not despair! You might try to use :doc:`PBSAdapterNERSC </fireworks.user_objects.queue_adapters>` as a reference for coding your own PBS adapter. You can also look at the docs for :doc:`QueueAdapterBase </fireworks.core>` to get an idea for what needs to be implemented. In most cases, adding a new QueueAdapterBase implementation should not be difficult. If you encounter trouble, you can contact us for help (see :ref:`contributing-label`).

3. The :doc:`QueueAdapterBase </fireworks.core>` serves as a template for interacting with the queue, but requires a JobParameters file to fill in specific values like walltime, desired queue name, and other application-specific parameters. An example of a very simple JobParameters file is given as job_params_pbs_nersc.yaml in the fireworks/user_objects/queue_adapters directory.

.. important:: The specific format of the JobParameters file might vary with the :doc:`QueueAdapterBase </fireworks.core>`, as each queuing system might require slightly different parameters. Refer to the documentation of your :doc:`QueueAdapterBase </fireworks.core>` implementation to see how to correctly structure a JobParameters file. For example, the :doc:`PBSAdapterNERSC </fireworks.user_objects.queue_adapters>` accepts many more parameters than those listed in the testing JobParameters file.

.. tip:: For more about the JobParameters file, look at the :doc:`JobParameters </fireworks.core>` class.

4. Copy an appropriate JobParameters file to your current directory

5. Modify the JobParameters file as needed to suit your cluster.

.. important:: Ensure that the 'exe' parameter in the JobParameters file reads: "echo 'howdy, your job launched successfully!' >> howdy.txt"

.. important:: Make sure the qa_name parameter in the JobParameters file indicates the name of your desired queue adapter.

6. Try submitting a job using the command::

    rocket_launcher_run.py <JOB_PARAMETERS_FILE>

where the <JOB_PARAMETERS_FILE> points to your JobParameters file, e.g. job_params_pbs_nersc.yaml.

7. Ideally, this should have submitted a job to the queue in the current directory. You can read the log files to get more information on what occurred. The log file location was specified in the JobParameters file.

8. After your queue manager runs your job, you should see the file howdy.txt in the current directory. This indicates that the exe you specified ran correctly.

If you finished this part of the tutorial successfully, congratulations! You've successfully set up a worker node to run FireWorks. You can now continue to test launching jobs in a "rapid-fire" mode.

Run the rocket launcher in rapid-fire mode
------------------------------------------

While launching a single job is nice, a more useful functionality is to maintain a certain number of jobs in the queue. The rocket launcher provides a "rapid-fire" mode that automatically provides this functionality. This mode requires another part of the :doc:`QueueAdapterBase </fireworks.core>` to be functioning properly, namely the part of the code that determines how many jobs are currently in the queue by the current user.

To test rapid-fire mode, try the following:

1. Navigate to a clean testing directory on your worker node.

2. Copy the same JobParameters file to this testing directory as you used for single-shot mode.

.. tip:: You don't always have to copy over the JobParameters file. If you'd like, you can keep a single JobParameters file in some known location and just provide the full path to that file when running the rocket_launcher_run.py executable.

3. Try submitting several jobs using the command::

    rocket_launcher_run.py --rapidfire -q 3 <JOB_PARAMETERS_FILE>
    
where the <JOB_PARAMETERS_FILE> points to your JobParameters file, e.g. job_params_pbs_nersc.yaml.

4. This method should have submitted 3 jobs to the queue at once, all inside of a directory beginning with the tag 'block_'.

5. You can maintain a certain number of jobs in the queue indefinitely by specifying the number of loops parameter to be much greater than 1 (e.g., the example below sets 100 loops)::

    rocket_launcher_run.py --rapidfire -q 3 -n 100 <JOB_PARAMETERS_FILE>

6. The script above should maintain 3 jobs in the queue for 100 loops of the rocket launcher. The rocket launcher will sleep for a user-adjustable time after each loop.

.. tip:: the documentation of the rocket launcher contains additional details, as well as the built-in help file obtained by running the rocket launcher with the -h option.
    
Next steps
----------

If you've completed this tutorial, you've successfully set up a worker node that can communicate with the queueing system and submit either a single job or maintain multiple jobs in the queue.

However, so far the jobs have not been very dynamic. The same executable (the one specified in the JobParameters file) has been run for every single job. This is not very useful.

In the next part of the tutorial, we'll set up a central workflow server and add some jobs to it. Then, we'll come back to the workers and walk through how to dynamically run the jobs specified by the workflow server.
