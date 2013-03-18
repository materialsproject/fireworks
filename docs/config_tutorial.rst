==========================================================
Modifying the FW Config (and linking to external packages)
==========================================================

Many parameters used by FireWorks can be changed to suit your needs. For example, by default FireWorks will print a ``FW.json`` file in your run directory, but you can turn this off or switch to YAML format. Or, you might write a :doc:`custom FireTask </firetask_tutorial>` in a Python package external to FireWorks and need FireWorks to discover it.

How to modify the FW Config
===========================

A sample FW_config file (that does not change any settings) is located in the FireWorks tutorial directory: ``<INSTALL_DIR>/fw_tutorials/fw_config/FW_config.yaml``.

1. To activate the config file, you must move it to your root ``<INSTALL_DIR>`` (do not change it's name!)

2. To test whether your config file is activated, run any LaunchPad command::

    lpad version

You should see text printed to the Terminal saying ``successfully loaded your custom FW_config.yaml!``. You can remove this text by deleting the ``ECHO_TEST`` parameter from your ``FW_config.yaml`` file.

Linking to FireTasks in external packages
=========================================

If you've placed Python code for some of your own custom FireTasks in an external Python package named *my_package.firetasks*, you can notify FireWorks of the FireTasks in this directory by adding the packages to your config::

    ADD_USER_PACKAGES:
      - my_package.firetasks

.. note:: Make sure your package is in your PYTHONPATH! For example, typing ``from my_package import firetasks`` in an interactive Python terminal should succeed.

Parameters you might want to change
===================================

A few basic parameters that can be tweaked are:

* ``PRINT_FW_JSON: True`` - whether to print the ``FW.json`` file in your run directory
* ``PRINT_FW_YAML: False`` - whether to print the ``FW.yaml`` file in your run directory
* ``SUBMIT_SCRIPT_NAME: FW_submit.script`` - the name to give the script for submitting PBS/SLURM/queue jobs
* ``FW_LOGGING_FORMAT: %(asctime)s %(levelname)s %(message)s`` - format for loggers (this String will be passed to ``logging.Formatter()``)


Parameters that you probably shouldn't change
=============================================

Some parameters that you can change, but probably shouldn't, are:

* ``QUEUE_RETRY_ATTEMPTS`` - number of attempts to re-try communicating with queue server when communication fails
* ``QUEUE_UPDATE_INTERVAL: 15`` - max interval (seconds) needed for queue to update after submitting a job
* ``PING_TIME_SECS: 3600`` - means that the Rocket will ping the LaunchPad that it's alive every 3600 seconds. See the :doc:`failures tutorial <failures_tutorial>`.
* ``RUN_EXPIRATION_SECS: 14400`` - means that the LaunchPad will mark a Rocket FIZZLED if it hasn't received a ping in 14400 seconds. See the :doc:`failures tutorial <failures_tutorial>`.
* ``RESERVATION_EXPIRATION_SECS: 1209600`` - means that the LaunchPad will unreserve a FireWork that's been in the queue for 1209600 seconds (14 days). See the ``queue reservation tutorial <queue_tutorial_pt2>`.
* ``FW_BLOCK_FORMAT: %Y-%m-%d-%H-%M-%S-%f`` - the ``launcher_`` and ``block_`` directories written by the Rocket and Queue Launchers add a date stamp to the directory. You can change this if desired.

For a full list of parameters that can be changed, you can browse the ``fw_config.py`` file in the FireWorks source. In general, however, we suggest that you leA few basic settings::

