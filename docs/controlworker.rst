=================================================
Controlling the directory and Worker of execution
=================================================

Controlling the directory in which a Firework is executed
=========================================================

By default, FireWorks automatically creates a datestamped directory containing each job. This directory structure can be difficult to browse through manually, or you might need your runs in a particular directory format for another reason (e.g., to be compatible with a post-processing script).

To set the directory where a Firework will execute:

#. set the ``_launch_dir`` key in your Firework *spec* to the *full path* of the directory you want to execute the Firework in.

*(that's it!)*

Potential pitfalls
------------------

While setting execution directory is simple enough, we suggest that you avoid this feature of FireWorks unless absolutely necessary. Here are a few pitfalls to consider when using this feature:

#. If you have multiple Workers, make sure that the ``_launch_dir`` you set is accessible from all Workers. Or, set things up so that only the correct Worker will pull your job (see next section).
#. If you direct multiple FireWorks into the same ``_launch_dir``, you might overwrite output files (like ``FW.json``).
#. If your code depends on having a particular directory structure in order to function, it's perhaps a sign that your code could be strengthened. For example, if you direct a job to a critical directory and it *fails* (e.g., due to a node crash), a rerun of that job might overwrite your original run because it's being directed to the same directory. This might not be your intended behavior.
#. Note that by default, FireWorks tries to clean (delete) the default FireWorks launch directory. If you find this is causing problems (it shouldn't), you can set ``REMOVE_USELESS_DIRS`` to False in the :doc:`FireWorks config </config_tutorial>`.

Alternatives to using _launch_dir
---------------------------------

Potential alternatives to using ``_launch_dir`` are:

#. If you are worried about finding your jobs on the filesystem, try :doc:`exploring all the features of LaunchPad queries <query_tutorial>`. In general, the database method of searching for jobs is much more powerful than browsing filesystems, especially if you set up your FireWorks *name* and *spec* to include things you care about in your search.
#. Another solution is to have your Firework write an empty file in its directory that has a name like "JOB--Cadmium" or "JOB--Silicon". Then you can quickly see what kind of job is in a bunch of ``launcher`` directories using a command like ``ls launcher*/JOB*`` - you'll see a list of launcher directories and which one contains "Cadmium" or "Silicon".
#. If you have a job that depends on knowing the location of other Firework runs, try writing your FireTasks to pass the location of execution to children using the *FWAction* object. Then, locations are passed dynamically in a true workflow fashion rather than hard-coded.

Of course, these are just suggestions. In the end, do what works!

Controlling the Worker that executes a Firework
===============================================

By default, any FireWorker can pull and run any Firework. However, in some cases you might want to control which computing resources should run a Firework. For example, if some of your FireWorks require a lot of memory and fast processors, you might want to direct those jobs to only a subset of FireWorkers that have sufficiently high computing specifications.

There are four methods to control where FireWorks are executed.

Method 1: Using name
--------------------

A simple method to direct FireWorks to FireWorks is by assigning the name of the resource where you want the job to run. You can do this by:

#. setting a ``_fworker`` key in your Firework spec **AND**
#. setting the ``name`` variable in your FireWorker to match that value

.. note:: Recall the ``my_fworker.yaml`` file from the :doc:`FireWorker tutorial </worker_tutorial>`. To set the FireWorker name, modify the ``name`` key.

Once you've set these values, job execution occurs as follows:

* FireWorks with a ``_fworker`` variable set will only run on a FireWorker with the exactly matching ``name`` variable.

Method 2: Using categories
--------------------------

Another simple method to direct FireWorks to FireWorks is by assigning *categories*. You can do this by:

#. setting a ``_category`` key in your Firework spec **AND**
#. setting the ``category`` variable in your FireWorker to match that value

.. note:: Recall the ``my_fworker.yaml`` file from the :doc:`FireWorker tutorial </worker_tutorial>`. To set the FireWorker category, modify this file so that the ``category`` key is non-empty.

Once you've set these values, job execution occurs as follows:

* FireWorkers with no ``category`` variable set will be able to run **any** Firework (even FireWorks with a ``_category`` key in the spec).
* FireWorkers with a ``category`` set will only run the FireWorks with an exactly matching ``_category`` variable in the Firework spec.

And finally, a few final notes and limitations about this method:

* The same ``category`` can be shared by multiple FireWorkers (if desired).
* Each FireWorker can only have a single String category
* A Firework can have an array of Strings for the ``_category`` variable, but we suggest you stick to a simple String where possible.

Method 3: Using raw queries
---------------------------

A more flexible, but less intuitive method to restrict the FireWorks that a FireWorker through a raw MongoDB query. The query will restrict the FireWorker to only running FireWorks matching the query. For example, your query might specify that the ``spec.parameter1`` is under 100. In this case, FireWorks with ``spec.parameter1`` greater than 100 must be run elsewhere.

To set up a raw query:

#. set the ``query`` variable in your FireWorker to be a JSON String that can be interpreted by Pymongo.

.. note:: Recall the ``my_fworker.yaml`` file from the :doc:`FireWorker tutorial </worker_tutorial>`. To set the FireWorker query, modify this file so that the ``query`` key is non-empty. An example of a query string in YAML format would be ``'{"spec.parameter1": {"$lte":100}}'``

Note that if you set both a category and a query for a FireWorker, both constraints will be used.

Method 4: Running child Fireworks on the same resource as the parent
--------------------------------------------------------------------

If you want the a child Firework to run on the same FireWorker as the parent, set the ``_preserve_fworker`` key in the Firework spec of the *parent* to True. This will automatically pass the ``_fworker`` of the child to be the FWorker of the parent. See :doc:`reference <reference>` for more details.