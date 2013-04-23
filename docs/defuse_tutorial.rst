===================================
Canceling and restarting a workflow
===================================

You can cancel a FireWork using the *defuse* command of the LaunchPad::

    lpad defuse <FW_ID>

where ``<FW_ID>`` is the numerical id of the FireWork you want to cancel.

.. note:: The defuse command cancels a FireWork and all of its children. However, parent and sibling FireWorks are *not* cancelled. If you wish to cancel an entire Workflow, make sure to cancel the root FireWork id (the first FireWork).

If you later decide you want to run the workflow, you can use the command::

    lpad reignite <FW_ID>

Note that the *defuse* and *reignite* commands will not re-run a workflow that has already been run. To re-run a FireWork, please see the :doc:`rerun tutorial </rerun_tutorial>`.
