======================
Writing Queue Adapters
======================

FireWorks is intended to support multiple queueing systems. To support a new queueing system, a few functions need to be defined for that queue manager (e.g., what command is used to submit jobs?). In most cases, new queue managers can be supported with minimal effort.

Modifying the template of the CommonAdapter
===========================================

The FireWorks CommonAdapter supports several queueing engines such as PBS, SGE, SLURM, and IBM LoadLeveler. If you want to use one of these queueing systems but make minor modifications to how the queue submission file looks, you only need to write a new template file and point your queue adapter to it.

1. Create a template file for job submission. Variables that you want to specify later should be written using the ``$${var}`` notation.  Save this template file somewhere, e.g. as ``PBS_template_custom.txt``. An example template file is given below::

    #!/bin/bash

    #PBS -l nodes=$${nnodes}:ppn=$${ppnode}
    #PBS -l walltime=$${walltime}
    #PBS -q $${queue}
    #PBS -A $${account}
    #PBS -G $${group_name}
    #PBS -N $${job_name}
    #PBS -o FW_job.out
    #PBS -e FW_job.error

    $${pre_rocket}
    cd $${launch_dir}
    $${rocket_launch}
    $${post_rocket}

    # CommonAdapter (PBS) completed writing Template

   .. note:: Be sure to keep the lines involving ``cd $${launch_dir}`` and ``$${rocket_launch}`` intact. Your template file does not need to have any other variables, although the ``$${queue}`` variable helps FireWorks count how many jobs you have in a given queue. Also, not all variable names will need to specified in order to write a queue script, so feel free to add lines containing optional variables at this stage.

2. Find your Queue Adapter file from the :doc:`queue tutorial </queue_tutorial>` - it should be named ``my_qadapter.yaml``. Modify it so that there is an additional parameter called ``_fw_template_file`` that points to your new template file. In addition, add lines to set the values of variables from your template (if you leave a variable in the template undefined, the line containing it will be skipped). For example, your custom ``my_qadapter.yaml`` file might look like this::

    _fw_name: CommonAdapter
    _fw_q_type: PBS
    _fw_template_file: /path/to/PBS_template_custom.txt
    rocket_launch: rlaunch -w path/to/my_fworker.yaml -l path/to/my_launchpad.yaml singleshot
    nnodes: 1
    ppnode: 1
    walltime: '00:02:00'
    queue: debug
    account: null
    job_name: null
    logdir: path/to/logging
    pre_rocket: null
    post_rocket: null

3. Use this new ``my_qadapter.yaml`` file (with the ``_fw_template_file`` key specified) when using the queue launcher. The queue launcher will write scripts according to your custom template, with variables substituted according to your ``my_qadapter.yaml`` file.


Writing a new queue adapter
===========================

If you need to support a new queueing system, you will change the Python code by either (i) modifying the CommonAdapter or (ii) writing a new qadapter from scratch. In either case, we suggest you contact us for help (see :ref:`contributing-label`) so that the process is as smooth and painless as possible.

Modifying the CommonAdapter
----------------------------

The CommonAdapter, which supports several queueing systems, is located in ``<INSTALL_DIR>/fireworks/user_objects/queue_adapters/common_adapter.py`` (you can find out ``<INSTALL_DIR`` by typing ``lpad version``). Review the code and make changes as necessary for your queue type to ``commonadapter.py``.

Note that you can make basic changes to the submit commands (e.g., ``qstat`` or ``squeue``) by overriding the ``q_commands_override`` in your qadapter YAML file::

    _q_commands_override:
        submit_cmd: my_qsubmit
        status_cmd: my_qstatus

If you decide that modifications to the CommonAdapter are necessary, make sure to:

* Add your queue type to ``supported_q_types``
* Ensure the ``submit_cmd`` parameter is set correctly
* Add a default template file for your queue in the same directory as ``common_adapter.py``, e.g. ``QUEUETYPE_template.txt``. Some examples are present in the FireWorks codebase.
* Review the remaining methods for consistency with your queue, e.g. ``get_njobs_in_queue`` and ``get_status_cmd``.

If all methods are implemented correctly, your new adapter should be functional and you can use it by modifying ``my_launchapd.yaml``:

* Set the ``_fw_name`` to *CommonAdapter*
* Set the `_fw_q_type`` to your new queue type

Writing a new adapter from scratch
----------------------------------

If your queue is a complex entity that is different than typical queue managers (maybe a web-based submission framework), you'll need to write a new class from scratch that extends ``QueueAdapterBase`` and:

* implement the ``submit_to_queue()`` method
* implement the ``get_njobs_in_queue()`` method
* set the ``_fw_name`` parameter to some unique String.
* set the ``template_file`` variable to a template file for your queue scripts
* implement the ``get_script_str()`` method (only in rare instances where your queue submission doesn't involve writing a templated script, otherwise do not implement this method)

You might look at the *CommonAdapter* class or *PBSAdapterNEWT* for examples. After writing your new code, decide on a location for your queue adapter Python code and template file. The built-in queue adapters are located in ``<INSTALL_DIR>/fireworks/user_objects/queue_adapters``, and FireWorks will discover your code there automatically (you can find out ``<INSTALL_DIR>`` by typing ``lpad version``). However, you can also place your queue adapter in a different Python package if you set the ``ADD_USER_PACKAGES`` option as in the :doc:`FW config </config_tutorial>`.

Again, we suggest that you contact us for help (see :ref:`contributing-label`) if you run into any problems during the process.

