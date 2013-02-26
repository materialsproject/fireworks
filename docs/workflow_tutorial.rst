==================
Defining Workflows
==================

Thus far, the only way to run multiple jobs in sequence was to define a list of several FireTasks inside a single FireWork. In this tutorial, we'll explore how Workflows let us deifne complex sequences of FireWorks. We'll start with a simple example and then move to more complicated workflows.

This tutorial can be completed from the command line. Some knowledge of Python is helpful, but not required. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.


The simplest workflow
=====================

The simplest workflow consists of two jobs without any data dependency between them. The only constraint is that the second job should be executed after the first.

For example, we might want print the first two lines of Hamlet's soliloquy to the standard out (e.g., your Terminal window). We can represent the workflow with the following diagram:

.. image:: _static/hamlet_wf.png
   :width: 200px
   :align: center
   :alt: FireWorks

Basically, we just want to ensure that *"To be, or not to be,"* is printed out before *"that is the question:"*. Let's define and execute this workflow.

1. Move to the ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``hamlet_wf.yaml`` file. Look inside this file. The first section, labeled ``fws``, contains a list of FireWork objects:

    * We define a FireWork with ``fw_id`` set to -1, and that prints *"To be, or not to be,"*.
    * We define another FireWork with ``fw_id`` set to -2, and that prints *"that is the question:"*

    The second section, labeled ``wf_connections``, connects these FireWorks into a workflow:

    * In the ``children_links`` subsection, we are specifying that the child of FW with id -1 is the FW with id -2. This means that to hold off on running *"that is the question:"* until we've first run *"To be, or not to be,"*.

#. Let's insert this workflow into our database::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_wf hamlet_wf.yaml

#. Let's look at our two FireWorks::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. You should notice that the FireWork that writes the first line of the text (*"To be, or not to be,"*) shows a state that is ``READY`` to run. In contrast, the FireWork that writes the second line (*"that is the question:"*) shows a state of ``WAITING``. The ``WAITING`` state indicates that a Rocket should not pull this FireWork just yet.

    .. note:: The ``fw_id`` is assigned randomly, so don't assign any meaning to the value of the ``fw_id``.

#. Let's run the just first step of this workflow, and then examine the state of our FireWorks::

    rocket_launcher_run.py singleshot

#. You should have seen the text *"To be, or not to be"* printed to your standard out. Let's examine our FireWorks again to examine our new situation::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. We see now that the first step is ``COMPLETED``, and the second step has automatically graduated from ``WAITING`` to ``READY``.

#. Let's now launch a Rocket that will run the second FireWork of this Workflow.

    rocket_launcher_run.py singleshot

#. This should print the second step of the workflow (*"That is the question"*). You can verify that both steps are completed::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

.. note:: Shakespeare purists will undoubtedly notice that I have mangled the first line of this soliloquy by splitting it into two lines.

A workflow that passes data
===========================

Our *Hamlet* workflow was not particularly interesting; you could have achieved the same result by :doc:`running multiple FireTasks within a single FireWork <firetask_tutorial>`. Indeed, the single-FireWork solution is conceptually much simpler than defining workflows. The design choice of using FireTasks versus a Workflow in such scenarios is discussed another tutorial.

Meanwhile, we will move on to the case where a FireWork needs data from a previous FireWork in order to perform its task. For example, we can imagine that the first step of our workflow is to add the numbers 1 + 1, and the second step is to add the number 10 to the result. The second step doesn't know in advance what the result of the first step will be; the first step must pass its output to the second step after it completes.

our next example will go one step further and pass data from the first step to the next. The first step of our workflow will add the numbers 1 + 1, and the second step will add the number 2 to the result. So the final result should equal 2 + (1 + 1) = 4. The workflow looks as follows:

We'll achieve this by defining a FireTask
