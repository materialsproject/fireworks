===============
Worker Tutorial
===============

If you've set up your FireServer, this tutorial will help you to:

* Set up a remote worker that connects to the FireServer to retrieve and execute jobs

Like the previous tutorial, our purpose is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail. This tutorial can be safely completed from the command line, and requires no programming.

Launch a Rocket on a worker machine (FireWorker)
================================================

In the Introductory tutorial, we entered a Firework (job) in the LaunchPad (database) on the FireServer (central server). We then launched a Rocket that fetched the Firework from the database and executed it, all within the same machine.

A more interesting use case of FireWorks is to store FireWorks in the FireServer, but execute them on one or several outside 'worker' machine (FireWorkers). We'll next configure a worker machine.

Install FireWorks on the FireWorker
-----------------------------------

On the worker machine, follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

Reset the FireWorks database
----------------------------

1. Back at the **FireServer**, let's reset our database and add a Firework::

    lpad reset
    cd <INSTALL_DIR>/fw_tutorials/worker
    lpad add fw_test.yaml

Make sure to keep the MongoDB running on the FireServer, and do not launch a Rocket yet!

Connect to the FireServer from the FireWorker
---------------------------------------------

The FireWorker needs to know the login information for the FireServer. On the **FireWorker**,

1. Navigate to the worker tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/worker

   where <INSTALL_DIR> is your FireWorks installation directory.

#. Modify the ``my_launchpad.yaml`` to contain the credentials of your FireServer. In particular, the ``host`` parameter must be changed to the IP address of your FireServer.

   .. tip:: If you do not know the IP address of your FireServer and you are on a Linux machine, you can try running ``/sbin/ifconfig``.

   .. note:: The name ``my_launchpad.yaml`` is a special filename that contains your database credentials. By default, FireWorks checks for this file in the current directory. You can also specify its location manually using the ``-l`` parameter of ``lpad``, or you can :doc:`set up your configuration <config_tutorial>` to set the location of this file once and for all.

#. Confirm that you can query the FireServer from your FireWorker::

    lpad get_fws -i 1 -d all

   This should print out the description of a Firework that is *READY* to run.

   .. tip:: If you cannot connect to the database from a remote worker, you might want to check your Firewall settings and ensure that port 27017 (the default Mongo port) is open/forwarded on the central server. For Macs, you might try the `Port Map <http://www.codingmonkeys.de/portmap/>`_ application to easily open ports. If you're still having problems, you can use telnet to check if a port is open: ``telnet <HOSTNAME> <PORTNAME>``, where ``<HOSTNAME>`` is your FireServer hostname and ``<PORTNAME>`` is your Mongo port (probably 27017).


Configure your FireWorker
-------------------------

The FireWorker file contains information about this worker's configuration. Staying in the ``worker`` tutorial directory on the FireWorker, modify your ``my_fworker.yaml`` by changing the ``name`` parameter to something that will help you identify the worker that ran your Firework later on. For example, you might want to use the hostname of the worker machine.

   .. note:: The name ``my_fworker.yaml`` is a special filename that contains your FireWorker's credentials. By default, FireWorks checks for this file in the current directory. You can also specify its location manually using the ``-w`` parameter of ``lpad``, or you can :doc:`set up your configuration <config_tutorial>` to set the location of this file once and for all.

Launch a Rocket on the FireWorker
---------------------------------

#. Staying in the ``worker`` tutorial directory on your FireWorker, type::

    rlaunch singleshot

   This should successfully launch a rocket that finds and runs your Firework from the central server.

   .. tip:: Remember that we are getting database and FireWorker credentials automatically from ``my_launchpad.yaml`` and ``my_fworker.yaml``.

#. Confirm that the Firework was run::

    lpad get_fws -i 1 -d all

You should notice that the Firework is listed as being *COMPLETED*. In addition, the ``name`` parameter under the ``launches.fworker`` field should match the name that you gave to your FireWorker in ``my_fworker.yaml``. If you have multiple FireWorkers, this can help you identify where your job ran later on.

Running rapidfire mode on the FireWorker
========================================

Just like on the central server, you can run in rapidfire mode on the FireWorker to process many jobs.

1. Staying in the ``worker`` tutorial directory on your FireWorker, clean up your directory::

    rm FW.json howdy.txt

2. Add three more FireWorks. Let's do this from the FireWorker this time instead of the FireServer::

    lpad add fw_test.yaml
    lpad add fw_test.yaml
    lpad add fw_test.yaml

3. Run Rockets in rapidfire mode::

    rlaunch rapidfire

You've now run multiple jobs on your FireWorker! You could even try running the Rocket Launcher in ``--nlaunches infinite`` mode - then, you would have FireWorker that continuously ran new jobs added to the LaunchPad on the FireServer.

Setting Machine-specific or worker-specific parameter via the *env* variable
----------------------------------------------------------------------------

From v0.7.7, the FireWorker file now supports the *env* key. As its name
implies, this key allows you to specify machine-specific (or more accurately, worker-specific) environment settings.
For example, a particular command called in your FireTasks may be called
"command" in machine 1 and "command_v1.2" in machine 2. You can then abstract
out this command by specifying the differences in the FireWorker file::

    # For the FireWorker file on machine 1
    env:
        command: command

    # For the FireWorker file on machine 2
    env:
        command: command_v1.2

The env can then be accessed within your FireTasks as the "_fw_env" variable
in the fw_spec. For example, the run_task method for your FireTask may be
something like::

    def run_task(fw_spec):
        subprocess.call(fw_spec["_fw_env"]["command"])

This provides a clean way to write machine-agnostic FireTasks with an
abstraction of machine-specific commands and settings. Note that you can also use dfferent fw_env settings on the same machine if you run multiple job launch scripts using different Workers on that machine.

Next Steps
==========

A central FireServer and one or more FireWorkers pulling jobs in ``rapidfire`` mode might be all that you need to automate your application. However, if your FireWorker is a shared resource you might want to run jobs through an external queuing system rather than directly run ``rlaunch`` on your FireWorker. A description of how to run through a queue is given here:  :doc:`Launching Rockets through a queue </queue_tutorial>`. Or, you might return to the :doc:`home page <index>` and pursue a different tutorial.