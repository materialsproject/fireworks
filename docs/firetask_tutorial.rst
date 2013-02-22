============================
Defining Jobs using FireTasks
============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. Looking inside ``fw_test.yaml``, you might have noticed that command defined within a task labeled 'SubprocessTask'. The ``SubprocessTask`` is one type of *FireTask*, which is a predefined job template written in Python. The *SubprocessTask* is Python code that runs an arbitrary shell script that you give it, so you can use the SubProcessTask to run almost any job (without worrying that it's all done within a Python layer).

. In this section, we'll demonstrate how to use and define FireTasks.

.. note:: In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker using the instructions from the :doc:`installation tutorial <installation_tutorial>`.

Running multiple FireTasks
--------------------------

You can run multiple tasks within the same FireWork. For example, the first step of your FireWork might write an input file that the second step processes. Let's create a FireWork where the first step prints ``howdy.txt``, and the second step counts the number of words in that file.

1. Navigate to the tasks tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/firetask

2. Look inside the file ``fw_multi.yaml``. You should see two FireTasks; the second one runs the ``wc -w`` command to count the number of characters in ``howdy.txt`` and exports the result to ``words.txt``.

3. Run this multi-step FireWork on the central server::

	 launchpad_run.py initialize <TODAY'S DATE>
	 launchpad_run.py upsert_fw fw_multi.yaml
	 rocket_run.py

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will allow you to reset the database, insert a FW, and run it within a single command.

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

Using SubprocessTask
--------------------

While running arbitrary shell scripts is nice, it's not particularly well-organized. The command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) are all intermingled within the same line. If we separated these components, it would be easier to do a data-parallel task where the same commands are run for multiple arguments. Let's explore a better way to define our multi-step job:

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/firetask
    rm *.txt fw.json

2. Look inside the file ``fw_better_multi.yaml``. You should see two FireTasks as before. However, this time, the text we are printing is separated into its own ``echo_text`` parameter. We just need to change the value of this parameter in order to perform the same commands (``echo`` and ``wc``) on different input data. Note also that the names of the input and output files are also clearly separated from the commands themselves within the FireWork specification.

3. Run the FireWork on the central server to confirm that this new formulation also works as intended::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py upsert_fw fw_better_multi.yaml
	rocket_run.py


Creating a custom FireTask
--------------------------

Because the SubprocessTask can run arbitrary shell scripts, it can in theory run any type of job and is an 'all-encompassing' FireTask. However, it is better to define your own custom FireTasks (job templates) for the codes you run. A custom FireTask can clarify the usage of your code and guard against unintended behavior by restricting the commands that can be executed. For example, let's create a custom FireTask that adds one or more numbers using Python's ``sum()`` function:

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/firetask
    rm *.txt fw.json

2. Look inside the file ``fw_adder.yaml`` for a new FireWork definition. This FireWork references a new FireTask, ``Addition Task``, which is defined inside the file ``addition_task.py`` in the same directory.

3. Look inside the file ``addition_task.py``. It should be clear how a FireTask is set up:
 	a. the reserved ``fw_name`` parameter is set to ``Addition Task``, which is how FireWorks knows to use this code when an ``Addition Task`` is specified inside a FireWork.
 	b. the ``run_task()`` method is the code that gets executed. In this case, the task sums the values in the field called ``input_array``, and writes the output to ``sum_output.txt``.

	.. note:: The main method in ``addition_task.py`` is not necessary to define a FireTask. However, it demonstrates how we created the ``fw_adder.yaml`` file.

4. Run the FireWork on the central server to confirm that the ``Addition Task`` works::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py upsert_fw fw_adder.yaml
	rocket_run.py

Next up: Workflows!
-------------------

With custom FireTasks, you can now go beyond running shell commands and execute arbitrary Python code templates. Furthermore, these templates can operate on dynamic input from the ``spec`` of the FireWork. For example, the ``Addition Task`` used the ``input_array`` from the spec to decide what numbers to add.

While one could construct an entire workflow by chaining together FireTasks within a single FireWork, this is often not ideal. For example, we might want to switch between different FireWorkers for different parts of the workflow depending on the computing requirements for each step. Or, we might have a restriction on walltime that necessitates breaking up the workflow into more atomic steps. Finally, we might want to employ complex branching logic or error-correction that would be cumbersome to employ within a single FireWork. The next step in the tutorial is to explore connecting together FireWorks into a true *workflow*.