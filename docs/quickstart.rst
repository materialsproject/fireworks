=====================
Five-minute quickstart
=====================

In this quickstart, you will:

* Add a simple workflow to the central database via the command line
* Run that workflow
* Monitor your job status with the FireWorks database
* Get a flavor of the Python API

This tutorial will emphasize "hands-on" usage of FireWorks via the command line and not explain things in detail.

Start FireWorks
===============

#. If not already running, start MongoDB::

    mongod --logpath <FILENAME_TO_LOG_TO> --fork

.. note::

    If MongoDB is outputting a lot of text, you might want to start it in a
    dedicated Terminal window or use the ``--quiet`` option. In addition, if
    you are running it on a shared machine, make sure that the ``--dbpath``
    variable is set to a directory that you can access. You may also wish to
    set up your Mongo config in a file and use the --config option.

#. Reset/Initialize the FireWorks database (the LaunchPad)::

    lpad reset

  .. note:: If your FireWorks database is located on a different computer from your FireWorks installation, navigate to the computer containing FireWorks and type ``lpad init``. This will set up a file that points to your remote database. You can now run ``lpad`` commands from within this directory. Alternatively, use the ``lpad -l`` option to point to this file or set up this file as your default db location using the :doc:`FW config </config_tutorial>`.

  .. note:: All FireWorks commands come with built-in help. For example, type ``lpad -h`` or ``lpad reset -h``. There often exist many different options for each command.

Add a Workflow
==============

#. There are many ways to add Workflows to the database. You can do it directly from the command line as::

    lpad add_scripts 'echo "hello"','echo "goodbye"' -n hello,goodbye -w test_workflow

   *Output*::

    2013-10-03 13:51:19,991 INFO Added a workflow. id_map: {0: 1, 1: 2}

   This added a two-job linear workflow. The first jobs prints *hello* to the command line, and the second job prints *goodbye*. We gave names (optional) to each step as "hello" and "goodbye". We named the workflow overall (optional) as "test_workflow".

#. Let's look at our test workflow::

    lpad get_wfs -n test_workflow -d more

   *Output*::

    {
        "created_on": "2013-10-03T20:54:28.296672",
        "states": {
            "hello--1": "READY",
            "goodbye--2": "WAITING"
        },
        "state": "READY",
        "launch_dirs": {
            "hello--1": [],
            "goodbye--2": []
        },
        "name--id": "test_workflow--1",
        "updated_on": "2013-10-03T20:54:28.296676"
    }

   We get back basic information on our workflows. The second step "goodbye" is *waiting* for the first one to complete; it is not ready to run because it depends on the first job.

Run all Workflows
=================

#. You can run jobs one at a time (*"singleshot"*) or all at once (*"rapidfire"*). Let's run all jobs::

    rlaunch --silencer rapidfire

   *Output*::

    hello
    goodbye

   Clearly, both steps of our workflow ran in the correct order.

#. Let's again look at our workflows::

    lpad get_wfs -n test_workflow -d more

   *Output*::

    {
        "created_on": "2013-10-03T20:57:24.978665",
        "states": {
            "hello--1": "COMPLETED",
            "goodbye--2": "COMPLETED"
        },
        "state": "COMPLETED",
        "launch_dirs": {
            "hello--1": [
                "/some/path/launcher_2013-10-03-20-56-29-345603"
            ],
            "goodbye--2": [
                "/some/path/launcher_2013-10-03-20-56-29-861385"
            ]
        },
        "name--id": "test_workflow--1",
        "updated_on": "2013-10-03T20:57:24.978670"
    }

   FireWorks automatically created ``launcher_`` directories for each step in the Workflow and ran them. We see that both steps are complete. Note that there exist options to :doc:`choose where to run jobs </controlworker>`, as well as to :doc:`tear down empty directories after running jobs </config_tutorial>`.

Launch the web GUI
==================

#. If you have a web browser and installed Django (``pip install django``), you can launch the web browser to see your results::

    lpad webgui

Python code
===========

The following Python code achieves the same behavior::

    from fireworks.core.firework import FireWork, Workflow
    from fireworks.core.launchpad import LaunchPad
    from fireworks.core.rocket_launcher import rapidfire
    from fireworks.user_objects.firetasks.script_task import ScriptTask

    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    launchpad.reset('', require_password=False)

    # create the individual FireWorks and Workflow
    fw1 = FireWork(ScriptTask.from_str('echo "hello"'), name="hello", fw_id=1)
    fw2 = FireWork(ScriptTask.from_str('echo "goodbye"'), name="goodbye", fw_id=2)
    wf = Workflow([fw1, fw2], {1:2}, name="test workflow")

    # store workflow and launch it locally
    launchpad.add_wf(wf)
    rapidfire(launchpad)

.. note:: The ``{1:2}`` argument is adding a dependency of fw2 to fw1. Meaning, fw2 will only run after fw1 completes.

Next steps
==========

Now that you've successfully gotten things running, we encourage you to learn about all the different options FireWorks provides for designing, managing, running, and monitoring workflows. A good next step is the :doc:`Introductory tutorial <introduction>`, which takes things more slowly than this quickstart.