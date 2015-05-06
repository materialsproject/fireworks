===================
FireWorks ToDo List
===================

Major Features
==============

* Put all worker config files in a central location on the server, rather than scatter them amongst worker nodes?

* Add send e-mail?

* Global pause, and perhaps exercise this option automatically on catastrophe. Think whether it will affect offline submissions or not (probably not)

Built-in FireTasks
==================

* Maybe a GridFS file storage task

Misc.
=====

* Make it easy to pass directories between jobs, e.g. "_pass_dir: True" in spec.

* Tools for unreserving a FW

* remove use_global_spec option, and just have the parameters be taken from the root spec and overridden by the task parameters.

* Speed up database queries

* Make it easy to set up the FW_config, my_launchpad.yaml, etc as environment variable. A separate tutorial, or maybe a single command? e.g. lpad setup

* Store FW templates in "cloud". Lpad has command to read/write template to Mongo, and templatewritertask can grab template from MongoDB.

* Detect a blank config dir and give a proper error.

* Pitfall - putting the same FW in 2 workflows. Also note that RUNNING state updated a little bit after queue running state.

* No negative fw_ids needed when returning FWAction

* Go through logging, make sure it's sane

* Add option to automatically pass run dirs, e.g. send dict of {"fw_name":"run_dir"} from parents to children

* change docstring format to Google-style like pymatgen

Tests
=====

* test offline_mode

* overriding queue parameters test

* unit tests of passing spec amongst firetasks

* change tests to use mongomock

FW Docs
=======

* Clean up docs regarding custom FireTasks. It is part of the basic tutorial AND partly in the comprehensive guide, with no links between the two. Also the basic tutorial should introduce PyTask.

* Put a code example up front, along with the video

* describe passing of information as being like 'ports'

* Show to use RocketLauncher to run a particular fw_id (probably in the priorities tutorial) (note, this is already implemented, just needs documentation)

* Update all tutorials so config file is handled smoothly, not terribly...and clean up options like CONFIG_FILE_LOC, make .fireworks dir integration more clear, etc...

* Update all tutorials so that FireWorks have names, and lpad get_fws command uses the name of the Firework rather than the id. Also talk about the metadata parameter of workflows

* Give examples on how to implement certain things, e.g. a workflow where one step gives an output file used as input by the second step. Set up an example which lets you change queue parameters if the previous job FIZZLED. Examples library can point to docs because some examples are already there.

* Setting up logging (in deployment section of tutorials)

* Finish duplicates tutorial, and add a principles of duplicate checking section (same spec is the same job and will give the same Launch action, Launch object contains action, etc.)

* Provide a video showing how things look in production. That way people get a quick feel for what's going to happen.