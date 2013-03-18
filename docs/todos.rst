===================
FireWorks ToDo List
===================

FW Docs
=======

* describe passing of information as being like 'ports'

* describe how to pause jobs. (defuse them, and then when 'refusing' them you need to just set the state to 'WAITING' and then refresh the workflow).

* Note: reserved spec keywords:
    * _tasks - a list of FireTasks to run
    * _priority - the priority of the FW
    * _dupefinder - a DupeFinder object, for avoiding duplicates
    * _queueparams - values of the QueueParams dict to override

* Show to use RocketLauncher to run a particular fw_id (probably in the priorities tutorial) (note, this is already implemented, just needs documentation)

Major Features
==============

* Figure out what to do about fsync

* Add a checkpoint/restart function

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location

* More and better unit tests, e.g. unit tests of scripts

FireTasks
=========

* Something to commit data to MongoDB
* Maybe a GridFS file storage task
* File movement tasks?

Misc.
=====

# Detect a blank config dir and give a proper error.

* Update all tutorials for the config directory option rather than individual files.

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?

* Standard setup instructures for big supercomputing facilities  - NERSC. Teragrid, etc (e.g. things like module load Python/2.7, also virtualenv)

* Install using pip only, not Github devleopers! Package the tutorial separately.

* <INSTALL_DIR> is only installation from the perspective the the "develop" command to setup.py, which users won't think of as installation. Maybe clarify.