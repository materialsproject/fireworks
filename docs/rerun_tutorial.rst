================================
Rerunning a FireWork or Workflow
================================

In some instances, you may want to rerun a FireWork or Workflow. For example, your computing resource may have crashed or been configured incorrectly during the first run, leading to your first launch being *FIZZLED*. When you rerun a FireWork:

* All the FireWork's previous launches are *archived* into a special section of the FireWork called *archived_launches*. This process also occurs for all the children of the FireWork (but not the parents).
* The FireWork's state is reset back *READY*. The state of all children is reset back to *WAITING* for the FireWork to complete. The archived launches be read by the user but do not affect the operation of the FireWork.

One issue with rerunning FireWorks is that the procedure does not reset any previous actions taken by your FireWork. For example, if your FireWork executed an instruction to create a new Workflow step within its FWAction, or modified the inputs of the child FireWork, these actions will **not** be reset when you rerun the FireWork. The point is important enough that we'll repeat it in a warning:

.. warning:: Re-running a FireWork does not reset any dynamic actions taken by that FireWork, such as creating new Workflow steps or modifying the **spec** of its children.

Rerunning a FireWork
====================

Rerunning a FireWork is simple - just type::

    lpad rerun_fws -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the FireWork you want to re-run (or a list of space-separated ids). Note that all children of a re-run FireWork will also be re-run.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad rerun_fws [-i FW_IDS] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad rerun_fws -h``) for more information.

Example: Rerunning all FIZZLED FireWorks
========================================

A common use case is to rerun all FIZZLED fireworks. You can do this via::

    lpad rerun_fws -s FIZZLED