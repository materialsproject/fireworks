=============================
Defining Jobs using FireTasks
=============================

This tutorial show you how to:

* Run multiple tasks within a single FireWork
* Run tasks that are defined within a Python function, rather than a shell script

This tutorial can be completed from the command line, but some knowledge of Python is helpful. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.

Introduction to FireTasks
=========================

In the :doc:`quickstart <quickstart>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. Looking inside ``fw_test.yaml``, recall that the command was defined within a task labeled ``Script Task``::

    spec:
      _tasks:
      - _fw_name: Script Task
        script: echo "howdy, your job launched successfully!" >> howdy.txt

The ``Script Task`` is one type of *FireTask*, which is a predefined job template written in Python. The ``Script Task`` in particular refers Python code inside FireWorks that runs an arbitrary shell script that you give it. You can use the ``Script Task`` to run almost any job (without worrying that it's all done within a Python layer). However, you might want to set up custom job templates that are more explicit and reusable. In this section, we'll demonstrate how to accomplish this with *FireTasks*, but first we'll demonstrate the simplest version to linearly run multiple tasks.

Running multiple FireTasks
==========================

You can run multiple tasks within the same FireWork (it might be helpful to review the :ref:`wfmodel-label` diagram). For example, the first step of your FireWork might write an input file that the second step reads and processes. Finally, a third step might move the entire output directory somewhere else on your filesystem (or a remote server).

Let's create a FireWork that:

#. Writes an input file based on a *template* with some substitutions applied. We'll do this using a built-in ``Template Writer Task`` that can help create such files.
#. Executes a script using ``Script Task`` that reads the input file and produces some output. In our test case, it will just count the number of words in that file. However, this code could be any program, for example a chemistry code.
#. Copies all your outputs to your home directory using ``Transfer Task``.

The three-step FireWork thus looks like this:

.. image:: _static/templatetask.png
   :width: 300px
   :align: center
   :alt: Template FireWork

1. Navigate to the tasks tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/firetask

#. Look inside the file ``fw_multi.yaml``::

    spec:
      _tasks:
      - _fw_name: Template Writer Task
        context:
          opt1: 5.0
          opt2: fast method
        output_file: inputs.txt
        template_file: simple_template.txt
      - _fw_name: Script Task
        script: wc -w < inputs.txt > words.txt
        use_shell: true
      - _fw_name: Transfer Task
        files:
        - dest: ~/words.txt
          src: words.txt
        mode: copy

   There are now three tasks inside our **spec**: the ``Template Writer Task``, ``Script Task``, and ``Transfer Task``. The ``Template Writer Task`` will load an example template called ``simple_template.txt`` from inside the FireWorks code, replace certain portions of the template using the ``context``, and write the result to ``input.txt``. Next, the ``Script Task`` runs a word count on ``input.txt`` using the ``wc`` command and print the result to ``words.txt``. Finally, ``Transfer Task`` will copy the resulting output file to your home directory.

   .. note:: If you would like to know more about how templated input writing works and define your own templated files, you should consult the :doc:`Template Writer Task tutorial <templatewritertask>`. A copy of ``simple_template.txt`` is given in the directory as ``simple_template_copy.txt`` (however, modifying the copy won't modify the actual template).

   .. note:: The ``Transfer Task`` can do much more than copy a single file. For example, it can transfer your entire output directory to a remote server using SSH. For details, see the :doc:`Transfer Task docs <transfertask>`.

#. Run this multi-step FireWork on your FireServer::

	 lpad reset <TODAY'S DATE>
	 lpad add fw_multi.yaml
	 rlaunch singleshot

.. tip:: You can run all three of these commands on a single line by separating them with a semicolon. This will reset the database, insert a FW, and run it within a single command.

You should see two files written out to the system, ``inputs.txt`` and ``words.txt``, confirming that you successfully ran the first two steps of your job! You can also navigate to your home directory and look for ``words.txt`` to make sure the third step also got completed correctly.

.. note:: The only way to communicate information between FireTasks within the same FireWork is by writing and reading files, such as in our example. If you want to perform more complicated information transfer, you might consider :doc:`defining a workflow <workflow_tutorial>` that connects FireWorks instead. You can pass information easily between different FireWorks in a Workflow through the *FWAction* object, but not between FireTasks within a FireWork (:ref:`wfmodel-label`).

Python Example (optional)
-------------------------

Here is a complete Python example that runs multiple FireTasks within a single FireWork::

    from fireworks.core.firework import FireWork
    from fireworks.core.fworker import FWorker
    from fireworks.core.launchpad import LaunchPad
    from fireworks.core.rocket_launcher import launch_rocket
    from fireworks.user_objects.firetasks.script_task import ScriptTask
    from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask

    # set up the LaunchPad and reset it
    from fireworks.user_objects.firetasks.transfer_task import TransferTask

    launchpad = LaunchPad()
    launchpad.reset('', require_password=False)

    # create the FireWork consisting of multiple tasks
    firetask1 = TemplateWriterTask({'context': {'opt1': 5.0, 'opt2': 'fast method'}, 'template_file': 'simple_template.txt', 'output_file': 'inputs.txt'})
    firetask2 = ScriptTask.from_str('wc -w < inputs.txt > words.txt')
    firetask3 = TransferTask({'files': [{'src': 'words.txt', 'dest': '~/words.txt'}], 'mode': 'copy'})
    fw = FireWork([firetask1, firetask2, firetask3])

    # store workflow and launch it locally, single shot
    launchpad.add_wf(fw)
    launch_rocket(launchpad, FWorker())

.. _customtask-label:

Creating a custom FireTask
==========================

The ``Template Writer Task``, ``Script Task``, ``Transfer Task`` are built-into FireWorks and can be used to perform useful operations. In fact, they might be all you need! In particular, because the ``Script Task`` can run arbitrary shell scripts, it can in theory run any type of computation and is an 'all-encompassing' FireTask. Script Task also has many additional features that are covered in the :doc:`Script Task tutorial <scripttask>`.

However, if you are comfortable with some basic Python, you can define your own custom FireTasks for the codes you run. A custom FireTask gives you more control over your jbos, clarifies the usage of your code, and guards against unintended behavior by restricting the commands that can be executed.

Even if you plan to only use the built-in tasks, we suggest that you still read through the next portion before continuing with the tutorial. We'll be creating a custom FireTask that adds one or more numbers using Python's ``sum()`` function, and later building workflows using this (and similar) FireTasks.

How FireWorks bootstraps a job
------------------------------

Before diving into an example of custom FireTask, it is worth understanding how FireWorks is bootstrapping jobs based on your specification. The basic process looks like this:

.. image:: _static/spec_sketch.png
   :width: 500px
   :align: center
   :alt: FireWorks Bootstrap

1. The first step of the image just shows how the **spec** section of the FireWork is structured. There is a section that contains your FireTasks (one or many), as we saw in the previous examples. The **spec** also allows you to define arbitrary JSON data (labeled *input* in the diagram) to pass into your FireTasks as input. So far, we haven't seen an example of this; the only information we gave in the spec in the previous examples was within the **_tasks** section.

2. In the second step, FireWorks dynamically loads Python objects based on your specified **_tasks**. It does this by searching a list of Python packages for Python objects that have a value of *_fw_name* that match your setting. When we set a *_fw_name* of ``ScriptTask`` in the previous examples, FireWorks was loading a Python object with a *_fw_name* class variable set to ``ScriptTask`` (and passing the ``script`` parameter to its constructor). The ``ScriptTask`` is just one type of FireTask that's built into FireWorks to help you run scripts easily. You can write code for custom FireTasks anywhere in the **user_packages** directory of FireWorks, and it will automatically be discovered. If you want to place your FireTasks in a package outside of FireWorks, please read the :doc:`FireWorks configuration tutorial <config_tutorial>`. You will just need to define what Python packages to search for your custom FireTasks.

3. In the third step, we execute the code of the FireTask we loaded. Specifically, we execute the ``run_task`` method which must be implemented for every FireTask. FireWorks passes in the *entire* spec to the ``run_task`` method; the ``run_task`` method can therefore modify its behavior based on any input data present in the spec, or by detecting previous or future tasks in the spec.

4. When the FireTask is done executing, it returns a *FWAction* object that can modify the workflow (or continue as usual) and pass information to downstream FireWorks.

Custom FireTask example: Addition Task
--------------------------------------

Let's explore custom FireTasks with by writing custom Python for adding two numbers specified in the **spec**.

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
   * A special parameter named *_fw_name* is set to ``Addition Task``. This parameter sets what this FireTask will be called by the outside world and is used to bootstrap the object, as described in the previous section.
   * The ``run_task()`` method is a special method name that gets called when the task is run. It can take in a FireWork specification (**spec**) in order to modify its behavior.
   * When executing ``run_task()``, the AdditionTask we defined first reads the **input_array** parameter of the FireWork's **spec**. It then sums all the values it finds in the **input_array** parameter of the FireWork's **spec** using Python's ``sum()`` function. Next, the FireTask prints the inputs and the sum to the standard out. Finally, the task returns a *FWAction* object.
   * We'll discuss the FWAction object in greater detail in future tutorials. For now, it is sufficient to know that this is an instruction that says we should store the sum we computed in the database (inside the FireWork's ``stored_data`` section).

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

    lpad get_fws -i 1 -d all

Python example (optional)
-------------------------

Here is a complete Python example that runs a custom FireTask::

    from fireworks.core.firework import FireWork
    from fireworks.core.fworker import FWorker
    from fireworks.core.launchpad import LaunchPad
    from fireworks.core.rocket_launcher import launch_rocket
    from fw_tutorials.firetask.addition_task import AdditionTask

    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    launchpad.reset('', require_password=False)

    # create the FireWork consisting of a custom "Addition" task
    firework = FireWork(AdditionTask(), spec={"input_array": [1, 2]})

    # store workflow and launch it locally
    launchpad.add_wf(firework)
    launch_rocket(launchpad, FWorker())

Next up: Workflows!
===================

With custom FireTasks, you can go beyond the limitations of running shell commands and execute arbitrary Python code templates. Furthermore, these templates can operate on data from the **spec** of the FireWork. For example, the ``Addition Task`` used the ``input_array`` from the **spec** to decide what numbers to add. By using the same FireWork with different values in the **spec** (try it!), one could execute a data-parallel application.

While one could construct an entire workflow by chaining together multiple FireTasks within a single FireWork, this is often not ideal. For example, we might want to switch between different FireWorkers for different parts of the workflow depending on the computing requirements for each step. Or, we might have a restriction on walltime that necessitates breaking up the workflow into more atomic steps. Finally, we might want to employ complex branching logic or error-correction that would be cumbersome to employ within a single FireWork. The next step in the tutorial is to explore :doc:`connecting together FireWorks into a workflow <workflow_tutorial>`.