===================
FireWorks ToDo List
===================

Major Features
==============

* Allow the server to submit jobs to workers (maybe using ssh-commands?)

* Put all worker config files in a central location on the server, rather than scatter them amongst worker nodes?

* Add send e-mail?

* Global pause, and perhaps exercise this option automatically on catastrophe. Think whether it will affect offline submissions or not (probably not)

Built-in FireTasks
==================

* Maybe a GridFS file storage task

Misc.
=====

* Speed up database queries

* Make it easy to set up the FW_config, my_launchpad.yaml, etc as environment variable. A separate tutorial, or maybe a single command? e.g. lpad setup

* Store FW templates in "cloud". Lpad has command to read/write template to Mongo, and templatewritertask can grab template from MongoDB.

* FireTask name defaults to Class name.

* Detect a blank config dir and give a proper error.

* Allow FireWorks to block ports so that a parent job cannot override a setting. Maybe this is not needed?

* Add stats, preferably using a MapReduce call for speed

* Pitfall - putting the same FW in 2 workflows. Also note that RUNNING state updated a little bit after queue running state.

* No negative fw_ids needed when returning FWAction

* Go through logging, make sure it's sane

* Add option to automatically pass run dirs, e.g. send dict of {"fw_name":"run_dir"} from parents to children

* allow workflow connections to be defined by FW_name instead of by ids?

Tests
=====

* test that if two classes have the same _fw_name, that we will get an error

* test offline_mode

* More and better unit tests, e.g. unit tests of scripts

FW Docs
=======

* Put a code example up front, along with the video

* describe passing of information as being like 'ports'

* Show to use RocketLauncher to run a particular fw_id (probably in the priorities tutorial) (note, this is already implemented, just needs documentation)

* Update all tutorials so config file is handled smoothly, not terribly...

* Update all tutorials so that FireWorks have names, and lpad get_fws command uses the name of the FireWork rather than the id. Also talk about the metadata parameter of workflows

* Detailed tutorial on implementing dynamic jobs

* Give examples on how to implement certain things, e.g. a workflow where one step gives an output file used as input by the second step. Set up an example which lets you change queue parameters if the previous job FIZZLED. Examples library can point to docs because some examples are already there.

* Setting up logging (in deployment section of tutorials)

* Provide a video showing how things look in production. That way people get a quick feel for what's going to happen.

* Document the FWAction (in context of writing dynamic workflows). Make pictures for detour vs addition, etc. Show the mod_spec language (DictMod)
