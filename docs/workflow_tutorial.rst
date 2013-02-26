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
   :alt: Hamlet WF

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

.. note:: Shakespeare purists will undoubtedly notice that I have mangled the first line of this soliloquy by splitting it into two lines. But at least we printed them in the correct order!

A Diamond Workflow
==================

Let's continue with a very similar example, but make the workflow a little more intricate. We will now print the org chart of a company. Of course, CEOs should be printed before managers, and managers before interns:

.. image:: _static/org_wf.png
   :width: 400px
   :align: center
   :alt: Org chart WF

Let's quickly define and execute this workflow.

1. Move to the ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``org_wf.yaml`` file. Look inside this file.

    * The ``fws`` section should make sense - we have defined a FireWork to print each position in the company.
    * The ``wf_connections`` section should also make sense. The CEO has two children (the managers). The managers each have the same child (the intern). (The company appears to be quite the oligarchy!)

#. Once everything makes sense, let's add the workflow and run everything at once!::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_wf org_wf.yaml
    rocket_launcher_run.py rapidfire --silencer

#. You should notice that the CEO correctly gets printed above the managers, who in turn are printed above the intern. There is no preference amongst the two managers as written; FireWorks might print either manager first. If you want to distinguish between them, you can use priorities (covered in a future tutorial).

#. Finally, you can clean up your directory::

    rm -r launcher_*

A workflow that passes data
===========================

Our *Hamlet* workflow was not particularly interesting; you could have achieved the same result by :doc:`running multiple FireTasks within a single FireWork <firetask_tutorial>`. Indeed, the single-FireWork solution with multiple FireTasks is conceptually much simpler than defining workflows. The design choice of using FireTasks versus a Workflow in such scenarios is discussed another tutorial.

Meanwhile, we will move on to the case where a FireWork needs data from a previous FireWork in order to perform its task. For example, we can imagine that the first step of our workflow adds the numbers 1 + 1, and the second step adds the number 10 to the result of the first step. The second step doesn't know in advance what the result of the first step will be; the first step must pass its output to the second step after it completes. The final result should be 10 + (1 + 1) = 12. Visually, the workflow looks like:

.. image:: _static/addmod_wf.png
   :width: 200px
   :align: center
   :alt: Add and Modify WF

The text in blue lettering is not known in advance and can only be determined after running the first workflow step. Let's examine how we can set up such a workflow.

1. Move to the ``workflow`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/workflow

#. The workflow is encapsulated in the ``addmod_wf.yaml`` file. Look inside this file. Like last time, the ``fws`` section contains a list of FireWork objects:

    * ``fw_id`` -1 looks like it adds the numbers 1 and 1 (defined in the ``input_array``) within an ``Add and Modify`` FireTask. This is clearly the first step of our desired workflow.
    * ``fw_id`` -2 only adds the number 10 thus far. It is is so far not clear how this FireWork will add the output of the previous FireWork to this single number. We'll explain this in the next step.

    The second section, labeled ``wf_connections``, connects these FireWorks into a workflow in the same manner as the previous example.

#. We pass information by defining a custom FireTask that returns an instruction to modify the workflow. To see how this happens, we need to look inside the definition of our custom ``Add and Modify`` FireTask. Look inside the file ``addmod_task.py``:

    * Most of this FireTask should now be familiar to you; it is very similar to the ``Addition Task`` we investigated in the :doc:`FireTask tutorial <firetask_tutorial>`.
    * The last line of this file, however, is different. It reads::

        return FWDecision('MODIFY', {'sum': m_sum}, {'dict_mods': [{'_push': {'input_array': m_sum}}]})

    * The first argument, *MODIFY*, indicates that we want to modify the inputs of the next FireWork (somehow!)
    * The second argument, *{'sum': m_sum}*, is the data we want to store in our database. It does not affect this FireWork's operation.
    * The final argument, *{'dict_mods': [{'_push': {'input_array': m_sum}}]}*, is the most complex. This argument describes the modifications to make to the next FireWork using a special language. For now, it's sufficient to know that when using the *MODIFY* command, one must specify a *dict_mods* key that contains a list of *modifications*. In our case, we have just a single modification: *{'_push': {'input_array': m_sum}}*.
    * The instruction *{'_push': {'input_array': m_sum}}* means that the *input_array* key of the next FireWork(s) will have another item *pushed* to the end of it. In our case, we will be pushing the sum of (1 + 1) to the ``input_array`` of the next FireWork.

#. The previous step can be summarized as follows: when our FireTask completes, it will push the sum of its inputs to the inputs of the next FireWork. Let's see how this operates in practice by inserting the workflow in our database::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_wf addmod_wf.yaml

#. If we examined our two FireWorks at this stage, nothing would be out of the ordinary. In particular, the FireWork that is ``WAITING`` has only a single input, ``10``, and does not yet know what number to add to ``10``. To confirm::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. Let's now run the first step of the workflow::

    rocket_launcher_run.py singleshot

#. This prints out ``The sum of [1, 1] is: 2`` - no surprise there. But let's look what happens when we look at our FireWorks again::

    launchpad_run.py get_fw 1
    launchpad_run.py get_fw 2

#. You should notice that the FireWork that is ``READY`` - the one that only had a single input of ``10`` - now has *two* inputs: ``10`` and ``2``. Our first FireTask has pushed its sum onto the ``input_array`` of the second FireWork!

#. Finally, let's run the second step to ensure we successfully passed information between FireWorks::

    rocket_launcher_run.py singleshot

#. This prints out ``The sum of [10, 2] is: 12`` - just as we desired!

You've now successfully completed an example of passing information between workflows! You should now have a rough sense of how one step of a workflow can modify the inputs of future steps. There are many types of workflow modifications that are possible, including file transfer operations (listed in future tutorials). For now, we will continue by quickly running a complex workflow.

A complex workflow
==================
