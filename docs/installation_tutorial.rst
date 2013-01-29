=====================
Installation Tutorial
=====================

This tutorial will guide you through FireWorks installation on worker nodes, test communication with the queue, and submit some placeholder jobs.

Set up worker nodes
===================

Install FireWorks on the worker
-------------------------------
To install FireWorks on the worker, please follow the instructions listed at :doc:`Installation on a machine </installation>`

Test FireWorks on the worker
----------------------------

Next steps - set up workers and central server
---------------------------------------------

**Note: this part is not yet written properly! Please disregard!!**

If all the unit tests pass, you are ready to begin setting up your workers and central server. Follow the installation tutorial to guide you through this process.

1. Create a subclass of QueueAdapter that handles queue issues - an example is PBSAdapterNersc

2. Create an appropriate JobParameters file for your cluster - an example is provided.

3. Try running rocket_launcher.py on your cluster with a test job config. See if it prints 'howdy, you won' or whatever.

4. Try changing the executable to be the Rocket. See if it grabs a job properly...