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
    * _category - For directing jobs
    * _launch_dir - For directing jobs to a certain directory

* Show to use RocketLauncher to run a particular fw_id (probably in the priorities tutorial) (note, this is already implemented, just needs documentation)

* Tell people how to run different EXE based on machine, ie.. by changing bashrc and using an alias

* Update all tutorials so config file is handled smoothly, not terribly...

* Quickstart and Installation are completely separate tutorials.

* Update all tutorials so that FireWorks have names, and lpad get_fws command uses the name of the FireWork rather than the id. Also talk about the metadata parameter of workflows

* Detailed tutorial on implementing dynamic jobs

* Give examples on how to implement certain things, e.g. a workflow where one step gives an output file used as input by the second step.

* Setting up logging (in deployment section of tutorials)

* Provide a video showing how things look in production. That way people get a quick feel for what's going to happen.

* Put the bird's eye view on the Home Page rather than as something you need to click.

* Document the FWAction (in context of writing dynamic workflows)


Major Features
==============

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location on the server, rather than scatter them amongst worker nodes?

* More and better unit tests, e.g. unit tests of scripts

* Add way to monitor a file during the run

* Implement job packing using multiprocessing first, threads later. (this probably needs some unit test)

FireTasks
=========

* Something to commit data to MongoDB

* Maybe a GridFS file storage task

* File movement tasks? including ssh transfer?

Misc.
=====

* Make it easy to set up the FW_config, my_launchpad.yaml, etc as environment variable. A separate tutorial?

* Store FW templates in "cloud". Lpad has command to read/write template to Mongo, and templatewritertask can grab template from MongoDB.

* FireTask name defaults to Class name.

* Ensure that lpad commands work in a pip installation with virtualenv.

* Detect a blank config dir and give a proper error.

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?

* Add stats, preferably using a MapReduce call for speed

* Only allow a job to be rerun if it and all children are in {FIZZLED, READY, WAITING, COMPLETED}

* Pitfall - putting the same FW in 2 workflows. Also note that RUNNING state updated a little bit after queue running state.

* keep looking for FWs with the same _fw_name, and throw an error if you find 2 with the same _fw_name

* No negative fw_ids needed when returning FWAction

* Document how to create a queue script for a new machine (and perhaps clean up the code)

* Go through logging, make sure it's sane

* Not require init.py in all tutorial dirs by fixing MANIFEST.in (somehow)

* In addition to mod_spec and dict_mod, allow a template_mod of the spec that directly acts on the JSON...