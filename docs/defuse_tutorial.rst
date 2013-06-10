=============================================
Canceling, restarting, and deleting Workflows
=============================================

Canceling and restarting workflows
==================================

You can cancel a FireWork using the *defuse* command of the LaunchPad::

    lpad defuse <FW_ID>

where ``<FW_ID>`` is the numerical id of the FireWork you want to cancel.

.. note:: The defuse command cancels a FireWork and all of its children. However, parent and sibling FireWorks are *not* cancelled. If you wish to cancel an entire Workflow, make sure to cancel the root FireWork id (the first FireWork).

If you later decide you want to run the workflow, you can use the command::

    lpad reignite <FW_ID>

Note that the *defuse* and *reignite* commands will not re-run FireWorks in a workflow that have already been run. Only FireWorks that were never run before will be run upon reignition. To re-run a FireWork, please see the :doc:`rerun tutorial </rerun_tutorial>`.

Deleting (archiving) workflows
==============================

FireWorks does not provide a way to do a hard delete of a Workflow from its database. However, you can simulate a delete operation using the **archive** command. This command prevents all steps in a Workflow from running. It also archives any FireWorks in the Workflow that already ran, in effect simulating that they never existed. Therefore, the Workflow is for practical purposes erased. However, even archived Workflows still exists in the database, and you can query them down the road.

To archive a Workflow, use the command::

    lpad archive <FW_ID>

where *<FW_ID>* is the id of any FireWork in the workflow. Note that all FireWorks in the Workflow will be archived, regardless of which **fw_id** you chose.
