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

* Figure out what to do about fsync (in progress...)

* Add a checkpoint/restart function

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location on the server, rather than scatter them amongst worker nodes?

* More and better unit tests, e.g. unit tests of scripts

FireTasks
=========

* Something to commit data to MongoDB
* Maybe a GridFS file storage task
* File movement tasks?

Misc.
=====

* Detect a blank config dir and give a proper error.

* It's too easy to mess up the FWAction, and then debugging is a pain. e.g. need a dict_mods key, make sure the dict_mods is a list, make sure no $ sign, etc... One option is to allow a simple dict.update() instead of the Mongo language.

* RUNTIME key not there in launches?

* allow environment varialbe to set config dir location

* Finish all planned tutorials

* Add warning or reject if you try to add a FW with FW_id > 1

* Update all tutorials for the config directory option rather than individual files.

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?

* Standard setup instructures for big supercomputing facilities  - NERSC. Teragrid, etc (e.g. things like module load Python/2.7, also virtualenv)

* Install using pip only, not Github devleopers! Package the tutorial separately.

* Fully support .tar?

* Clean up job_exists() calls - they are now expensive!

* <INSTALL_DIR> is only installation from the perspective the the "develop" command to setup.py, which users won't think of as installation. Maybe clarify.

Potential bugs?
===============

1) Add two duplicated workflows. Run the rapidfire rocketlauncher.