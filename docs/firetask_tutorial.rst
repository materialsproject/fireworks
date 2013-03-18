=============================
Defining Jobs using FireTasks
=============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. Looking inside ``fw_test.yaml``, that command was defined within a task labeled ``Script Task``::

    spec:
      _tasks:
      - _fw_name: Script Task
        parameters:
          script: echo "howdy, your job launched successfully!" >> howdy.txt
          use_shell: true

The ``Script Task`` is one type of *FireTask*, which is a predefined job template written in Python. The ``Script Task`` in particular refers Python code inside FireWorks that runs an arbitrary shell script that you give it. You can use the ``Script Task`` to run almost any job (without worrying that it's all done within a Python layer). However, you might want to set up custom job templates that are more explicit and reusable. In this section, we'll demonstrate how to accomplish this with *FireTasks*, as well as provide more details on the ``Script Task``.

This tutorial can be completed from the command line. Some knowledge of Python is helpful, but not required. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.

Running multiple FireTasks
--------------------------

You can run multiple tasks within the same FireWork. For example, the first step of your FireWork might write an input file that the second step processes. Let's create a FireWork where the first step prints ``howdy.txt``, and the second step counts the number of words in that file.

1. Navigate to the tasks tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/firetask

#. Look inside the file ``fw_multi.yaml``. You should see two instances of ``Script Task`` inside our **spec**. Remember, our **spec** contains all the information needed to run our job. The second ``Script Task`` runs the ``wc -w`` command to count the number of characters in ``howdy.txt`` and exports the result to ``words.txt``::

    spec:
      _tasks:
      - _fw_name: Script Task
        parameters:
          script: echo "howdy, your job launched successfully!" > howdy.txt
          use_shell: true
      - _fw_name: Script Task
        parameters:
          script: wc -w < howdy.txt > words.txt
          use_shell: true

#. Run this multi-step FireWork on your FireServer::

	 lpad reset <TODAY'S DATE>
	 lpad add fw_multi.yaml
	 rlaunch singleshot

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will reset the database, insert a FW, and run it within a single command.

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

.. note:: The only way to communicate information between FireTasks within the same FireWork is by writing and reading files, such as in our example. If you want to perform more complicated information transfer, you might consider :ref:`customtask-label` or :doc:`defining a workflow <workflow_tutorial>` that connects FireWorks instead.

Using ScriptTask
--------------------

While running arbitrary shell scripts is flexible, it's not particularly well-organized. The command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) are all intermingled within the same line. If we separated these components, it would be easier to do a data-parallel task where the same commands are run for multiple arguments. Let's explore a better way to define our multi-step job:

1. Staying in the firetasks tutorial directory, remove any output from the previous step::

    rm howdy.txt FW.json words.txt

#. Look inside the file ``fw_better_multi.yaml``::

    spec:
      _tasks:
      - _fw_name: Script Task
        parameters:
          script: cat -t
          stdin_key: echo_text
          stdout_file: howdy.txt
      - _fw_name: Script Task
        parameters:
          script: wc -w
          stdin_file: howdy.txt
          stdout_file: words.txt
      echo_text: howdy, your job launched successfully!

   You should see two FireTasks as before. However, this time, the **spec** contains more than just **_tasks** - it also contains an **echo_text** parameter that's separated from the **_tasks**. We can replace the **echo_text** parameter with arbitrary data, and the same **_tasks** will process that data. Thus, performing the same tasks on multiple data is just a matter of changing a single parameter.

   Under the hood, the first ``Script Task`` is getting its input from the **echo_text** parameter (we defined its ``stdin_key`` to be *echo_text*). It is then writing its output to ``howdy.txt``. The second ``Script Task`` is reading in ``howdy.txt``, performing the ``wc -w`` command, and writing its output ``words.txt``.

   .. note:: We have changed the command from ``echo`` (in earlier examples) to ``cat -t`` - this is because ``cat -t`` can easily take in input from a standard input stream, which is how the **echo_text** parameter is being fed in.

#. Run the FireWork on the central server to confirm that this new formulation also works as intended::

	lpad reset <TODAY'S DATE>
	lpad add fw_better_multi.yaml
	rlaunch singleshot

At this point, you might want to change the ``echo_text`` parameter to something other than ``howdy, your job launched successfully!``, reinsert the FireWork, and re-run the Rocket. Your custom text should get printed to ``howdy.txt`` and the number of words should change appropriately.

.. _customtask-label:

Creating a custom FireTask
--------------------------

Because the ``Script Task`` can run arbitrary shell scripts, it can in theory run any type of job and is an 'all-encompassing' FireTask. However, if you are comfortable with some basic Python, it is better to define your own custom FireTasks (job templates) for the codes you run. A custom FireTask can clarify the usage of your code and guard against unintended behavior by restricting the commands that can be executed.

Even if you plan to only use ``Script Task``, we suggest that you still read through the next portion before continuing with the tutorial. We'll be creating a custom FireTask that adds one or more numbers using Python's ``sum()`` function, and later building workflows using this (and similar) FireTasks:

.. note:: You can place code for custom FireTasks in the **user_packages** directory of FireWorks; it will be discovered there. If you want to place your FireTasks in a package outside of FireWorks, please read the :doc:`FireWorks configuration tutorial <config_tutorial>`.

1. Staying in the firetasks tutorial directory, remove any output from the previous step::

    rm howdy.txt FW.json words.txt

#. Let's first look at what a custom FireTask looks like in Python. Look inside the file ``addition_task.py`` which defines the ``Addition Task``::

    class AdditionTask(FireTaskBase, FWSerializable):

        _fw_name = "Addition Task"

        def run_task(self, fw_spec):
            input_array = fw_spec['input_array']
            m_sum = sum(input_array)

            print "The sum of {} is: {}".format(input_array, m_sum)

            return FWAction('CONTINUE', {'sum': m_sum})

#. A few notes about what's going on:

 * In the class definition, we are extending *FireTaskBase* to tell FireWorks that this is a FireTask.
 * A special parameter named *_fw_name* is set to ``Addition Task``. This parameter sets what this FireTask will be called by the outside world.
 * The ``run_task()`` method is a special method name that gets called when the task is run. It can take in a FireWork object's specification (*fw_spec*).
 * This FireTask first reads the **input_array** parameter of the FireWork's **spec**.
 * It then sums all the values it finds in the **input_array** parameter of the FireWork's **spec** using Python's ``sum()`` function.
 * The FireTask then prints both the inputs and the sum to the standard out.
 * Finally, the task returns a *FWAction* object. We'll discuss this object in greater detail in future tutorials. For now, it is sufficient to know that this is an instruction that says we should *CONTINUE* with the workflow, and store the sum we computed in the database (inside the FireWork's ``stored_data`` section).

#. Now let's define a FireWork that runs this FireTask to add the numbers ``1`` and ``2``. Look inside the file ``fw_adder.yaml`` for this new FireWork definition::

    spec:
      _tasks:
      - _fw_name: Addition Task
        parameters: {}
      input_array:
      - 1
      - 2

#. Let's match up this FireWork's **spec** with our code for our custom FireWork:

 * The *_fw_name* parameter is set to the same value as in our code for the FireTask (``Addition Task``). This is how FireWorks knows to run your custom FireTask rather than ``Script Task`` or some other FireTask.
 * This **spec** has an **input_array** field defined to ``1`` and ``2``. Remember that our Python code was grabbing the values in the **input_array**, summing them, and printing them to standard out.

#. When you are comfortable that you roughly understand how a custom FireTask is set up, try running the FireWork on the central server to confirm that the ``Addition Task`` works::

	lpad reset <TODAY'S DATE>
	lpad add fw_adder.yaml
	rlaunch --silencer singleshot

.. note:: The ``--silencer`` option suppresses log messages.

# Confirm that the *sum* is not only printed to the screen, but also stored in our FireWork in the ``stored_data`` section::

    lpad get_fw 1

Next up: Workflows!
-------------------

With custom FireTasks, you can go beyond the limitations of running shell commands and execute arbitrary Python code templates. Furthermore, these templates can operate on data from the ``spec`` of the FireWork. For example, the ``Addition Task`` used the ``input_array`` from the spec to decide what numbers to add. By using the same FireWork with different values in the ``spec``, one could execute a data-parallel application.

While one could construct an entire workflow by chaining together multiple FireTasks within a single FireWork, this is often not ideal. For example, we might want to switch between different FireWorkers for different parts of the workflow depending on the computing requirements for each step. Or, we might have a restriction on walltime that necessitates breaking up the workflow into more atomic steps. Finally, we might want to employ complex branching logic or error-correction that would be cumbersome to employ within a single FireWork. The next step in the tutorial is to explore :doc:`connecting together FireWorks into a workflow <workflow_tutorial>`.