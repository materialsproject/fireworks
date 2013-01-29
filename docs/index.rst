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
==============

*Currently, we suggest that you install FireWorks in developer mode using the instructions below rather than using pip or easy-install.*

**Note:** We suggest that you begin by installing FireWorks on one of your worker computers, as this more naturally follows the tutorial on FireWorks setup.

Install required software
-------------------------
To prepare for installation, you should:

1. Install `git <http://git-scm.com>`_, if not already packaged with your system. This will allow you to download the latest source code.
2. Install `pip <http://www.pip-installer.org/en/latest/installing.html>`_, if not already packaged with your system. This will allow you to download required dependencies.

Download FireWorks and dependencies
-----------------------------------
1. Run the following code to download the FireWorks source::

    git clone git@github.com:materialsproject/fireworks.git

2. Navigate inside the FireWorks directory containing the file setup.py and run the following command (you might need administrator privileges, so pre-pend the word 'sudo' as needed)::

    python setup.py develop

3. Install the needed dependencies using pip with the following commands (with administrator privileges)::

    pip install nose
    pip install pyyaml
    pip install simplejson

Run unit tests
--------------
1. Staying in the directory containing setup.py, run the following command::

    nosetests
    
2. Ideally, a printout should indicate that all tests have passed. If not, you might try to debug based on the error indicated, or you can let us know the problem so we can improve the docs (see :ref:`contributing-label`).

Next steps - set up workers and central server
---------------------------------------------

**Note: this part is not yet written properly! Please disregard!!**

If all the unit tests pass, you are ready to begin setting up your workers and central server. Follow the installation tutorial to guide you through this process.

1. Create a subclass of QueueAdapter that handles queue issues - an example is PBSAdapterNersc

2. Create an appropriate JobParameters file for your cluster - an example is provided.

3. Try running rocket_launcher.py on your cluster with a test job config. See if it prints 'howdy, you won' or whatever.

4. Try changing the executable to be the Rocket. See if it grabs a job properly...

Thank yous and Contributors
===========================

Michael Kocher and Dan Gunter initiated the architecture of a central database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code for pulling jobs onto nodes was refashioned for FireWorks.

Shyue Ping Ong was extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, etc. If you are in the market for a free Python materials analysis code, I highly recommend his pymatgen_ library (which I also sometimes contribute to).

.. _pymatgen: http://packages.python.org/pymatgen/

.. toctree::
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

