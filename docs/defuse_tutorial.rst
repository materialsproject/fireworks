=======================================================
Canceling (pausing), restarting, and deleting Workflows
=======================================================

Canceling/pausing/restarting entire workflows
=============================================

You can cancel (pause) Workflows using the *defuse_wflows* command of the LaunchPad::

    lpad defuse_wflows -i <FW_IDS>

where ``<FW_IDS>`` is a numerical id of one of the FireWorks in the workflow you want to defuse (or a list of space-separated ids). This will defuse the **entire** Workflow.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``) for the workflow. The full command is thus::

     lpad defuse_wflows [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad defuse_wflows -h``) for more information.

Restarting workflows
--------------------

If you later decide you want to run a defused workflow (resume), you can use the command::

    lpad reignite_wflows -i <FW_IDS>

where ``<FW_IDS>`` is a numerical id of one of the FireWorks in the workflow you want to reignite (or a list of space-separated ids). This will **reignite** the entire Workflow. Note that the *reignite* command will not re-run FireWorks in a workflow that have already been run. Only FireWorks that were never run before will be run upon reignition. To re-run a Firework, please see the :doc:`rerun tutorial </rerun_tutorial>`.

Canceling and restarting individual FireWorks
=============================================

You can cancel and restart individual FireWorks instead of entire sub-Workflows using the ``lpad defuse_fws`` and ``lpad rerun_fws`` commands. These commands will only pause/restart the current Firework (and by extension, any dependent children), but not any parents or siblings. See above and use the built-in help (e.g., ``lpad rerun_fws -h``) for more information.

Archiving workflows
===================

There are both "hard" and "soft" deletes of jobs from the FireWorks database. The **archive** command is a soft delete that prevents all steps in a Workflow from running. It also archives any FireWorks in the Workflow that already ran, in effect simulating that they never existed. Therefore, the Workflow is for practical purposes erased. However, archived Workflows still exist in the database, and you can *query* them down the road for job provenance, but you cannot rerun them.

To archive Workflows, use the command::

    lpad archive_wflows -i <FW_IDS>

where ``<FW_IDS>`` is the numerical id of the Firework you want to defuse (or a list of space-separated ids). Note that all FireWorks in the Workflow will be archived, regardless of which **fw_id** you chose.

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad archive_wflows [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad archive_wflows -h``) for more information.

Deleting workflows
==================

The **delete** command is a hard delete that *removes all data* about a Workflow from the database.

To delete Workflows, use the command::

    lpad delete_wflows -i <FW_IDS>

Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``). The full command is thus::

     lpad delete_wflows [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad delete_wflows -h``) for more information.