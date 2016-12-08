=======================================================
Canceling (pausing), restarting, and deleting Workflows
=======================================================

Canceling/pausing/restarting entire workflows
=============================================

You can pause Workflows in one of two ways: *pausing* them and *defusing* them. Both method do essentially the same thing,
except that defusing Fireworks can be done programmatically via a *FWAction* and is often associated with something going "wrong".

To pause a Workflow::

    lpad pause_wflows -i <FW_IDS>

To defuse a Workflow::

    lpad defuse_wflows -i <FW_IDS>

where ``<FW_IDS>`` is a numerical id of one of the FireWorks in the workflow you want to defuse (or a list of space-separated ids). Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``) for the workflow. The full command is thus::

     lpad defuse_wflows [-i FW_ID] [-n NAME] [-s STATE] [-q QUERY]

Refer to the documentation (``lpad pause_wflows -h`` and ``lpad defuse_wflows -h``) for more information.

Restarting workflows
--------------------

If you *paused* a Workflow, you can resume the entire workflow using::

    lpad rerun_fws -i <FW_IDS>

Note that this will rerun any existing run data in the Firework.

The equivalent command if you *defused* a Workflow is::

    lpad reignite_wflows -i <FW_IDS>

where ``<FW_IDS>`` is a numerical id of one of the FireWorks in the workflow you want to reignite (or a list of space-separated ids). This will **reignite** the entire Workflow. Note that the *reignite* command will not re-run FireWorks in a workflow that have already been run. Only FireWorks that were never run before will be run upon reignition. You can also rerun a defused Firework, please see the :doc:`rerun tutorial </rerun_tutorial>`.

Canceling and restarting individual FireWorks
=============================================

You can cancel and restart individual FireWorks instead of entire sub-Workflows.

To pause an individual Firework, use::

    lpad pause_fws -i <FW_IDS>

To resume/restart an individual Firework that was previously *paused*, use::

    lpad resume_fws -i <FW_IDS>

To defuse an individual Firework, use::

    lpad defuse_fws -i <FW_IDS>

To resume/restart an individual Firework that was previous *defused*, use::

    lpad reignite_fws -i <FW_IDS>

where ``<FW_IDS>`` is a numerical id of one of the FireWorks in the workflow you want to defuse (or a list of space-separated ids). Instead of specifying ids, you can also specify a name (``-n``), a state (``-s``), or a custom query (``-q``) for the Firework.

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
