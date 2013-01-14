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
FireWorks might not be for you.

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