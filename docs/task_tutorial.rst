============================
Defining Jobs with FireTasks
============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. You may have noticed that the ``fw_test.yaml`` file specified that command within a 'FireTask' labeled 'SubprocessTask'. A *FireTask* is simply a predefined job template; the *SubprocessTask* is a very general FireTask that runs an arbitrary shell script.

In this section, we'll provide more details about FireTasks.

Running multiple FireTasks
--------------------------

You can run multiple tasks within the same job. For example, the first step of your job might involve writing an input file, while a second step is needed to process that input file. Let's extend our previous job to count the number of words in ``howdy.txt``, and print the result to ``words.txt``.

1. Navigate to the tasks tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/task

2. Look inside the file ``fw_multi.yaml``. You should see two FireTasks. The second one runs the ``wc -w`` command to count the number of characters in ``howdy.txt``.

3. Run this FireWork on the central server::

	 launchpad_run.py initialize <TODAY'S DATE>
	 launchpad_run.py upsert_fw fw_multi.yaml
	 rocket_run.py

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will allow you to very quickly reset the database, insert a FW, and run it.

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

Using SubprocessTask
--------------------

While running arbitrary shell scripts is nice, it's not particularly clean. The command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) were all intermingled within the same line. If we separated these components, it would be easier to do a data-parallel task where the same commands are run for multiple arguments. Let's examine a better way to define our multi-step job:

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/task
    rm *.txt *.json

2. Look inside the file ``fw_better_multi.yaml``. You should see two FireTasks as before. However, this time notice that the command we are printing out is separated out into its own ``echo_text`` parameter. We just need to change the value of this parameter in order to perform the same commands (``echo`` and ``wc``) on different input data. Note also that the input and output files are also now clearly separated from the commands.

3. Run the FireWork on the central server to confirm that it also works::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py upsert_fw fw_better_multi.yaml
	rocket_run.py


Creating a new FireTask
-----------------------

Because the SubprocessTask can run arbitrary shell scripts, it can in theory run any type of job. However, it is better to define custom FireTasks (job templates) for the codes you run. A custom FireTask can clarify the usage of your code and guard against unintended behavior by restricting the commands that can be executed. For example, let's look at a custom FireTask that adds one or more numbers using Python's ``sum()`` function:

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/task
    rm *.txt *.json

2. Look inside the file ``fw_adder.yaml``. This FireWork references the ``Addition Task``, which is defined inside the file ``addition_task.py`` in the same directory.

3. Look inside the file ``addition_task.py``. It should be clear how a FireTask is set up:
 	a. the reserved ``fw_name`` parameter is set to ``Addition Task``, which is how FireWorks knows to use this code when an ``Addition Task`` is specified inside a FireWork.
 	b. the ``run_task()`` method is the code that gets executed. In this case, the task sums the values in the field called ``input_array``, and writes the output to ``sum_output.txt``.

 
4. Run the FireWork on the central server to confirm that it also works::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py upsert_fw fw_better_multi.yaml
	rocket_run.py

