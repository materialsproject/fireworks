=======================================================
Canceling (pausing), restarting, and deleting Workflows
=======================================================

Canceling workflows
===================

You can cancel (pause) Workflows using the *defuse* command of the LaunchPad::

    lpad defuse -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the FireWork you want to defuse (or a list of space-separated ids). Note that all children of a defused FireWork will also be defused. However, parent and sibling FireWorks are *not* cancelled.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad defuse [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad defuse -h``) for more information.

Restarting workflows
====================

If you later decide you want to run a defused workflow (resume), you can use the command::

    lpad reignite -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the FireWork you want to reignite (or a list of space-separated ids). Note that all children of a reignited FireWork will also be reignited. However, parent and sibling FireWorks are *not* reignited. Note that the *reignite* command will not re-run FireWorks in a workflow that have already been run. Only FireWorks that were never run before will be run upon reignition. To re-run a FireWork, please see the :doc:`rerun tutorial </rerun_tutorial>`.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad reignite [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad reignite -h``) for more information.

Canceling and restarting individual FireWorks
=============================================

You can cancel and restart individual FireWorks instead of entire sub-Workflows using the ``lpad defuse_fws`` and ``lpad rerun_fws`` commands. See above and use the built-in help (e.g., ``lpad rerun_fws -h``) for more information.

Deleting (archiving) workflows
==============================

FireWorks does not provide a way to do a hard delete of a Workflow from its database. However, you can simulate a delete operation using the **archive** command. This command prevents all steps in a Workflow from running. It also archives any FireWorks in the Workflow that already ran, in effect simulating that they never existed. Therefore, the Workflow is for practical purposes erased. However, even archived Workflows still exists in the database, and you can query them down the road.

To archive Workflows, use the command::

    lpad archive -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the FireWork you want to defuse (or a list of space-separated ids). Note that all FireWorks in the Workflow will be archived, regardless of which **fw_id** you chose.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad archive [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad archive -h``) for more information.