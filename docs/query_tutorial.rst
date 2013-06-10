================================
Querying FireWorks and Workflows
================================

FireWorks provides two functions for getting information about your Workflows. The ``lpad get_fws`` command queries individual FireWorks (steps in a Workflow), whereas the ``lpad get_wfs`` command queries entire Workflows.

Full usage of these commands can be found through the built-in help::

    lpad get_fws --help
    lpad get_wfs --help

Example queries - FireWorks
===========================

#. Count the number of completed FireWorks::

    lpad get_fws -s COMPLETED -d count

#. Show all information for the 3 most recently updated FIZZLED FireWorks::

    lpad get_fws -s FIZZLED -d all -m 3 --rsort updated_on

#. Show all information of the FireWork with *name* set to ``my_fw``::

    lpad get_fws -n my_fw -d all

#. Show a summary of the FireWork with *fw_id* of 1::

    lpad get_fws -i 1 -d more

#. Show a summary of all FireWorks where the **spec** contains a value of *my_parameter* equal to 3::

    lpad get_fws -q '{"spec.my_parameter":3}' -d more

Example queries - Workflows
===========================

#. Count the number of completed Workflows::

    lpad get_wfs -s COMPLETED -d count

#. Show all information for the 3 most recently updated FIZZLED Workflows::

    lpad get_wfs -s FIZZLED -d all -m 3 --rsort updated_on

#. Show all information of the Workflow with *name* set to ``my_wf``::

    lpad get_wfs -n my_wf -d all

#. Show a summary of the Workflow containing a FireWork with *fw_id* of 1::

    lpad get_wfs -i 1 -d more

#. Show a summary of all Workflows where the **metadata** contains a value of *my_parameter* equal to 3::

    lpad get_wfs -q '{"metadata.my_parameter":3}' -d more
