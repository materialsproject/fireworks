.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

*Note: FireWorks is under active development; major features are yet to be implemented, and the internal code is refactored often and not suitable for production. However, certain components of the code are available for initial testing.*

.. warning:: **The latest version of FireWorks renames the lpad.py, rlauncher.py, and qlauncher.py scripts**. The .py extension has been removed and the names shortened as requested by some users. If you are upgrading from an old installation, you should delete the old scripts (e.g., by typing ``which lp.py`` and deleting it from that location). If you have set up queueparams, you will also want to update the script specified in the ``exe`` section to read ``rlaunch`` instead of ``rlauncher_run.py``. If you encounter problems with your configuration, please contact the developer.

.. warning:: The syntax for the QueueLauncher has changed recently, i.e. you no longer need to specify ``my_queueparams.yaml`` if you specify a config dir.

.. warning:: If you encounter bugs or mismatches between the tutorials and the code, please first make sure that you have the latest version of FireWorks installed. Instructions on how to update your installation are here: :ref:`updating-label`. (This warning will be removed when FireWorks is no longer in development mode.)

FireWorks is a code for defining, managing, and executing scientific workflows. It can be used to automate most types of calculations over arbitrary computing resources, including those that have a queueing system.

Features
========

FireWorks is intended to be a friendly workflow software that is easy to get started with, but flexible enough to handle complicated use cases.

Some (but not all) of its features include:

* Storage and management of workflows through MongoDB, a noSQL datastore that is flexible and easy to use.

* Ability to distribute calculations over multiple worker nodes, each of which might use different a queueing system and process a different type of calculation.

* Support for *dynamic* workflows that that react to results programmatically.  You can pre-specify what actions to take depending on the output of a job (e.g., terminate a workflow, add a new step, or completely alter the workflow)

* Automatic detection of duplicate sub-workflows - skip duplicated portions between two workflows while still running unique sections

* Loosely-coupled and modular infrastructure that is intentionally hackable. Use some FireWorks components without using *everything*, and more easily adapt FireWorks to your application.

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Monitoring of workflows through a web service *(future)*

* Package many small jobs into a single large job (useful for running on HPC machines that prefer a small number of large-CPU jobs). *(future)*

Limitations
===========

Some limitations of FireWorks include:

* FireWorks has not been stress-tested to hundreds of jobs within a single workflow.

* FireWorks has not been stress-tested to millions of workflows.

* FireWorks does not automatically optimize the distribution of computing tasks over worker nodes (e.g., to minimize data movement or to match jobs to appropriate hardware); you must define such optimizations yourself.

* FireWorks has only been tested on Linux and Macintosh machines.

If you encounter any problems while using FireWorks, please let us know (see :ref:`contributing-label`).


Is FireWorks for me?
====================

It can be time-consuming to evaluate whether a workflow software will meet your computing needs from documentation alone. If you just want to know whether FireWorks is a potential solution to your workflow problem, one option is to e-mail a description of your problem to the developer at: |Mail|
   
We can tell you if:

* Your problem is a great match for FireWorks
* Your problem requires implementing minor extensions or modifications to FireWorks, but FireWorks is still a potential solution
* Your problem is not easily solved with FireWorks and you should probably look elsewhere!

Getting Started!
================

To get started with FireWorks, we suggest that you follow our core tutorials. These tutorials will set up a central server as well as worker computers. They will also demonstrate how to define and run basic workflows. We expect that completing all of the core tutorials will take between one and three hours. (You might want to get a snack...)

.. toctree::
   :maxdepth: 1
   
   installation_tutorial
   installation_tutorial_pt2
   firetask_tutorial
   workflow_tutorial
   dynamic_wf_tutorial

To get things running on a shared resource with a queueing system (e.g., a supercomputing center), you should complete the following tutorials:

.. toctree::
    :maxdepth: 1

    queue_tutorial
    queue_tutorial_pt2

More!
=====

We recommend that all users read the following tutorials before using FireWorks seriously:

.. toctree::
    :maxdepth: 1

    failures_tutorial
    security_tutorial
        duplicates_tutorial

Python users and Power users will be interested in the following:

.. toctree::
    :maxdepth: 1

    python_tutorial
    config_tutorial

Planned future tutorials:

* Maintaining the FW database and
* Detailed tutorial on implementing dynamic jobs
* Securing the FW database
* Detailed tutorial on Script Task
* File movement Task Operations
* Database Task Operations
* Assigning specific FireWorkers to run certain jobs
* Assigning and modifying job priority
* Using a web interface to monitor FireWorks
* Checkpoint / restart of jobs
* Using the QueueLauncher outside of FW
* Searching for FireWorks and Workflows
* Logging
* FW design guide, e.g. FireTasks vs Workflows
* JSON vs. YAML and serialization of FW objects (including WF serialiazation as TAR instead of JSON/YAML)


.. _contributing-label:

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

License
=======

FireWorks is released under a modified BSD license; the full text can be found :doc:`here</license>`.

Comprehensive Documentation
===========================

Some comprehensive documentation is listed below (only for the brave!)

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`