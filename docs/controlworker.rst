========================================
Controlling where FireWorks are executed
========================================

By default, any FireWorker can pull and run any FireWork. However, in some cases you might want to control which computing resources should run a FireWork. For example, if some of your FireWorks require a lot of memory and fast processors, you might want to direct those jobs to only a subset of FireWorkers that have sufficiently high computing specifications.

There are two methods to control where FireWorks are executed.

Method 1: Using categories
==========================

A simple method to direct FireWorks to FireWorks is by assigning *categories*. You can do this by:

#. setting a ``_category`` key in your FireWork spec **AND**
#. setting the ``category`` variable in your FireWorker to match that value

.. note:: Recall the ``my_fworker.yaml`` file from the :doc:`FireWorker tutorial </worker_tutorial>`. To set the FireWorker category, modify this file so that the ``category`` key is non-empty.

Once you've set these values, job execution occurs as follows:

* FireWorkers with no ``category`` variable set will be able to run **any** FireWork (even FireWorks with a ``_category`` key in the spec).
* FireWorkers with a ``category`` set will only run the FireWorks with an exactly matching ``_category`` variable in the FireWork spec.

And finally, a few final notes and limitations about this method:

* The same ``category`` can be shared by multiple FireWorkers (if desired).
* Each FireWorker can only have a single String category
* A FireWork can have an array of Strings for the ``_category`` variable, but we suggest you stick to a simple String where possible.

Method 2: Using raw queries
===========================

A more flexible, but less intuitive method to restrict the FireWorks that a FireWorker through a raw MongoDB query. The query will restrict the FireWorker to only running FireWorks matching the query. For example, your query might specify that the ``spec.parameter1`` is under 100. In this case, FireWorks with ``spec.parameter1`` greater than 100 must be run elsewhere.

To set up a raw query:

#. set the ``query`` variable in your FireWorker to be a JSON String that can be interpreted by Pymongo.

.. note:: Recall the ``my_fworker.yaml`` file from the :doc:`FireWorker tutorial </worker_tutorial>`. To set the FireWorker query, modify this file so that the ``query`` key is non-empty. An example of a query string in YAML format would be ``'{"spec.parameter1": {"$lte":100}}'``

Note that if you set both a category and a query for a FireWorker, both constraints will be used.
