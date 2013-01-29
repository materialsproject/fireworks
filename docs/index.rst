.. FireWorks documentation master file, created by
   sphinx-quickstart on Fri Jan 11 16:36:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/FireWorks_logo.png
   :width: 300 px
   :alt: FireWorks

*Note: FireWorks is under active development. It is currently incomplete and not useable as workflow software. However, certain components of the code are available for initial testing.*

FireWorks allows you to define calculation workflows and execute them on remote
computers, usually through an external queuing system like PBS. The architecture of FireWorks is that of a central management server that stores and maintains the workflows, and a reasonable number of worker computers that pull jobs and perform the computations.

Features
========

FireWorks allows you to:

* Store and query workflows through MongoDB.

* Distribute calculations over multiple computing resources simultaneously, and direct certain workflows to intended worker computers.

* Define *dynamic* workflows that that react to results programmatically.  You can pre-specify what actions to take depending on the output of a workflow step (canceling a workflow, restarting the current step, or completely altering the workflow)

* Automatically detect duplicate sub-workflows - avoid re-running the duplicated sections of a workflow while still running unique sections

* Plug-and-play on several large supercomputing clusters and queueing systems *(future)*

* Web-based monitoring of workflows *(future)*

* Tools for packaging many small jobs into a single large job (useful for running on HPC machines that stipulate a small number of large-CPU jobs). *(future)*

Limitations
===========

FireWorks is intended for applications where realtime performance of the workflow software is not a big issue. For example, if you require steps in a workflow to execute within a few seconds of one another, FireWorks might not be for you. In addition, FireWorks has only been tested for a few worker nodes running simultaneously, and has not been stress-tested for hundreds of worker nodes.

Contributing
============

There are many ways to help make FireWorks better. Many of them involve very little time and effort but would be of great use to the developers. Some ways to get involved are:

* Send a note about how you're using FireWorks, and features you might like to see. 
* Send a note about how the documentation might be improved. We'd like FireWorks to be frustration-free, and if you've encountered a stumbling block chances are others are also getting stuck. Sometimes, a little bit of extra explanation goes a long way!
* Send a note about areas of the code that are difficult to understand. We want FireWorks to be easy to read, modify, and maintain.
* Develop adapters for your queuing system or computing center, and share them with the main repo.
* Share code on how FireWorks might be used within a specific application
* Get in touch and contribute to the core codebase. 

Technical Issues
================
Installation
------------

* Use pip-install
* run python setup.py nosetests


Setup on clusters / Tutorial (Future)
-------------------------------------

*TODO: link to another page...*

*TODO: add proper docs*

1. Create a subclass of QueueAdapter that handles queue issues - an example is PBSAdapterNersc

2. Create an appropriate JobParameters file for your cluster - an example is provided.

3. Try running rocket_launcher.py on your cluster with a test job config. See if it prints 'howdy, you won' or whatever.

4. Try changing the executable to be the Rocket. See if it grabs a job properly...

Thank yous
================
Michael Kocher, Shyue Ping Ong

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

