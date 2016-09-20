================================
Rerunning a Firework or Workflow
================================

In some instances, you may want to rerun a Firework or Workflow. For example, your computing resource may have crashed or been configured incorrectly during the first run, leading to your first launch being *FIZZLED*. When you rerun a Firework:

* All the Firework's previous launches are *archived* into a special section of the Firework called *archived_launches*. This process also occurs for all the children of the Firework (but not the parents).
* The Firework's state is reset back *READY*. The state of all children is reset back to *WAITING* for the Firework to complete. The archived launches be read by the user but do not affect the operation of the Firework.

One issue with rerunning FireWorks is that the procedure does not reset any previous actions taken by your Firework. For example, if your Firework executed an instruction to create a new Workflow step within its FWAction, or modified the inputs of the child Firework, these actions will **not** be reset when you rerun the Firework. The point is important enough that we'll repeat it in a warning:

.. warning:: Re-running a Firework does not reset any dynamic actions taken by that Firework, such as creating new Workflow steps or modifying the **spec** of its children.

Rerunning a Firework
====================

Rerunning a Firework is simple - just type::

    lpad rerun_fws -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the Firework you want to re-run (or a list of space-separated ids). Note that all children of a re-run Firework will also be re-run.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad rerun_fws [-i FW_IDS] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad rerun_fws -h``) for more information.

Example: Rerunning all FIZZLED FireWorks
========================================

A common use case is to rerun all FIZZLED fireworks. You can do this via::

    lpad rerun_fws -s FIZZLED

Task-level reruns
=================

A Firework might fail while running one of its intermediate or final FireTasks. In that case, sometimes it is desirable not to rerun the entire FireWork, but rather just the tasks that failed. In case of *clean* failures, FireWorks stores data about what step failed inside the database. This data can later be used to restart at the task level. The ``--task-level`` option to the ``rerun_fws`` command allows this type of recovery. For example::

    lpad rerun_fws -s FIZZLED  --task-level

Further options exist, e.g. to attempt to copy data from the previous run into the new run attempt (same filesystem only) via ``--copy-data`` or attempt to rerun in the same directory (``--previous-dir``). Refer to the documentation (``lpad rerun_fws -h``) for more information.  Note also that task-level reruns will modify the spec of your firework such that future standard (i. e. non-task-level) reruns will retain the recovery and attempt to restart at the task level using that recovery.  If you want to clear the recovery information from the spec to ensure that fireworks starts from scratch, you can do so by using the ``--clear-recovery`` flag, e. g. ``lpad rerun_fws -i <FW_IDS> --clear-recovery``.

Rerunning based on error message
================================

The ``launches`` collection in the LaunchPad contains data on the stack trace of the error, which is located in the ``action.stored_data._exception._stacktrace`` key. You can rerun jobs that have a certain text in the error stack trace using something like the following::

    lpad rerun_fws -q '{"action.stored_data._exception._stacktrace": {"$regex": "My custom error message"}}' -lm

Here, the ``My custom error message`` will be searched as a regular expression inside the stack trace. Note the use of the ``lm`` argument - this stands for ``launch_mode`` and indicates that you want to query the ``launches`` collection data. Note the same arguments will work for other commands, e.g. the ``lpad get_fws`` command, in case you want to preview your results before rerunning.