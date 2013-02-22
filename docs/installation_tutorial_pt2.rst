==========================================
Installation Tutorial (part 2: the Worker)
==========================================

If you've set up your FireServer, the next step is to set up worker nodes to run your jobs on a large scale (perhaps through a queuing system). This tutorial will guide you through FireWorks installation on a worker node. Like the previous tutorial, our purpose is to get you set up as quickly as possible; it isn't intended to demonstrate the features of FireWorks or explain things in great detail.

This tutorial can be safely completed from the command line, and requires no programming.

Launch a Rocket on a worker machine (FireWorker)
================================================

So far, we have added a FireWork (job) to the database on the FireServer (central server). We then launched a Rocket that fetched the FireWork from the database and executed it, all within the same machine.

A more interesting use case of FireWorks is to store FireWorks in the FireServer, but execute them on one or several outside 'worker' machine (FireWorkers), perhaps through a queueing system. We'll next configure a worker machine.

Install FireWorks on the FireWorker
-----------------------------------

On the worker machine, follow the instructions listed at :doc:`Basic FireWorks Installation </installation>`.

Reset the FireWorks database
----------------------------

1. Back at the FireServer, let's reset our database and add a FireWorks::

    launchpad_run.py initialize <TODAY'S DATE>
    launchpad_run.py insert_single_fw fw_test.yaml

Make sure to keep the FireWorks database running, and do not launch a Rocket yet!

Connect to the FireServer from the FireWorker
---------------------------------------------

The FireWorker needs to know the login information for the FireServer. On the FireWorker,

1. Navigate to the new installation tutorial directory::

    cd <INSTALL_DIR>/fw_tutorials/installation_pt2

where <INSTALL_DIR> is your FireWorks installation directory.

2. Copy the LaunchPad file to a new name::

    cp launchpad.yaml my_launchpad.yaml

3. Modify your ``my_launchpad.yaml`` to contain the credentials of your FireServer. In particular, the ``host`` parameter must be changed to the IP address of your FireServer.

3. Confirm that you can query the FireServer from your FireWorker::

    launchpad_run.py -l my_launchpad.yaml get_fw 1

This should print out the description of a FireWork that is ready to run.

.. tip:: If you cannot connect to the database from a remote worker, you might want to check your Firewall settings and ensure that port 27017 (the default Mongo port) is open/forwarded on the central server. For Macs, you might try the `Port Map <http://www.codingmonkeys.de/portmap/>`_ application to easily open ports. If you're still having problems, you can use telnet to check if a port is open: ``telnet <HOSTNAME> <PORTNAME>``, where ``<HOSTNAME>`` is your FireServer hostname and ``<PORTNAME>`` is your Mongo port (probably 27017).


Configure your FireWorker
-------------------------

Staying in the ``installation_pt2`` tutorial directory on the FireWorker,

1. Copy the FireWorker file to a new name::

    cp fworker.yaml my_fworker.yaml

2. Modify your ``my_fworker.yaml`` by changing the ``name`` parameter to something that will help you identify the worker that ran your FireWork later on. For example, you might want to use the hostname of the worker machine.

Launch a Rocket on the FireWorker
---------------------------------

1. Staying in the ``installation_pt2`` tutorial directory on your FireWorker, type::

    rocket_run.py -l my_launchpad.yaml -w my_fworker.yaml

This should successfully launch a rocket that finds and runs your FireWork from the central server.

2. Confirm that the FireWork was run::

    launchpad_run.py -l my_launchpad.yaml get_fw 1

You should notice that the FireWork is listed as being COMPLETED. In addition, the ``name`` parameter under the ``launch_data`` field should match the name that you gave to your FireWorker in ``my_fworker.yaml``.

Running loop mode on the FireWorker
-----------------------------------

Just like on the central server, you can run in loop mode on the FireWorker to process many jobs.

1. Staying in the ``installation_pt2`` tutorial directory on your FireWorker, clean up your directory::

    rm fw.json howdy.txt

2. Add three more FireWorks. Let's do this from the FireWorker this time instead of the FireServer::

    launchpad_run.py -l my_launchpad.yaml insert_single_fw fw_test.yaml
    launchpad_run.py -l my_launchpad.yaml insert_single_fw fw_test.yaml
    launchpad_run.py -l my_launchpad.yaml insert_single_fw fw_test.yaml

3. Run Rockets in loop mode::

    rocket_run.py -l my_launchpad.yaml -w my_fworker.yaml --loop

You've now run multiple jobs on your FireWorker!

Next Steps
==========

A central FireServer and one or more FireWorkers pulling jobs in loop mode might be all that you need to automate your application. However, if your FireWorker is a shared resource you might want to run jobs through an external queuing system rather than directly run ``rocket_run.py`` on your FireWorker.

If you'd like to learn how to launch jobs through a queue, continue on to the final chapter of FireWorks installation:  :doc:`Installation (part 3) </installation_tutorial_pt3>`

Otherwise, you can safely skip ahead to :doc:`defining jobs using FireTasks </task_tutorial>`.