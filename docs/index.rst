.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. title:: Introduction

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

.. raw::<div>

.. pull-quote:: | "Give me six hours to chop down a tree and I will spend the first four sharpening the axe."
                |    - Abraham Lincoln

FireWorks is a code for defining, managing, and executing scientific workflows. It can be used to automate calculations over arbitrary computing resources, including those that have a queueing system.

Some features that distinguish FireWorks are the capability to program dynamic workflows and built-in tools for running high-throughput computations at large computing centers.

.. raw::</div>

====================
Is FireWorks for me?
====================

FireWorks is intended to be a friendly workflow software that is easy to get started with, but flexible enough to handle complicated use cases.

Some (but not all) of its features include:

* Storage and management of workflows through MongoDB, a noSQL datastore that is flexible and easy to use.

* A clean and powerful Python API for defining, running, and maintaining workflows.

* Ability to distribute calculations over multiple worker nodes, each of which might use different a queueing system and process a different type of calculation.

* Support for *dynamic* workflows that that react to results programmatically.  You can pre-specify code that performs actions based on the output of a job (e.g., terminate a workflow, add a new step, or completely alter the workflow)

* Automatic detection of duplicate sub-workflows - skip duplicated portions between two workflows while still running unique sections

* Loosely-coupled and modular infrastructure that is intentionally hackable. Use some FireWorks components without using *everything*, and more easily adapt FireWorks to your application.

* Monitoring workflows with a *built-in*, easy-to-use web service

* Built-in tasks for creating templated inputs, running scripts, and copying files to remote machines

* Package many small jobs into a single large job (e.g., *automatically* run 100 serial workflows in parallel over 100 cores).

* Have fine control of job execution, including priorities and where jobs run.

* Support for several queueing systems such as PBE/Torque, Sun Grid Engine, and SLURM.

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

The FireWorks tutorials and :doc:`FW design tips <design_tips>` explain how to connect these components to achieve the desired behavior.


========================
Quickstart and Tutorials
========================

Quickstart ("Wiggle your big toe")
==================================

To get started with FireWorks, we suggest that you follow our quickstart tutorial, which should take 15 minutes for experienced Python users and covers basic installation and usage.

.. toctree::
   :maxdepth: 1

   quickstart

Basic usage
===========

After completing the quickstart, we suggest that you follow our core tutorials that cover the primary features of FireWorks. Depending on your application, you may not need to complete all the tutorials.

Designing workflows
-------------------

.. toctree::
   :maxdepth: 1

   firetask_tutorial
   workflow_tutorial
   dynamic_wf_tutorial
   design_tips

Executing workflows on different types of computing resources
-------------------------------------------------------------

.. toctree::
   :maxdepth: 1

   worker_tutorial
   queue_tutorial
   queue_tutorial_pt2
   installation_notes

Managing jobs and deployment
============================

This series of tutorials cover how to manage your jobs and deploy FireWorks in a production environment.

Job priority, cancellation, restart, and failure
------------------------------------------------

.. toctree::
    :maxdepth: 1

    priority_tutorial
    defuse_tutorial
    rerun_tutorial
    failures_tutorial
    maintain_tutorial

Monitoring FireWorks
--------------------

.. toctree::
    :maxdepth: 1

    query_tutorial
    basesite_tutorial

Deploying FireWorks in production
---------------------------------

.. toctree::
    :maxdepth: 1

    security_tutorial
    config_tutorial
    performance_tutorial

Additional features and topics
==============================

The built-in FireTasks
----------------------

.. toctree::
    :maxdepth: 1

    scripttask
    templatewritertask
    transfertask

Additional features and topics
------------------------------

.. toctree::
    :maxdepth: 1

    controlworker
    multi_job
    duplicates_tutorial
    python_tutorial

.. _contributing-label:

====================================
Contributing / Contact / Bug Reports
====================================

Want to see something added or changed? There are many ways to make that a reality! Some ways to get involved are:

* Help us improve the documentation - tell us where you got 'stuck' and improve the install process for everyone.
* Let us know if you need support for a queueing system or certain features.
* Point us to areas of the code that are difficult to understand or use.
* Contribute code! If you are interested in this option, please see our :doc:`contribution guidelines</contributing>`.

The collaborative way to submit questions, issues / bug reports, and all other communication is through the `FireWorks Github page <https://github.com/materialsproject/fireworks/issues>`_. You can also contact: |Mail|

.. |Mail| image:: _static/mail.png
   :alt: developer contact
   :align: bottom

The list of contributors to FireWorks can be found :doc:`here </contributors>`.

=========
Changelog
=========

.. toctree::
   :maxdepth: 1

   changelog

=======
License
=======

FireWorks is released under a modified BSD license; the full text can be found :doc:`here</license>`.

===========================
Comprehensive Documentation
===========================

Some comprehensive documentation is listed below (only for the brave!)

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`