===============================================================
Installation Notes on various clusters / supercomputing centers
===============================================================

This page compiles installation notes and tips for getting FireWorks working in different sites.

NERSC
=====

Loading the FireWorks code
--------------------------

You can simply load FireWorks through the NERSC modules system via::

    module unload python
    module load fireworks python

A few notes:
  * The ``module unload python`` command will unload your Python environment and load the proper Python version for the FireWorks.
  * There may be multiple options available for the FireWorks module and the Python version - they are generally labeled as "fireworks/<FW_VERSION>-<PYTHON_VERSION>". You can type ``module avail fireworks`` to see all options. If you don't see the version you want, you can contact the NERSC help desk.
  * If you want to attempt a manual install, you can follow the normal :doc:`installation instructions </installation>` but use the :doc:`virtualenv </virtualenv_tutorial>` option to make sure your $PYTHONPATH is set up correctly and to install outside of the NERSC system Python. In general this is also easy, but not as easy as the modules system.

Verifying your installation - connect to a test server
------------------------------------------------------

Follow the instructions for :ref:`remote_test-label` to test that you can connect to a FireWorks database hosted externally to NERSC. This verifies that your software installation is OK.


Installing the database
-----------------------

You'll need a MongoDB database to store your actual workflows before you get started with the tutorials. You can follow the normal :doc:`installation instructions </installation>` for installing MongoDB; for getting started at NERSC, the best option is likely the free cloud service as you don't need to install software or configure firewalls. You can also contact NERSC to see if they can host a database for your workflows; this process is slower but might be used in production. For example, NERSC hosts the production databases for the Materials Project.

Misc notes
----------

* NERSC times-out your scripts, even if they are performing actions. For example, if you are running the Queue Launcher on Hopper/Carver in infinite mode, the script will time out after a few hours. This makes it difficult to run FireWorks as a "service" that always pulls any new jobs you enter into the database over the span of days or weeks. To get around this, you can try setting up a cron job at NERSC that regularly pulls jobs from the database and submits them to the queue.
* Once you get the hang of things, make sure you set up your :doc:`configuration file <config_tutorial>` to save time and typing - in particular, set the path to your LaunchPad, FireWorker, and QueueAdapter files.

After installation
==================

After you've installed the FireWorks software and set up a Mongo database for your workflows, you should proceed with the tutorials on the :doc:`main page </index>`.