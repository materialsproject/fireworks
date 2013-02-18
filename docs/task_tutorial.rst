============================
Defining Jobs with FireTasks
============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. You may have noticed that the ``fw_test.yaml`` file specified that command within a 'FireTask' labeled 'SubprocessTask'. A *FireTask* is simply a predefined job template; the *SubprocessTask* is a very general FireTask that runs an arbitrary shell script.

In this section, we'll provide more details about FireTasks.

Running multiple tasks
----------------------

You can run multiple tasks within the same job. For example, the first step of your job might involve writing an input file, while a second step is needed to process that input file. Let's extend our previous job to count the number of words in ``howdy.txt``, and print the result to ``words.txt``.

1. Navigate to the tasks tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/task

2. Look inside the file ``fw_multi.yaml``. You should see two FireTasks. The second one runs the ``wc -w`` command to count the number of characters in ``howdy.txt``.

3. Run this FireWork on the central server::

	 launchpad_run.py initialize <TODAY'S DATE>
	 launchpad_run.py upsert_fw fw_multi.yaml
	 rocket_run.py

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

Improving our use of SubprocessTask
-----------------------------------

While running arbitrary shell scripts is nice, it's not particularly clean. For example, 
the command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) were all intermingled within the same line. If we separated these components, it would be easier to do a data-parallel task where the same command (e.g., ``echo``) is run for multiple arguments. In addition, we might want to avoid using shell operators such as piping to file (``>>``). Let's examine a better way to define our multi-step job.

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/task
    rm *.txt

2. Look inside the file ``fw_better_multi.yaml``. You should see two FireTasks. The second one runs the ``wc -w`` command to count the number of characters in ``howdy.txt``.


Improving our code with the SubProcess FireTask
-----------------------------------------------

