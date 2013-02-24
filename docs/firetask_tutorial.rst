============================
Defining Jobs using FireTasks
============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. Looking inside ``fw_test.yaml``, you might have noticed that command defined within a task labeled ``Subprocess Task``::

    fw_id: -1
    spec:
      _tasks:
      - _fw_name: Subprocess Task
        parameters:
          script: echo "howdy, your job launched successfully!" >> howdy.txt
          use_shell: true

The ``Subprocess Task`` is one type of *FireTask*, which is a predefined job template written in Python. The ``Subprocess Task`` is Python code that runs an arbitrary shell script that you give it, so you can use the ``SubProcess Task`` to run almost any job (without worrying that it's all done within a Python layer). In this section, we'll demonstrate how to use and define FireTasks.

This tutorial can be completed from the command line. Some knowledge of Python is helpful, but not required. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.

Running multiple FireTasks
--------------------------

You can run multiple tasks within the same FireWork. For example, the first step of your FireWork might write an input file that the second step processes. Let's create a FireWork where the first step prints ``howdy.txt``, and the second step counts the number of words in that file.

1. Navigate to the tasks tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/firetask

2. Look inside the file ``fw_multi.yaml``. You should see two instances of ``Subprocess Task``; the second one runs the ``wc -w`` command to count the number of characters in ``howdy.txt`` and exports the result to ``words.txt``::

    fw_id: -1
    spec:
      _tasks:
      - _fw_name: Subprocess Task
        parameters:
          script: echo "howdy, your job launched successfully!" > howdy.txt
          use_shell: true
      - _fw_name: Subprocess Task
        parameters:
          script: wc -w < howdy.txt > words.txt
          use_shell: true
    launch_data: []

3. Run this multi-step FireWork on the central server::

	 launchpad_run.py initialize <TODAY'S DATE>
	 launchpad_run.py insert_single_fw fw_multi.yaml
	 rocket_launcher_run.py singleshot

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will reset the database, insert a FW, and run it within a single command.

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

.. note:: The only way to communicate information between FireTasks within the same FireWork is by writing and reading files, such as in our example. If you want to perform more complicated information transfer, you should consider :doc:`defining a workflow <workflow_tutorial>` that connects FireWorks instead. Or, you could define a single custom FireTask that performs multiple steps internally (the `custodian <https://pypi.python.org/pypi/custodian>`_ Python package is one option to help achieve this).

Using SubprocessTask
--------------------

While running arbitrary shell scripts is nice, it's not particularly well-organized. The command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) are all intermingled within the same line. If we separated these components, it would be easier to do a data-parallel task where the same commands are run for multiple arguments. Let's explore a better way to define our multi-step job:

1. Staying in the firetasks tutorial directory, remove any output from the previous step::

    rm howdy.txt fw.json

2. Look inside the file ``fw_better_multi.yaml``. You should see two FireTasks as before. However, this time, the text we are printing is separated into its own ``echo_text`` parameter, which is defined outside the ``tasks`` part of the ``spec``. We just need to change the value of this parameter in order to perform the same commands (``echo`` and ``wc``) on different input data. Note also that the names of the input and output files are also clearly separated from the commands themselves within the FireWork specification::

    fw_id: -1
    spec:
      _tasks:
      - _fw_name: Subprocess Task
        parameters:
          script: cat -t
          stdin_key: echo_text
          stdout_file: howdy.txt
      - _fw_name: Subprocess Task
        parameters:
          script: wc -w
          stdin_file: howdy.txt
          stdout_file: words.txt
      echo_text: howdy, your job launched successfully!
    launch_data: []

3. Run the FireWork on the central server to confirm that this new formulation also works as intended::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py insert_single_fw fw_better_multi.yaml
	rocket_launcher_run.py singleshot

At this point, you might want to change the ``echo_text`` parameter to something other than ``howdy, your job launched successfully!``, reinsert the FireWork, and re-run the Rocket. Your custom text should get printed to ``howdy.txt`` and the number of words should change appropriately.

Creating a custom FireTask
--------------------------

Because the ``Subprocess Task`` can run arbitrary shell scripts, it can in theory run any type of job and is an 'all-encompassing' FireTask. However, if you are comfortable with some basic Python, it is better to define your own custom FireTasks (job templates) for the codes you run. A custom FireTask can clarify the usage of your code and guard against unintended behavior by restricting the commands that can be executed.

Even if you plan to only use ``Subprocess Task``, we suggest that you still read through the next portion before continuing with the tutorial. We'll be creating a custom FireTask that adds one or more numbers using Python's ``sum()`` function, and later building workflows with this FireTask:

1. Navigate to the tasks tutorial directory and remove any output from the previous step::

    cd <INSTALL_DIR>/fw_tutorials/firetask
    rm howdy.txt fw.json

2. Look inside the file ``fw_adder.yaml`` for a new FireWork definition. This FireWork references a new FireTask, ``Addition Task``, that adds the numbers ``1`` and ``2``::

    fw_id: -1
    spec:
      _tasks:
      - _fw_name: Addition Task
        parameters: {}
      input_array:
      - 1
      - 2
    launch_data: []

3. Look inside the file ``addition_task.py`` which defines the ``Addition Task``::

     class AdderTask(FireTaskBase, FWSerializable):

        _fw_name = "Addition Task"

        def run_task(self, fw):
            input_array = fw.spec['input_array']
            m_sum = sum(input_array)

            with open('sum_output.txt', 'w') as f:
                f.write("The sum of {} is: {}".format(input_array, m_sum))

4. It should be clear how the ``Addition Task`` is set up:
 	a. the reserved ``_fw_name`` parameter is set to ``Addition Task``, which is how FireWorks knows to use this code when an ``Addition Task`` is specified inside the ``fw_adder.yaml`` FireWork file.
 	b. the ``run_task()`` method is the code that gets executed by the Rocket. In this case, we sum the values in the field called ``input_array``, and write the output to ``sum_output.txt``. In our ``fw_adder.yaml`` file, the ``input_array`` was set to ``1`` and ``2``.

	.. note:: The main method in ``addition_task.py`` is not necessary to define a FireTask. However, it demonstrates how we created the ``fw_adder.yaml`` file.

4. Run the FireWork on the central server to confirm that the ``Addition Task`` works::

	launchpad_run.py initialize <TODAY'S DATE>
	launchpad_run.py insert_single_fw fw_adder.yaml
	rocket_launcher_run.py singleshot

Next up: Workflows!
-------------------

With custom FireTasks, you can now go beyond running shell commands and execute arbitrary Python code templates. Furthermore, these templates can operate on dynamic input from the ``spec`` of the FireWork. For example, the ``Addition Task`` used the ``input_array`` from the spec to decide what numbers to add. By using the same FireWork with different values in the ``spec``, one could execute a data-parallel application.

While one could construct an entire workflow by chaining together FireTasks within a single FireWork, this is often not ideal. For example, we might want to switch between different FireWorkers for different parts of the workflow depending on the computing requirements for each step. Or, we might have a restriction on walltime that necessitates breaking up the workflow into more atomic steps. Finally, we might want to employ complex branching logic or error-correction that would be cumbersome to employ within a single FireWork. The next step in the tutorial is to explore :doc:`connecting together FireWorks into a workflow <workflow_tutorial>`.