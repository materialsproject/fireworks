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

#. The workflow is encapsulated in the ``hamlet_wf.tar`` file. Packed within this file are two FireWork files (one for each step of the workflow), and third file called ``wfconnections.yaml``. The ``wfconnections.yaml`` file defines the connections between the two FireWorks.

    .. note:: If you don't like the tar file format, you can also serialize an entire workflow as a single JSON or YAML file. For details, see the tutorial on FW serialization (*future*)

#. Normally, one would not need to unpack ``hamlet_wf.tar``. But for curiosity's sake, let's unpack this file and look inside. (if you're not curious, you can skip to step 5!) ::

    tar -xvf hamlet_wf.tar

#. You can now explore the files inside using a text editor. The ``fw_-1.yaml`` file writes the first line of the text to ``hamlet.txt``, the ``fw_-2.yaml`` file writes the second line to the same file, and the ``wfconnections.yaml`` file connects ``fw_id`` of the two FireWorks. Once you feel you have understood the contents of ``hamlet_wf.tar``, you can clean up your directory::

    rm *.yaml

#. Let's insert this workflow into our database::

    launchpad_run.py insert_wf hamlet_wf.tar

#. Let's look at our two FireWorks::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. You should notice that the FireWork that writes the first line of the text ("*To be, or not to be,*") shows a state that is ``READY`` to run. In contrast, the FireWork that writes the second line ("*that is the question:*") shows a state of ``WAITING``. The ``WAITING`` state indicates that a Rocket should not pull this FireWork just yet.

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

.. note:: In general, we do not recommend running ``rocket_launcher_run.py singleshot`` multiple times in the same directory, because the ``fw.json`` file gets overwritten. Instead, the ``rocket_launcher_run.py rapidfire`` option is recommended, along with defining appropriate data dependencies between your jobs (rapidfire changes directories, meaning you can't trivially access the same ``hamlet.txt`` file in both FireWorks).

