=================
Dynamic Workflows
=================

to the case where a FireWork needs data from a previous FireWork in order to perform its task, and create also dynamically bge

For example, we can imagine that the first step of our workflow adds the numbers 1 + 1, and the second step adds the number 10 to the result of the first step. The second step doesn't know in advance what the result of the first step will be; the first step must pass its output to the second step after it completes. The final result should be 10 + (1 + 1) = 12. Visually, the workflow looks like:

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
