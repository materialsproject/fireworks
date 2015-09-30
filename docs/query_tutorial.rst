=====================================================
Querying FireWorks and Workflows / Generating Reports
=====================================================

FireWorks provides two functions for getting information about your Workflows. The ``lpad get_fws`` command queries individual FireWorks (steps in a Workflow), whereas the ``lpad get_wflows`` command queries entire Workflows. The reporting features allows you to generate detailed reports about runtime statistics.

Full usage of these commands can be found through the built-in help::

    lpad get_fws --help
    lpad get_wflows --help
    lpad report --help

Example queries - FireWorks
===========================

#. Count the number of completed FireWorks::

    lpad get_fws -s COMPLETED -d count

#. Show all information for the 3 most recently updated FIZZLED FireWorks::

    lpad get_fws -s FIZZLED -d all -m 3 --rsort updated_on

#. Show all information of the Firework with *name* set to ``my_fw``::

    lpad get_fws -n my_fw -d all

#. Show a summary of the Firework with *fw_id* of 1::

    lpad get_fws -i 1 -d more

#. Show a summary of all FireWorks where the **spec** contains a value of *my_parameter* equal to 3::

    lpad get_fws -q '{"spec.my_parameter":3}' -d more

Example queries - Workflows
===========================

#. Count the number of completed Workflows::

    lpad get_wflows -s COMPLETED -d count

#. Show all information for the 3 most recently updated FIZZLED Workflows::

    lpad get_wflows -s FIZZLED -d all -m 3 --rsort updated_on

#. Show all information of the Workflow with *name* set to ``my_wf``::

    lpad get_wflows -n my_wf -d all

#. Show a summary of the Workflow containing a Firework with *fw_id* of 1::

    lpad get_wflows -i 1 -d more

#. Show a summary of all Workflows where the **metadata** contains a value of *my_parameter* equal to 3::

    lpad get_wflows -q '{"metadata.my_parameter":3}' -d more

Example queries - Reporting
===========================

#. Get a report of what happened to recently updated Fireworks::

    lpad report

#. Get report about workflows or jobs::

    lpad report -c wflows
    lpad report -c launches

#. Customize the reporting interval, e.g. see what happened the last 6 months::

    lpad report -i months -n 6