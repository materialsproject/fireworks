.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

*Note: FireWorks is under active development. It is currently incomplete and not useable as workflow software. However, certain components of the code are available for initial testing.*

FireWorks is a code for defining, managing, and executing scientific workflows. It can be used to automate most types of calculations over arbitrary computing resources.

Features
========

FireWorks is intended to be a friendly workflow software that is easy to get started with, but flexible enough to handle complicated use cases.

Some (but not all) of its features include:

* Storage and management of workflows through MongoDB, a noSQL datastore that is flexible and easy to use.

* Ability to distribute the calculations over multiple worker nodes, each of which might use different a queueing system and process a different type of calculation.

* Support for *dynamic* workflows that that react to results programmatically.  You can pre-specify what actions to take depending on the output of a job (e.g., terminate a workflow, add a new step, or completely alter the workflow)

* Automatic detection of duplicate sub-workflows - skip duplicated portions between two workflows while still running unique sections

* Loosely-coupled and modular infrastructure that is intentionally hackable. Use some FireWorks components without using *everything*, and more easily adapt FireWorks to your application.

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Monitoring of workflows through a web service *(future)*

* Package many small jobs into a single large job (useful for running on HPC machines that stipulate a small number of large-CPU jobs). *(future)*

Limitations
===========

Some limitations of FireWorks include:

* FireWorks has not been stress-tested to very large numbers of worker nodes. (If you try this, we'd love to hear the results!)

* FireWorks has not been stress-tested to hundreds or thousands of jobs in a workflow. (If you try this, we'd love to hear the results!)

* FireWorks does not automatically optimize the distribution of computing tasks over worker nodes (e.g., to minimize data movement or to match jobs to appropriate hardware); you must define such optimizations yourself.

* FireWorks has only been tested on Linux and Macintosh machines. (If you are trying to get set up on Windows, please let us know if you encounter problems)

Is FireWorks for me?
====================

It can be time-consuming to evaluate whether a workflow software will meet your computing needs from documentation alone. If you just want to know whether FireWorks is a potential solution to your workflow problem, one option is to e-mail a description of your problem to the developer at: |Mail|
   
We can tell you if:

* Your problem is a great match for FireWorks
* Your problem requires implementing minor extensions or modifications to FireWorks, but FireWorks is still a potential solution
* Your problem is not easily solved with FireWorks and you should probably look elsewhere!

Getting Started
===============

To get started with FireWorks, we suggest that you follow our core tutorials. The tutorials will guide you through set up of both worker computers and the central computer, as well as demonstrate how to define and run basic workflows.

.. toctree::
   :maxdepth: 1
   
   installation_tutorial
   installation_tutorial_pt2
   firetask_tutorial
   workflow_tutorial
   dynamic_wf_tutorial

Depending on your application, you might also be interested in the following tutorials:

.. toctree::
    :maxdepth: 1

    queue_tutorial

Planned future tutorials:

* Maintaining the FW database and dealing with crashed jobs
* Detailed tutorial on implementing dynamic jobs
* Securing the FW database
* Detailed tutorial on SubProcess Task
* File movement Task Operations
* Database Task Operations
* Assigning specific FireWorkers to run certain jobs
* Assigning and modifying job priority
* Automatically prevent duplicate jobs from running twice
* Using Python to command FireWorks
* Using a web interface to monitor FireWorks
* Checkpoint / restart of jobs
* Using the QueueLauncher outside of FW
* Searching for FireWorks and Workflows
* Logging
* FW design guide, e.g. FireTasks vs Workflows
* JSON vs. YAML and serialization of FW objects (including WF serialiazation as JSON/YAML instead of tar)


.. _contributing-label:

Contributing and Contact
========================

Want to see something added or changed? There are many ways to make that a reality! Some ways to get involved are:

* Help us improve the documentation - tell us where you got 'stuck' and improve the install process for everyone.
* Let us know if you need support for a queueing system or certain features.
* Point us to areas of the code that are difficult to understand or use.
* Share code on how FireWorks was used to solve a specific problem.
* Get in touch and contribute to the core codebase!

The collaborative way to submit questions, issues, and all other communication is through the `FireWorks Github page <https://github.com/materialsproject/fireworks/issues>`_. You can also contact: |Mail|

.. |Mail| image:: _static/mail.png
   :alt: developer contact
   :align: bottom

Thank yous
==========

Michael Kocher and Dan Gunter initiated the architecture of a central database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code was refashioned for the QueueLauncher and the PBS QueueAdapter.

Shyue Ping Ong was extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, etc. The code for modifying a FireWork specification using a dictionary (DictMod) was adapted from his custodian_ library. If you are in the market for a free Python materials analysis code, I highly recommend his pymatgen_ library (which I also sometimes contribute to).

Wei Chen was the first test pilot of FireWorks, and contributed greatly to improving the docs and ensuring that FireWorks installation went smoothly for others. In addition, he made many suggestions to improve the usability of the code.

FireWorks was developed primarily at Lawrence Berkeley National Lab using research funding from Kristin Persson for the `Materials Project <http://www.materialsproject.org>`_.

.. _pymatgen: http://packages.python.org/pymatgen/
.. _custodian: https://pypi.python.org/pypi/custodian

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`