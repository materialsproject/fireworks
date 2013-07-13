===================
FireWorks ToDo List
===================

FW Docs
=======

* describe passing of information as being like 'ports'

* Note: reserved spec keywords:
    * _tasks - a list of FireTasks to run
    * _priority - the priority of the FW
    * _dupefinder - a DupeFinder object, for avoiding duplicates
    * _queueadapter - values of the QueueAdapter dict to override
    * _allow_fizzled_parents - continue on FIZZLED parents

* Highlight the fact that the spec doesn't contain anything about run configuration (unless you want it to). Thus the person designing the spec or submitting jobs doesn't need to know anything about the resource it's running on. They can just set things that matter (like walltime or machine).

* Show to use RocketLauncher to run a particular fw_id (probably in the priorities tutorial) (note, this is already implemented, just needs documentation)

* Running different FireWorks on different resouces (FWorker category, FWorker query)

* Tell people how to run different EXE based on machine, ie.. by changing bashrc and using an alias

* Document all the features of Script Task

* Update all tutorials so config file is handled smoothly, not terribly...

* Update all tutorials so that FireWorks have names, and lpad get_fws command uses the name of the FireWork rather than the id.

* Detailed tutorial on implementing dynamic jobs

* Separate out the tutorial on running arbitrary Python code

* Give examples on how to implement certain things, e.g. a workflow where one step gives an output file used as input by the second step.

* Setting up logging

* Provide a video showing how things look in production. That way people get a quick feel for what's going to happen.

Major Features
==============

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location on the server, rather than scatter them amongst worker nodes?

* More and better unit tests, e.g. unit tests of scripts

* Add way to monitor a file during the run

* Change templating language to Django templates, adds dependency on Django

FireTasks
=========

* Something to commit data to MongoDB

* Maybe a GridFS file storage task

* File movement tasks? including ssh transfer?

Misc.
=====

* Detect a blank config dir and give a proper error.

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?

* Add stats, preferably using a MapReduce call for speed

* Clean up job_exists() calls - they are currently expensive!

* Only allow a job to be rerun if it and all children are in {FIZZLED, READY, WAITING, COMPLETED}

* Pitfall - putting the same FW in 2 workflows. Also note that RUNNING state updated a little bit after queue running state.

* No negative fw_ids needed when returning FWAction

* Go through logging, make sure it's sane