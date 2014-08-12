================================
Database administration commands
================================

There are two types of maintainence operations that can be performed through the LaunchPad:

* **maintain** - automatically detects and marks failed jobs and deleted queue reservations
* **tuneup** - tries to speed up database performance by updating indices and compacting the database. Should be performed during database downtime.

Maintain to mark failed jobs and queue reservations
===================================================

We recommend that all users periodically run the *maintain* command from the LaunchPad. This will detect failed jobs and queue reservations - for details, refer to the :doc:`failures tutorial </failures_tutorial>` and :doc:`queue reservation tutorial </queue_tutorial_pt2>`. In summary, the command will mark the state of failed jobs as *FIZZLED* and will move any long-waiting *RESERVED* FireWorks back to *READY*. The maintenance command can be run using::

    lpad admin maintain

If you would like to run maintenance in an infinite loop, you can use::

    lpad admin maintain --infinite --maintain_interval 6000

This formulation will run a maintenance job every 6000 seconds (100 minutes).

Tuneup to improve performance
=============================

You only need to run a database tuneup if you are not satisfied with the performance of FireWorks.


The tuneup will update all the indices::

    lpad admin tuneup

You can do a full tuneup which will block while updating indices and also compact the database. You should only run the full tuneup command during periods of downtime::

    lpad admin tuneup --full

Force Refresh Workflow
======================

This command should not be needed, but if you would like to force a workflow refresh you can do it via:

    lpad admin refresh_wf -i <FW_ID>

where ``<FW_ID>`` is the id of any one FW in the Workflow you want to refresh. More options are available, use ``lpad admin refresh -h`` for more information.