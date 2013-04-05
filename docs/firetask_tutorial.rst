=============================
Defining Jobs using FireTasks
=============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. Looking inside ``fw_test.yaml``, recall that the command was defined within a task labeled ``Script Task``::

    spec:
      _tasks:
      - _fw_name: Script Task
        script: echo "howdy, your job launched successfully!" >> howdy.txt

The ``Script Task`` is one type of *FireTask*, which is a predefined job template written in Python. The ``Script Task`` in particular refers Python code inside FireWorks that runs an arbitrary shell script that you give it. You can use the ``Script Task`` to run almost any job (without worrying that it's all done within a Python layer). However, you might want to set up custom job templates that are more explicit and reusable. In this section, we'll demonstrate how to accomplish this with *FireTasks*.

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
        script: echo "howdy, your job launched successfully!" > howdy.txt
      - _fw_name: Script Task
        script: wc -w < howdy.txt > words.txt

#. Run this multi-step FireWork on your FireServer::

	 lpad reset <TODAY'S DATE>
	 lpad add fw_multi.yaml
	 rlaunch singleshot

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will reset the database, insert a FW, and run it within a single command.

You should see two files written out to the system, ``howdy.txt`` and ``words.txt``, confirming that you successfully ran a two-step job!

.. note:: The only way to communicate information between FireTasks within the same FireWork is by writing and reading files, such as in our example. If you want to perform more complicated information transfer, you might consider :doc:`defining a workflow <workflow_tutorial>` that connects FireWorks instead.

.. _customtask-label:

Creating a custom FireTask
--------------------------

Because the ``Script Task`` can run arbitrary shell scripts, it can in theory run any type of job and is an 'all-encompassing' FireTask. Script Task also has many additional features that will be covered in a future tutorial.

However, if you are comfortable with some basic Python, it is better to define your own custom FireTasks (job templates) for the codes you run. A custom FireTask can clarify the usage of your code and guard against unintended behavior by restricting the commands that can be executed.

Even if you plan to only use ``Script Task``, we suggest that you still read through the next portion before continuing with the tutorial. We'll be creating a custom FireTask that adds one or more numbers using Python's ``sum()`` function, and later building workflows using this (and similar) FireTasks:

.. note:: You can place code for custom FireTasks anywhere in the **user_packages** directory of FireWorks; it will automatically be discovered there. If you want to place your FireTasks in a package outside of FireWorks, please read the :doc:`FireWorks configuration tutorial <config_tutorial>`.

1. Staying in the firetasks tutorial directory, remove any output from the previous step::

    rm howdy.txt FW.json words.txt

#. Let's first look at what a custom FireTask looks like in Python. Look inside the file ``addition_task.py`` which defines the ``Addition Task``::

    class AdditionTask(FireTaskBase, FWSerializable):

        _fw_name = "Addition Task"

        def run_task(self, fw_spec):
            input_array = fw_spec['input_array']
            m_sum = sum(input_array)

            print "The sum of {} is: {}".format(input_array, m_sum)

            return FWAction(stored_data={'sum': m_sum})

#. A few notes about what's going on (things will be clearer after the next step):

   * In the class definition, we are extending *FireTaskBase* to tell FireWorks that this is a FireTask.
   * A special parameter named *_fw_name* is set to ``Addition Task``. This parameter sets what this FireTask will be called by the outside world.
   * The ``run_task()`` method is a special method name that gets called when the task is run. It can take in a FireWork specification (**spec**) in order to modify its behavior.
   * This FireTask first reads the **input_array** parameter of the FireWork's **spec**.
   * It then sums all the values it finds in the **input_array** parameter of the FireWork's **spec** using Python's ``sum()`` function.
   * The FireTask then prints the inputs and the sum to the standard out.
   * Finally, the task returns a *FWAction* object. We'll discuss this object in greater detail in future tutorials. For now, it is sufficient to know that this is an instruction that says we should store the sum we computed in the database (inside the FireWork's ``stored_data`` section).

#. Now let's define a FireWork that runs this FireTask to add the numbers ``1`` and ``2``. Look inside the file ``fw_adder.yaml`` for this new FireWork definition::

    spec:
      _tasks:
      - _fw_name: Addition Task
        parameters: {}
      input_array:
      - 1
      - 2

#. Let's match up this FireWork with our code for our custom FireWork:

   * The *_fw_name* parameter is set to the same value as in our code for the FireTask (``Addition Task``). This is how FireWorks knows to run your custom FireTask rather than ``Script Task`` or some other FireTask.
   * This **spec** has an **input_array** field defined to ``1`` and ``2``. Remember that our Python code was grabbing the values in the **input_array**, summing them, and printing them to standard out.

#. When you are comfortable that you roughly understand how a custom FireTask is set up, try running the FireWork on the central server to confirm that the ``Addition Task`` works::

	lpad reset <TODAY'S DATE>
	lpad add fw_adder.yaml
	rlaunch --silencer singleshot

   .. note:: The ``--silencer`` option suppresses log messages.

#. Confirm that the *sum* is not only printed to the screen, but also stored in our FireWork in the ``stored_data`` section::

    lpad get_fw 1

Next up: Workflows!
-------------------

With custom FireTasks, you can go beyond the limitations of running shell commands and execute arbitrary Python code templates. Furthermore, these templates can operate on data from the **spec** of the FireWork. For example, the ``Addition Task`` used the ``input_array`` from the **spec** to decide what numbers to add. By using the same FireWork with different values in the **spec** (try it!), one could execute a data-parallel application.

While one could construct an entire workflow by chaining together multiple FireTasks within a single FireWork, this is often not ideal. For example, we might want to switch between different FireWorkers for different parts of the workflow depending on the computing requirements for each step. Or, we might have a restriction on walltime that necessitates breaking up the workflow into more atomic steps. Finally, we might want to employ complex branching logic or error-correction that would be cumbersome to employ within a single FireWork. The next step in the tutorial is to explore :doc:`connecting together FireWorks into a workflow <workflow_tutorial>`.