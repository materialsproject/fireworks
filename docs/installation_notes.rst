===============================================================
Installation Notes on various clusters / supercomputing centers
===============================================================

This page compiles installation notes and tips for getting FireWorks working in different sites.

NERSC - (Hopper, Carver)
========================

* When following the installation instructions, use the :doc:`virtualenv </virtualenv_tutorial>` option to make sure your $PYTHONPATH is set up correctly.
* Make sure you use ``module load python/2.7``, or ``module load python/2.7.3``. Perhaps put this in your ``.bashrc.ext``.
* You will probably need to initialize your central server somewhere at NERSC, otherwise coordinate with NERSC staff so that your external database is accessible from the NERSC firewall. In general hosting a database in your office will not work due to the firewalls on NERSC machines.
* Currently only Carver has Mongo installed, and it's a very old version (Mongo < 2.0). We coordinated with NERSC staff to host our FireWorks database for us on one of their nodes, with a newer version of Mongo installed (2.2)
* NERSC times-out your scripts, even if they are performing actions. For example, if you are running the Queue Launcher on Hopper/Carver in infinite mode, the script will time out after a few hours. This makes it difficult to run FireWorks as a "service" that always pulls any new jobs you enter into the database over the span of days or weeks. To get around this, you'd have to coordinate with NERSC staff, or write a script/macro that pretends to type commands in your terminal window to keep it alive (the latter is not a recommended solution, but has been known to be used even by NERSC staff...)
* Make sure you set up your :doc:`configuration file <config_tutorial>` to save headaches - in particular, set the path to your LaunchPad, FireWorker, and QueueAdapter files.
