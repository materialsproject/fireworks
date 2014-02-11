==================
Reference material
==================

Interpretation of 'state' of FWs and WFs
========================================

Recall that a Workflow is a composed of one or more FireWorks. Both FireWorks and Workflows have a *state* (status).

You can get the states of FireWorks and Workflows using :doc:`LaunchPad queries </query_tutorial>` or through the :doc:`web interface </basesite_tutorial>`.

FireWorks states
----------------

A FireWork state represents the status of a single job.

============  ==============
  **State**    **Meaning**
------------  --------------
ARCHIVED      Similar to *deleted*. The FireWork will not run, and its launches are archived (won't be used in duplicate checking). However, you can still query the FireWork. More information :doc:`here </defuse_tutorial>`.
DEFUSED       The FireWork is canceled/paused. Child FireWorks won't run (although siblings might). The FireWork can be resumed (*reignited*) later. More information :doc:`here </defuse_tutorial>`.
WAITING       The FireWork is waiting for a parent FireWork to complete. The Rocket Launcher will not pull this FireWork until parent jobs complete.
READY         This FireWork is ready to run, but hasn't started running yet. The Rocket Launcher must pull this job and start running it.
RESERVED      (Queue Launcher in reservation mode only). The FireWork is waiting in a queue to run. More information :doc:`here </queue_tutorial_pt2>`.
FIZZLED       The FireWork has failed; it was executed but threw an error during the process. It can be rerun if desired - more information :doc:`here </failures_tutorial>`.
RUNNING       The FireWork is currently running. Note that in catastrophic cases, a FireWork may display this state even though it has crashed; more information :doc:`here </failures_tutorial>`.
COMPLETED     The FireWork has successfully finished running.
============  ==============


Workflows states
----------------

The state of a Workflow depends on the states of its component FireWorks.

============  ==============
  **State**    **Meaning**
------------  --------------
ARCHIVED      Similar to *deleted*. All the individual FireWork states are ARCHIVED.
COMPLETED     All the individual FireWork states are COMPLETED - the workflow is finished.
DEFUSED       At least *one* FireWork in the workflow is DEFUSED. (If you have a branching workflow, other FireWorks might be running).
FIZZLED       At least *one* FireWork in the workflow is FIZZLED and no FWs are DEFUSED. (If you have a branching workflow, other FireWorks might be running).
RUNNING       At least one FireWork is RUNNING or COMPLETED. This state means that workflow has started but is not yet fully complete.
RESERVED      No FireWorks are RUNNING or COMPLETED, but at least one FireWork has been submitted to the queue.
READY         The workflow has not started running and no FireWorks are reserved to run.
============  ==============

Reserved keywords in FW spec
============================

The FW spec has certain **reserved keywords** that indicate special instructions to the FireWorks software. They are listed below:

======================  ==============
**Keyword**             **Meaning**
----------------------  --------------
_tasks                  Reserved for specifying the list of FireTasks in the spec.
_priority               Used to specify the job's priority. More information :doc:`here </priority_tutorial>`.
_launch_dir             Pre-specify the directory to run the job rather than using default FW directory. More information :doc:`here </controlworker>`.
_category               Used to control what resources run this job. More information :doc:`here </controlworker>`.
_queueadapter           Special queue parameters for this job. More information :doc:`here </queue_tutorial_pt2>`.
_dupefinder             Used to specify a duplicate finder object for avoiding duplicated runs. More information :doc:`here </duplicates_tutorial>`.
_allow_fizzled_parents  Run this FireWork if all parents are *either* COMPLETED or FIZZLED.
_fizzled_parents        Reserved for automatically putting information about FIZZLED parents in a child FireWork with the ``_allow_fizzled_parents`` option.
_trackers               Reserved for specifying Trackers.
_background_tasks       Reserved for specifying BackgroundTasks
======================  ==============