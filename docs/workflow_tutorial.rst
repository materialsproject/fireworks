==================
Creating Workflows
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
   :alt: Hamlet WF

Basically, we just want to ensure that *"To be, or not to be,"* is printed out before *"that is the question:"*. Let's define and execute this workflow.

1. Move to the ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``hamlet_wf.yaml`` file. Look inside this file. The first section, labeled ``fws``, contains a list of FireWork objects:

    * We define a FireWork with ``fw_id`` set to -1, and that prints *"To be, or not to be,"*.
    * We define another FireWork with ``fw_id`` set to -2, and that prints *"that is the question:"*

    .. note:: A negative ``fw_id`` means that the ``fw_id`` should be reassigned by the LaunchPad so as not to conflict with existing ``fw_ids``. When you insert the Workflow into the database using the LaunchPad, the LaunchPad will echo back an ``id_map`` that tells you how ``fw_ids`` were reassigned. The ``fw_id`` is assigned in an arbitrary order, so don't interpret any meaning in the value of the ``fw_id``.

    The second section, labeled ``links``, connects these FireWorks into a workflow:

    * In the ``children_links`` subsection, we are specifying that the child of FW with id -1 is the FW with id -2. This means hold off on running *"that is the question:"* until we've first run *"To be, or not to be,"*.

#. Let's insert this workflow into our database::

    lpad reset <TODAY'S DATE>
    lpad add hamlet_wf.yaml

#. Let's look at our two FireWorks::

    lpad get_fw 1
    lpad get_fw 2

#. You should notice that the FireWork that writes the first line of the text (*"To be, or not to be,"*) shows a state that is *READY* to run. In contrast, the FireWork that writes the second line is not yet *READY*.

#. Let's run the just first step of this workflow, and then examine the state of our FireWorks::

    rlaunch --silencer singleshot

#. You should have seen the text *"To be, or not to be"* printed to your standard out. Let's examine our FireWorks again to examine our new situation::

    lpad get_fw 1
    lpad get_fw 2

#. We see now that the first step is ``COMPLETED``, and the second step has automatically graduated from ``WAITING`` to ``READY``.

#. Let's now launch a Rocket that will run the second FireWork of this Workflow::

    rlaunch --silencer singleshot

#. This should print the second step of the workflow (*"That is the question"*). You can verify that both steps are completed::

    lpad get_fw 1
    lpad get_fw 2

.. note:: Shakespeare purists will undoubtedly notice that I have mangled the first line of this soliloquy by splitting it into two lines. But at least we printed them in the correct order!

A Diamond Workflow
==================

Let's continue with a very similar example, but make the workflow a little more intricate. We will now print the org chart of a company. Of course, CEOs should be printed before managers, and managers before interns:

.. image:: _static/org_wf.png
   :width: 400px
   :align: center
   :alt: Org chart WF

Let's quickly define and execute this workflow.

1. Stay in the same ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``org_wf.yaml`` file. Look inside this file.

    * The ``fws`` section should make sense - we have defined one FireWork for each position in the company (4 in total).
    * The ``links`` section should also make sense. The CEO has two children (the managers). The managers each have the same child (the intern). (The company appears to be quite the oligarchy!)

#. Once everything makes sense, let's add the workflow and run everything at once::

    lpad reset <TODAY'S DATE>
    lpad add org_wf.yaml
    rlaunch --silencer rapidfire

#. You should notice that the CEO correctly gets printed above the managers, who in turn are printed above the intern. There is no preference amongst the two managers as written; FireWorks might print either manager first. If you want to distinguish between them, you can use priorities (covered in a future tutorial).

#. Finally, you can clean up your rapid directory if you are not interested in saving the contents of each launch::

    rm -r launcher_*

Next steps
==========

Neither our *Hamlet* workflow nor our diamond workflow were particularly interesting; you could have achieved the same result by :doc:`running multiple FireTasks within a single FireWork <firetask_tutorial>`. Indeed, the single-FireWork solution with multiple FireTasks is conceptually much simpler than defining workflows. The design choice of using FireTasks versus a Workflow in such scenarios is discussed another tutorial. For example, you might want to use a Workflow if each step requires a different type of computing resource.

Meanwhile, you can continue on to the last step(!) of the core FireWorks tutorials, which better illustrates the power of workflows: :doc:`Dynamic workflows <dynamic_wf_tutorial>`.