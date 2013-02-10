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

* Ability to distribute the calculations over multiple worker nodes, each of which might use different a queueing system and process a different type of calculations.

* Support for *dynamic* workflows that that react to results programmatically.  You can pre-specify what actions to take depending on the output of a workflow step (canceling a workflow, restarting the current step, or completely altering the workflow)

* Detection of duplicate sub-workflows - automatically skip tasks that are duplicated between two workflows while still running unique sections

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Monitoring of workflows through a web service *(future)*

* Package many small jobs into a single large job (useful for running on HPC machines that stipulate a small number of large-CPU jobs). *(future)*

Limitations
===========

Some limitations of FireWorks include:

* FireWorks has not been stress tested to very large numbers of worker nodes.

* FireWorks is not designed to handle problems requiring movement and storage of extreme data sets (e.g., petabytes of data).

* FireWorks is not designed to be real-time workflow software. If each of your workflow steps is only a few seconds long, there might be a noticeable lag between the time one workflow step completes and the next step begins.

Getting Started
===============

To get started with FireWorks, we suggest that you follow our installation tutorial. The tutorial will help guide you through set up of both worker computers and the central computer, as well as demonstrate how to define and run basic workflows.

.. toctree::
   :maxdepth: 2
   
   installation_tutorial

.. _contributing-label:

Contributing and Contact
========================

Want to see something added or changed? There are many ways to make that a reality! Some ways to get involved are:

* Help us improve the documentation - tell us where you got 'stuck'.
* Point us to areas of the code that are difficult to understand or use.
* Tell us how you're using FireWorks, and request new features. 
* Let us know if you need support for a queueing system.
* Share code on how FireWorks might be used within a specific application.
* Get in touch and contribute to the core codebase!

The best way to submit questions, issues, and all other communication is through the `FireWorks Github page <https://github.com/materialsproject/fireworks/issues>`_. However, if you feel that e-mail is better suited for your purpose, you can contact: |Mail|

.. |Mail| image:: _static/mail.png
   :alt: developer contact
   :align: bottom

Thank yous
===========================

Michael Kocher and Dan Gunter initiated the architecture of a central database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code for pulling jobs onto nodes was refashioned for FireWorks.

Shyue Ping Ong was extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, etc. If you are in the market for a free Python materials analysis code, I highly recommend his pymatgen_ library (which I also sometimes contribute to).

Wei Chen was the first test pilot of FireWorks, and contributed greatly to improving the docs and ensuring that FireWorks installation went smoothly for others.

.. _pymatgen: http://packages.python.org/pymatgen/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

