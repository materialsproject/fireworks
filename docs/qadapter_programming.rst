======================
Writing Queue Adapters
======================

FireWorks is intended to support multiple queueing systems. To support a new queueing system, a few functions need to be defined for that queue manager (e.g., what command is used to submit jobs?). In most cases, new queue managers can be supported with minimal effort.

Writing a simple queue adapter
==============================

You can write a simple queue adapter with just a few code modifications of an existing queue adapter.

Find a location
---------------

First, you need to decide on a location for your queue adapter Python code. The built-in queue adapters are located in ``<INSTALL_DIR>/fireworks/user_objects/queue_adapters``. However, you can also place your queue adapter in a different Python package if you set the ``ADD_USER_PACKAGES`` option in the :doc:`FW config </config_tutorial>`.

Copy an existing adapter
------------------------

1. Choose a somewhat similar built-in adapter (e.g., ``pbs_adapter.py``) and copy that Python file to a new file, e.g. ``new_adapter.py``.
2. Also copy the corresponding template file (e.g., ``PBS_template.txt``) to a new file, e.g. ``new_template.txt``.

Modify the adapter
------------------

1. Modify your new template file (the ``.txt`` file) to look like a typical queue script for your queue manager. To define variables, use the ``$${var}`` notation. Anything that is a variable can be overridden by your ``my_qadapter.yaml`` file or by the ``_queueadapter`` key within reservation mode. Lines containing undefined variables will be skipped when writing the queue script.

2. Next, go to your new Python file (the ``.py`` file) and make the following simple variable changes:

  * Change the ``_fw_name`` to something descriptive for your new adapter. A common format is to put both the queue manager system and a specific machine the queue script was defined for.
  * Change the ``template_file`` parameter to point to your new template file
  * Change the ``submit_cmd`` to be the command used to submit jobs, e.g. ``qsub`` or ``squeue``.
  * Change the ``q_name`` to something descriptive of the queue manager, like ``pbs`` or ``slurm``. This name is used for the naming of log files and in error message reports.
  * (optional) Change the ``defaults`` to contain default parameter values for the variables in your template.

3. Finally, implement a few methods by modifying the existing ones:

  * ``_parse_jobid()`` should be able to take the standard output string returned when submitting a job and parse a job id (preferably an integer).
  * ``_get_status_cmd()`` should be an array of Strings describing the command for printing the list of jobs for a particular user. e.g. for PBS it involves the ``qstat`` command.
  * ``_parse_njobs()`` should take the raw text from the output of executing the status command (e.g. ``qstat``) and figure out then number of jobs currently in the queue for a given user. Often, this involves counting the lines of code returned by the status command.

After making these modifications, your new queue adapter should be ready! You can use it by specifying the correct ``_fw_name`` in your ``my_qadapter.yaml`` file.

Writing a complex queue adapter
===============================

FireWorks was structured so that when writing most queue adapters, you don't need to spend a lot of time writing boilerplate code (e.g. to execute commands, parse standard out, or log the sequence of commands). Rather, you just switch a couple of variable like ``submit_cmd``. By assuming a few things about your queue manager, FireWorks generally keeps queue adaptor code to something like 10-20 lines.

However, if your queue is a complex entity than typical queue managers (maybe a web-based submission framework), the boilerplate code may no longer apply. If this is the case, you will need to manually define or more of the following methods:

  * the ``the get_script_str()`` method
  * the ``submit_to_queue()`` method
  * the ``get_njobs_in_queue()`` method

In each case, you might look at the *QueueAdapterBase* class for an example.