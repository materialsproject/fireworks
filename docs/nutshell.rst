==============================
A bird's eye view of FireWorks
==============================

While FireWorks provides many features, its basic operation is simple.

Centralized Server and Worker Model
===================================

There are essentially just two components of a FireWorks installation:

* A **server** ("LaunchPad") that is used to manage workflows. You can add workflows (a DAG of "FireWorks") to the LaunchPad, query for the state of your workflows, or rerun workflows.

* One or more **workers** ("FireWorkers") that run your jobs. The FireWorkers request workflows from the LaunchPad, execute them, and send back information. The FireWorker can be as simple as the same workstation used to host the LaunchPad, or complicated like a national supercomputing center with a queueing system.

Thus, the basic infrastructure looks like this:

.. image:: _static/fw_model.png
   :width: 400px
   :align: center
   :alt: FireWorks Workflow

The components are largely decoupled, which makes installation of FireWorks straightforward. You can manage the LaunchPad (for example add new workflows) without interfering with the running operation of the FireWorkers. Similarly, if one of the FireWorkers has a failure, it won't affect the operation of the LaunchPad. Finally, this setup makes running on a heterogeneous set of FireWorkers simple - essentially the same code is used for running on a simple workstation versus a large supercomputing center.

Workflow Model
==============

Workflows in FireWorks are made up of three main components:

* A **FireTask** is an atomic computing job. It can call a single shell script or execute a single Python function that you define.
* A **FireWork** contains a *spec* that includes all the information needed to run your job. Part of the spec is an array of FireTasks that are executed in order. However, you can also include input parameters in your spec that get passed to your FireTasks. You can easily perform the same function over different input data by creating FireWorks that have the same FireTasks, but different input parameters in the specs. You can design your spec however you'd like, as long as it's valid JSON. This gives you a lot of flexibility in defining your input data.
* A **Workflow** is a set of FireWorks with dependencies between them. For example, you might need a parent FireWork to finish and generate some output files before running two child FireWorks. Between FireWorks, you can return a *FWAction* that can store data or modify the Workflow depending on the output (e.g., pass data to the next step, cancel the remaining parts of the Workflow, or even add new FireWorks that are defined within the object).

.. image:: _static/multiple_fw.png
   :width: 400px
   :align: center
   :alt: FireWorks Workflow

At this point, it may be unclear how to organize a set of computations into FireTasks, FireWorks, and Workflows. For example, for running 3 shell scripts in succession, one might choose a single FireWork with 3 FireTasks or three FireWorks that each have 1 FireTask. Both are viable options with different strengths. Over the course of the installation tutorials, we'll distinguish these a little more.

But wait - there's more!
========================

While the description above sounds simplistic, sophisticated types of workflow operation are possible with FireWorks. For example, you can:

* send different categories of FireWorks to different FireWorkers
* get the status of your all your jobs, where they're running, and how long they took to run or waited in the queue
* create and modify job priorities
* handle failures and crashes dynamically, by automatically creating FireWorks that fix crashed jobs in the FWAction object. You might even set up a workflow where a crashed job is automatically rerun at a different FireWorker, and with somewhat different parameters - no human intervention required!

We encourage you to explore all the possibilities by following the :doc:`installation tutorial</installation_tutorial>`.
