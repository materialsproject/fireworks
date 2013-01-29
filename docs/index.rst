.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

*Note: FireWorks is under active development. It is currently incomplete and not useable as workflow software. However, certain components of the code are available for initial testing.*

FireWorks allows you to define calculation workflows and execute them on remote
computers, usually through an external queuing system like PBS. The architecture of FireWorks is that of a central management server that stores and maintains the workflows, along with one or more worker computers that pull jobs and perform the computations.

Features
========

FireWorks allows you to:

* Store and query workflows through MongoDB.

* Distribute calculations over multiple computing resources simultaneously, and direct certain workflows to intended worker computers.

* Define *dynamic* workflows that that react to results programmatically.  You can pre-specify what actions to take depending on the output of a workflow step (canceling a workflow, restarting the current step, or completely altering the workflow)

* Automatically detect duplicate sub-workflows - avoid re-running the duplicated sections of a workflow while still running unique sections

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Monitoring of workflows through a web service *(future)*

* Package many small jobs into a single large job (useful for running on HPC machines that stipulate a small number of large-CPU jobs). *(future)*

Limitations
===========

FireWorks is currently intended for applications where performance of the workflow software is not of utmost concern:

* If you require steps in a workflow to execute within a few seconds of one another, the current version of FireWorks is not for you.

* FireWorks has only been tested for a few worker nodes running simultaneously, and has not been stress-tested for hundreds of worker nodes.

.. _contributing-label:

Contributing
============

Want to see something added or changed? There are many ways to help make that a reality. Some ways to get involved are:

* Help us improve the documentation - direct us to errors or areas that could be clearer. We want getting set up and using FireWorks to be a breeze for everyone.
* Point us to areas of the code that are difficult to understand or use. We hope to make FireWorks easy to understand, modify, and maintain.
* Tell us how you're using FireWorks, and request new features. 
* Develop adapters for your queuing system or computing center, and share them with the main repo.
* Share code on how FireWorks might be used within a specific application.
* Get in touch and contribute to the core codebase!

The best way to submit questions, issues, and all other communication is through the FireWorks Github page: https://github.com/materialsproject/fireworks/issues

The Github page is the preferred way of communication because it allows issues and requests to be tracked and shared. However, if you feel that e-mail is better suited for your purpose, you can contact: |Mail|

.. |Mail| image:: _static/mail.png
   :alt: developer contact
   :align: bottom

Getting Started
===============

To get started with FireWorks, we suggest that you follow our installation tutorial. The tutorial will help guide you through set up of both worker computers and the central computer, as well as demonstrate how to define and run basic workflows.

.. toctree::
   :maxdepth: 2
   
   installation_tutorial

Going Further
=============

**TODO: add another tutorial here...**

Thank yous and Contributors
===========================

Michael Kocher and Dan Gunter initiated the architecture of a central database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code for pulling jobs onto nodes was refashioned for FireWorks.

Shyue Ping Ong was extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, etc. If you are in the market for a free Python materials analysis code, I highly recommend his pymatgen_ library (which I also sometimes contribute to).

.. _pymatgen: http://packages.python.org/pymatgen/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

