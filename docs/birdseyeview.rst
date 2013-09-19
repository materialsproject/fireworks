==============================
A bird's eye view of FireWorks
==============================

While FireWorks provides many features, its basic operation is simple. You can run FireWorks on a single laptop or at a supercomputing center.

Centralized Server and Worker Model
===================================

There are essentially just two components of a FireWorks installation:

* A **server** ("LaunchPad") that manages workflows. You can add workflows (a DAG of "FireWorks") to the LaunchPad, query for the state of your workflows, or rerun workflows.

* One or more **workers** ("FireWorkers") that run your jobs. The FireWorkers request workflows from the LaunchPad, execute them, and send back information. The FireWorker can be as simple as the same workstation used to host the LaunchPad, or complicated like a national supercomputing center with a queueing system.

The basic infrastructure looks like this:

.. image:: _static/fw_model.png
   :width: 400px
   :align: center
   :alt: FireWorks Model

The components are largely decoupled, which makes FireWorks easier to use. End users can add new workflows to the LaunchPad without worrying about the details of how and where the workflows will be run (unless they really want to tailor the details of job execution). This keeps the workflow specifications lightweight, tidy, and easy to learn and use (if you've ever seen lengthy XML-based specifications in other workflow software, you'll notice the difference in FireWorks right away).

On the opposite end, administrators can configure worker computers without worrying about where workflows are coming from or what they look like (although you can assign jobs to certain resources if desired). Running on a heterogeneous set of worker computers is simple because essentially the same code is used internally by FireWorks for running on a simple workstation, a large supercomputing center, or packing together many jobs into a single queue submission.

.. _wfmodel-label:

Workflow Model
==============

Workflows in FireWorks are made up of three main components:

* A **FireTask** is an atomic computing job. It can call a single shell script or execute a single Python function that you define (either within FireWorks, or in an external package). Each FireTask receives input data in the form of a JSON specification. *Note: if you want to run non-Python code (e.g., C++ or Java code), you must either call the code as a shell script or write a Python function that executes your code (perhaps using a Python binding to that language for tighter integration).*
* A **FireWork** contains the JSON *spec* that includes all the information needed to bootstrap your job. For example, the spec contains an array of FireTasks to execute in sequence. The spec also includes any input parameters to pass to your FireTasks. You can easily perform the same function over different input data by creating FireWorks with identical FireTasks but different input parameters in the spec. You can design your spec however you'd like, as long as it's valid JSON. The JSON format used for FireWork specs is extremely flexible, very easy to learn (Python users familiar with *dicts* and *arrays* essentially already know JSON), and immediately makes rich searches over the input data available to end users through MongoDB's JSON document search capabilities.
* A **Workflow** is a set of FireWorks with dependencies between them. For example, you might need a parent FireWork to finish and generate some output files before running two child FireWorks.

Between FireWorks, you can return a **FWAction** that can store data or modify the Workflow depending on the output (e.g., pass data to the next step, cancel the remaining parts of the Workflow, or even add new FireWorks that are defined within the object).

.. image:: _static/multiple_fw.png
   :width: 400px
   :align: center
   :alt: FireWorks Workflow

At this point, you may be wondering how to organize a set of computations into FireTasks, FireWorks, and Workflows. For example, to run 3 shell scripts in succession, one might choose a single FireWork with 3 FireTasks or three FireWorks that each have 1 FireTask. Both are viable options with different strengths and possibilities. Over the course of the FireWorks tutorials, we'll distinguish these a little more (in particular, in the :doc:`FW design tips <design_tips>`).

But wait - there's more!
========================

While the description above sounds simplistic, sophisticated types of workflow operation are possible with FireWorks. For example, you can:

* send different categories of FireWorks to different FireWorkers
* get the status of your all your jobs, where they're running, and how long they took to run or waited in the queue
* create and modify job priorities
* pack small jobs into larger ones (e.g define 1000 serial workflows and automatically parallelize them over 100 processors).
* automatically prevent duplicating runs, even if different users submit the same thing to the LaunchPad
* handle failures and crashes dynamically, by automatically creating FireWorks that fix crashed jobs in the FWAction object. You might even set up a workflow where a crashed job is automatically rerun at a different FireWorker, and with somewhat different parameters - no human intervention required!

If this sounds good, we encourage you to get started by following the :doc:`quickstart</quickstart>`.
