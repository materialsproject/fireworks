=============================
FireWorks workflow management
=============================

FireWorks allows you to define calculation workflows and execute them on remote
computers, usually through a queueing system. Workflows are stored in a centralized
database, and jobs are pulled from the database by registered computers.


Features
========

Unique features of FireWorks include:

* Dynamic workflows that react to results programmatically. A job can be automatically restarted, modified, or cancelled in case of error or other condition. Entire workflows can be changed automatically based on calculation results.

* Distribute calculations over multiple computing resources simultaneously.

* Automated duplicate workflow detection

* Plug-and-play on several large supercomputing clusters and queueing systems (future)

* Web-based monitoring of workflows (future)

Limitations
===========

FireWorks is intended for applications where realtime performance of the workflow software is not
a big issue. For example, if you require steps in a workflow to execute within a few seconds of one another,
FireWorks might not be for you. In addition, FireWorks is a centralized workflow system.

Contributing
============
*TODO: add description*

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