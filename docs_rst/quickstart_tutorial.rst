=============================================
Two-minute installation, setup and quickstart
=============================================

Install and setup
=================

Supposed you have a :doc:`virtual environment </virtualenv_tutorial>` with the `pip`` package installed. Then simply type::

    pip install fireworks[mongomock]
    mkdir -p ~/.fireworks
    echo MONGOMOCK_SERVERSTORE_FILE: $HOME/.fireworks/mongomock.json > ~/.fireworks/FW_config.yaml
    echo '{}' > ~/.fireworks/mongomock.json
    lpad reset --password="$(date +%Y-%m-%d)"

See that the database contains no workflows::

    lpad get_wflows

*Output*::

    []

Add and display a workflow
==========================

Add a script that prints the date as a single firework in a workflow::

    lpad add_scripts 'date' -n date_printer_firework -w date_printer_workflow

Let us display the workflow just added::

    lpad get_wflows -d more

*Output*::

    {
        "state": "READY",
        "name": "date_printer_workflow--1",
        "created_on": "2024-06-07T15:05:02.096000",
        "updated_on": "2024-06-07T15:05:02.096000",
        "states": {
            "date_printer_firework--1": "READY"
        },
        "launch_dirs": {
            "date_printer_firework--1": []
        }
    }

We have only one workflow with only one firework on the database.

Run a workflow
==============

Now we can run the firework in our workflow locally with this simple command::

    rlaunch singleshot

*Output*::
    2024-06-07 17:15:08,515 INFO Hostname/IP lookup (this will take a few seconds)
    2024-06-07 17:15:08,517 INFO Launching Rocket
    2024-06-07 17:15:08,608 INFO RUNNING fw_id: 1 in directory: /home/ubuntu
    2024-06-07 17:15:08,610 INFO Task started: ScriptTask.
    Fri Jun  7 17:15:08 CEST 2024
    2024-06-07 17:15:08,612 INFO Task completed: ScriptTask
    2024-06-07 17:15:08,616 INFO Rocket finished

Further steps
=============

This setup uses a JSON file on the local computer as a database instead of MongoDB. You can carry out many of the following tutorials
and do local testing by using this setting.

If you want to complete the more advanced tutorials, such as the :doc:`queue tutorial </queue_tutorial>`, or use FireWorks productively on 
a computing cluster, then you should consider :doc:`installing and setting up FireWorks </installation>` with a MongoDB server.
