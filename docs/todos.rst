===================
FireWorks ToDo List
===================

FW Docs
=======

* describe passing of information as being like 'ports'

* describe how to pause jobs. (defuse them, and then when 'refusing' them you need to just set the state to 'WAITING' and then refresh the workflow).

* explain early on (first tutorial) that the FireServer and FireWorker are decoupled.

* Note: reserved spec keywords:
    * _tasks - a list of FireTasks to run
    * _priority - the priority of the FW
    * _dupefinder - a DupeFinder object, for avoiding duplicates
    * _queueparams - values of the QueueParams dict to override

Major Features
==============

* Add a checkpoint/restart function

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location

* More and better unit tests, e.g. unit tests of scripts

* When running a FireTask, ping the LaunchPad every once in awhile to know that all is OK...

FireTasks
=========

* Something to commit data to MongoDB
* Maybe a GridFS file storage task
* File movement tasks?

Misc.
=====

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?