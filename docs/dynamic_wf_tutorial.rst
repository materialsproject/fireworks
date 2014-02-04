=================
Dynamic Workflows
=================

In this tutorial, we'll explore how to:

* pass information between FireWorks in a Workflow
* define FireTasks that automatically create more FireWorks that depend on the output of the task

This tutorial can be completed from the command line, but basic knowledge of Python is suggested. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.

A workflow that passes data
===========================
Let's imagine a workflow in which the first step adds the numbers 1 + 1, and the second step adds the number 10 to the result of the first step. The second step doesn't know in advance what the result of the first step will be; the first step must pass its output to the second step after it completes. The final result should be 10 + (1 + 1) = 12. Visually, the workflow looks like:

.. image:: _static/addmod_wf.png
   :width: 200px
   :align: center
   :alt: Add and Modify WF

The text in blue lettering is not known in advance and can only be determined after running the first workflow step. Let's examine how we can set up such a workflow.

1. Move to the ``dynamic_wf`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/dynamic_wf

#. The workflow is encapsulated in the ``addmod_wf.yaml`` file. Look inside this file. Like last time, the ``fws`` section contains a list of FireWork objects:

 * ``fw_id`` 1 looks like it adds the numbers 1 and 1 (defined in the **input_array**) within an ``Add and Modify`` FireTask. This is clearly the first step of our desired workflow. Although we don't yet know what the ``Add and Modify`` FireTask is, we can guess that it at least adds the numbers in the **input_array**.
 * ``fw_id`` 2 only adds the number 10 thus far. Without knowing the details of the ``Add and Modify`` FireTask, it is unclear how this FireWork will obtain the output of the previous FireWork.  We'll explain that in the next step.
 * The second section, labeled ``links``, connects these FireWorks into a workflow in the same manner as in the :doc:`first workflow tutorial <workflow_tutorial>`.

#. We pass information by defining a custom FireTask that returns an instruction to modify the workflow. To see how this happens, we need to look inside the definition of our custom ``Add and Modify`` FireTask. Look inside the file ``addmod_task.py``:

 * Most of this FireTask should now be familiar to you; it is very similar to the ``Addition Task`` we investigated when :ref:`customtask-label`.
 * The last line of this file, however, is different. It reads::

        return FWAction(stored_data={'sum': m_sum}, mod_spec=[{'_push': {'input_array': m_sum}}])

 * The first argument, *{'sum': m_sum}*, is the data we want to store in our database for future reference. (We've explored this before when :ref:`customtask-label`). It does not affect this FireWork's operation.
 * The second argument, *mod_spec=[{'_push': {'input_array': m_sum}}]*, is more complex. This argument describes a list of modifications to make to the next FireWork's **spec** using a special language.
 * The instruction *{'_push': {'input_array': m_sum}}* means that the *input_array* key of the next FireWork(s) will have another item *pushed* to the end of it. In our case, we will be pushing the sum of (1 + 1) to the ``input_array`` of the next FireWork.

#. The previous step can be summarized as follows: when our FireTask completes, it will push the sum of its inputs to the inputs of the next FireWork. Let's see how this operates in practice by inserting the workflow in our database::

    lpad reset
    lpad add addmod_wf.yaml

#. If we examined our two FireWorks at this stage, nothing would be out of the ordinary. In particular, one of the FireWorks has only a single input, ``10``, and does not yet know what number to add to ``10``. To confirm::

    lpad get_fws -i 1 -d all
    lpad get_fws -i 2 -d all

#. Let's now run the first step of the workflow::

    rlaunch -s singleshot

#. This prints out ``The sum of [1, 1] is: 2`` - no surprise there. But let's look what happens when we look at our FireWorks again::

    lpad get_fws -i 1 -d all
    lpad get_fws -i 2 -d all

#. You should notice that the FireWork that is ``READY`` - the one that only had a single input of ``10`` - now has *two* inputs: ``10`` and ``2``. Our first FireTask has pushed its sum onto the ``input_array`` of the second FireWork!

#. Finally, let's run the second step to ensure we successfully passed information between FireWorks::

    rlaunch -s singleshot

#. This prints out ``The sum of [10, 2] is: 12`` - just as we desired!

You've now successfully completed an example of passing information between workflows! You should now have a rough sense of how one step of a workflow can modify the inputs of future steps. There are many types of workflow modifications that are possible, including some that involve a simpler (but less flexible) language than what we just demonstrated. We will present details in a different document. For now, we will continue by demonstrating another type of dynamic workflow.

A Fibonacci Adder
=================

You may not know in advance how many workflow steps you require to achieve a result. For example, let's generate all the `Fibonacci numbers <http://en.wikipedia.org/wiki/Fibonacci_number>`_ less than 100, but only using a single addition in each FireWork. It's unclear how many additions we'll need, so we can't set up this workflow explicitly.

Instead, we will start with a single FireWork that contains the start of the sequence (0, 1). This FireWork will generate the next Fibonacci number in the sequence by addition, and then *generate its own child FireWork* to carry out the next addition operation. That child will in turn generate its own children. Starting from a single FireWork, we will end up with as many FireWorks as are needed to generate all the Fibonacci numbers less than 100.

A diagram of our the first two steps of operation of our FireWork looks like this:

.. image:: _static/fibnum_wf.png
   :width: 200px
   :align: center
   :alt: Fibonacci Number Workflow

Our single FireWork will contain a custom FireTask that does the following:

* Given two input Fibonacci numbers (e.g., 0 and 1), find the next Fibonacci number (which is equal to their sum, in this case 1).
* If this next Fibonacci number is less than 100 (the **stop_point**):
    * Print it
    * Create its own child FireWork that will sum the new Fibonacci number we just found with the larger of the current inputs. In our example, this would mean to create a new FireWork with inputs 1 and 1.
    * This new FireWork will output the next Fibonacci number (2), and then create its own child FireWork to continue the sequence (not shown)

* When the next Fibonacci number is greater than 100, print a message that we have exceeded our limit and stop the workflow rather than generate more FireWorks.

Let's see how this is achieved:

1. Stay in the ``dynamic_wf`` tutorial directory on your FireServer and clear it::

    cd <INSTALL_DIR>/fw_tutorials/dynamic_wf
    rm FW.json

#. The initial FireWork is in the file ``fw_fibnum.yaml``. Look inside it. However, there is nothing special here. We are just defining the first two numbers, 0 and 1, along with the **stop_point** of 100, and asking to run the ``Fibonacci Adder Task``.

#. The dynamicism is in the ``Fibonacci Adder Task``, which is defined in the file ``fibadd_task.py``. Look inside this file.

 * The most important part of the code are the lines::

    new_fw = FireWork(FibonacciAdderTask(), {'smaller': larger, 'larger': m_sum, 'stop_point': stop_point})
    return FWAction(stored_data={'next_fibnum': m_sum}, additions=new_fw)

 * The first line defines a new FireWork that is also a ``Fibonacci Adder Task``. However, the inputs are slightly changed: the **smaller** number of the new FireWork is the larger number of the current FireWork, and the **larger** number of the new FireWork is the sum of the two numbers of the current FireWork (just like in our diagram). The **stop_point** is kept the same.
 * The *{'next_fibnum': m_sum}* portion is just data to store inside the database, it does not affect the FireWork's operation.
 * The *additions* argument contains our dynamicism. Here, you can add a FireWork to the workflow (as shown), or even add lists of FireWorks or entire lists of Workflows!

#. Now that we see how our FireTask will create a new FireWork dynamically, let's run the example::

    lpad reset
    lpad add fw_fibnum.yaml
    lpad get_fws

#. That last command should prove that there is only one FireWork in the database. Let's run it::

    rlaunch -s singleshot

#. You should see the text ``The next Fibonacci number is: 1``. Normally this would be the end of the story - one FireWork, one Rocket. But let's try to again to get all the FireWorks in the database::

    lpad get_fws

#. Now there are *two* FireWorks in the database! The previous FireWork created a new FireWork dynamically. We can now run this new FireWork::

    rlaunch -s singleshot

#. This should print out the next Fibonacci number (2). You can repeat this until our FireTask detects we have gone above our limit of 100::

    $ rlaunch -s singleshot
    The next Fibonacci number is: 3
    $ rlaunch -s singleshot
    The next Fibonacci number is: 5
    $ rlaunch -s singleshot
    The next Fibonacci number is: 8
    $ rlaunch -s singleshot
    The next Fibonacci number is: 13
    $ rlaunch -s singleshot
    The next Fibonacci number is: 21
    $ rlaunch -s singleshot
    The next Fibonacci number is: 34
    $ rlaunch -s singleshot
    The next Fibonacci number is: 55
    $ rlaunch -s singleshot
    The next Fibonacci number is: 89
    $ rlaunch -s singleshot
    We have now exceeded our limit; (the next Fibonacci number would have been: 144)

#. If we try to run another Rocket, we would get an error that no FireWorks are left in the database (you can try it if you want). We'll instead look at all the different FireWorks created dynamically by our program::

    lpad get_fws

There are 11 FireWorks in all, and 10 of them were created automatically by other FireWorks!

A Fibonacci Adder: The Quick Way
================================

Let's see how quickly we can add and run our entire workflow consisting of 11 steps::

    lpad add fw_fibnum.yaml
    rlaunch -s rapidfire

That was quick! You might even try again with the **stop_point** in fw_fibnum.yaml raised to a higher value.

.. note:: The rapidfire option creates a new directory for each launch. At the end of the last script you will have many directories starting with ``launcher_``. You might want to clean these up after running.

Python example (optional)
-------------------------

Here is complete Python code for running a dynamic workflow. Note that this code is no different than running any other custom FireWork - it is almost identical to the code we used to run the AdditionTask() two tutorials ago::

    from fireworks import FireWork, FWorker, LaunchPad
    from fireworks.core.rocket_launcher import rapidfire
    from fw_tutorials.dynamic_wf.fibadd_task import FibonacciAdderTask

    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    launchpad.reset('', require_password=False)

    # create the FireWork consisting of a custom "Fibonacci" task
    firework = FireWork(FibonacciAdderTask(), spec={"smaller": 0, "larger": 1, "stop_point": 100})

    # store workflow and launch it locally
    launchpad.add_wf(firework)
    rapidfire(launchpad, FWorker())

Next step: Learning to design workflows
=======================================

You've now explored examples of designing many types of workflows, ranging from very simple and deterministic to quite flexible and dynamic. In the :doc:`final workflow tutorial </design_tips>`, we'll provide some tips on mapping your computing workload into FireTasks, FireWorks, and Workflows.