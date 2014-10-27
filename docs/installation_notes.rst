===============================================================
Installation Notes on various clusters / supercomputing centers
===============================================================

This page compiles installation notes and tips for getting FireWorks working in different sites.

NERSC
=====

Installing the FireWorks code
-----------------------------

We are working on having FireWorks being loadable through the modules system, such that a user can simply do "module load FireWorks" in the future and skip the rest of this subsection.

However, at the moment one must install FireWorks manually.

* Make sure you use ``module load python/2.7``, or ``module load python/2.7.x``. Perhaps put this in your ``.bashrc.ext``.
* Follow the normal :doc:`installation instructions </installation>` with the following modifications:
    * You can skip MongoDB installation for the moment, we will do that next
    * Use the :doc:`virtualenv </virtualenv_tutorial>` option to make sure your $PYTHONPATH is set up correctly and to install outside of the NERSC system Python.

Verifying your installation - connect to a test server
------------------------------------------------------

Follow the instructions for :ref:`remote_test-label`.


Installing the database
-----------------------

You'll need a MongoDB database to store your actual workflows before you get started with the tutorials. Follow the normal :doc:`installation instructions </installation>` for installing MongoDB. For getting started, the best option is likely the free cloud service. You can also contact NERSC to see if they can host a database for your workflows; this process is slower but might be used in production. For example, NERSC hosts the production databases for the Materials Project.

Misc notes
----------

* NERSC times-out your scripts, even if they are performing actions. For example, if you are running the Queue Launcher on Hopper/Carver in infinite mode, the script will time out after a few hours. This makes it difficult to run FireWorks as a "service" that always pulls any new jobs you enter into the database over the span of days or weeks. To get around this, you can try setting up a cron job at NERSC.
* Once you get the hang of things, make sure you set up your :doc:`configuration file <config_tutorial>` to save headaches - in particular, set the path to your LaunchPad, FireWorker, and QueueAdapter files.