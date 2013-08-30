.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

FireWorks is a code for defining, managing, and executing scientific workflows. It can be used to automate most types of calculations over arbitrary computing resources, including those that have a queueing system.

====================
Is FireWorks for me?
====================

FireWorks is intended to be a friendly workflow software that is easy to get started with, but flexible enough to handle complicated use cases.

Some (but not all) of its features include:

* Storage and management of workflows through MongoDB, a noSQL datastore that is flexible and easy to use.

* A clean and powerful Python API for defining, submitting, running, and maintaining workflows.

* Ability to distribute calculations over multiple worker nodes, each of which might use different a queueing system and process a different type of calculation.

* Support for *dynamic* workflows that that react to results programmatically.  You can pre-specify code that performs actions based on the output of a job (e.g., terminate a workflow, add a new step, or completely alter the workflow)

* Automatic detection of duplicate sub-workflows - skip duplicated portions between two workflows while still running unique sections

* Loosely-coupled and modular infrastructure that is intentionally hackable. Use some FireWorks components without using *everything*, and more easily adapt FireWorks to your application.

* Monitoring of workflows through a web service

* Batteries included (useful built-in tasks for creating templated inputs, running scripts, and even copying files to remote machines)

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Package many small jobs into a single large job (useful for running on HPC machines that prefer a small number of large-CPU jobs). *(future)*

Limitations
===========

Some limitations of FireWorks include:

* FireWorks has not been stress-tested to hundreds of jobs within a single workflow.

* FireWorks has not been stress-tested to millions of workflows.

* FireWorks does not *automatically* optimize the distribution of computing tasks over worker nodes (e.g., to minimize data movement or to match jobs to appropriate hardware); however, you can define such optimizations yourself.

* FireWorks has only been tested on Linux and Macintosh machines (and not Windows).

If you encounter any problems while using FireWorks, please let us know (see :ref:`contributing-label`).

========================
Quickstart and Tutorials
========================

Quickstart ("Wiggle your big toe")
==================================

To get started with FireWorks, we suggest that you follow our quickstart tutorial, which should take about half an hour for experienced Python users and covers basic installation and usage.

.. toctree::
   :maxdepth: 1

   birdseyeview
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

Misc. topics
------------

.. toctree::
    :maxdepth: 1

    controlworker
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