==================
Defining Workflows
==================

Thus far, the only way to run multiple jobs in sequence was to define a list of several FireTasks inside a FireWork. In this tutorial, we'll explore how workflows can help us set up complex sequences of FireWorks. We'll start simple and then move to more complicated workflows.

This tutorial can be completed from the command line. Some knowledge of Python is helpful, but not required. In this tutorial, we will run examples on the central server for simplicity. One could just as easily run them on a FireWorker if you've set one up.


The simplest workflow
=====================

The simplest workflow consists of two jobs without any data dependency between them. The only constraint is that the second job should be executed after the first.

For example, we might want print the first two lines of Hamlet's soliloquy into a file called ``hamlet.txt``. We can represent the workflow using the following diagram:

.. image:: _static/hamlet_wf.png
   :width: 200px
   :align: center
   :alt: FireWorks

Let's define and execute this workflow.

1. Move to the ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``hamlet_wf.yaml`` file. Look inside this file. The first section, labeled ``fws``, contains a list of FireWork objects:

    * We define a FireWork with ``fw_id`` set to -1, and that prints *"To be, or not to be,"*.
    * We define another FireWork with ``fw_id`` set to -2, and that prints *"that is the question:"*

    The second section, labeled ``wf_connections``, connects these FireWorks into a workflow:

    * In the ``children_links`` subsection, we are specifying that the child of FW with id -1 is the FW with id -2. This means that we want to run *"To be, or not to be,"* first, and *"that is the question:"* after that.

#. Let's insert this workflow into our database::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_wf hamlet_wf.yaml

#. Let's look at our two FireWorks::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. You should notice that the FireWork that writes the first line of the text (*"To be, or not to be,"*) shows a state that is ``READY`` to run. In contrast, the FireWork that writes the second line (*"that is the question:"*) shows a state of ``WAITING``. The ``WAITING`` state indicates that a Rocket should not pull this FireWork just yet.

    .. note:: The ``fw_id`` is assigned randomly, and it's possible that that the FireWork that will run first will have a larger ``fw_id`` than the one that runs second.

#. Let's run the just first step of this workflow, and then examine the state of our FireWorks::

    rocket_launcher_run.py singleshot
    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. We see now that the first step is ``COMPLETED``, and the second step has automatically graduated from ``WAITING`` to ``READY``. In addition, the file ``hamlet.txt`` correctly contains the first section of our desired text.

#. Let's finish by running the second step of the workflow and re-examining the FireWork states::

    rocket_launcher_run.py singleshot
    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. Now, both steps should be completed. In addition, ``hamlet.txt`` should contain our text in the correct order!

    .. note:: Shakespeare purists will undoubtedly notice that I have mangled the first line of this soliloquy by splitting it into two lines.

#. Finally, let's clean up our directory::

    rm fw.json hamlet.txt

.. note:: In general, we do not recommend running ``rocket_launcher_run.py singleshot`` multiple times in the same directory, because the ``fw.json`` file gets overwritten. We are running in the same directory for this example so that that both FireWorks can access ``hamlet.txt``. The example will break if we run a Rocket in a different location. In a later tutorial we will cover how to properly pass files between FireWorks in a workflow.

A workflow that passes data
===========================

Our *Hamlet* workflow was not particularly interesting; you could have achieved the same result by :doc:`running multiple FireTasks within a single FireWork <firetask_tutorial>`. Indeed, the single-FireWork solution is conceptually much simpler than defining workflows. However, even for our *Hamlet* example, a workflow possesses some advantages over using a single FireWork. First, the LaunchPad kept detailed records about the operation of each workflow step, allowing you to dig into the specifics of where and when each individual step completed (using ``launchpad_run.py get_fw <fw_id>``). Second, splitting the job into multiple FireWorks means that multiple Rockets will be launched rather than a single Rocket containing the entire job. The runtime of each Rocket can be kept short, and the load of the job can be split up over several FireWorkers. This latter feature is especially useful if different steps of your workflow require to be run on different types of hardware. However, it does mean that necessary files and data must be transferred between workflow steps.

Our next example will go one step further and pass data from the first step to the next. The first step of our workflow will add the numbers 1 + 1, and the second step will add the number 2 to the result. So the final result should equal 2 + (1 + 1) = 4. The workflow looks as follows:

We'll achieve this by defining a FireTask
