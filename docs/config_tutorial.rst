=======================
Modifying the FW Config
=======================

Many parameters used by FireWorks can be changed to suit your needs. Some examples include:

* specifying the default locations of your configuration files. This will save you **a lot** of typing when running FireWorks scripts, e.g. ``lpad -l my_launchpad.yaml get_fws`` becomes ``lpad get_fws`` once you've set your default LaunchPad location.
* enabling FireTasks for which the code is located outside of the FireWorks package
* smaller adjustments, e.g. whether to print a ``FW.json`` file in your run directory
* performance tweaks (not recommended!)

How to modify the FW Config
===========================

A sample FW_config file (that does not change any settings) is located in the FireWorks tutorial directory: ``<INSTALL_DIR>/fw_tutorials/fw_config/FW_config.yaml``.

1. To activate the config file, you can do any one of the following:
    i. put it in the current directory where you run FireWorks commands
    ii. put it in your root ``<INSTALL_DIR>`` (do not change it's name!). Recall that your ``<INSTALL_DIR>`` can be found by typing ``lpad version``.
    iii. put the config file in ``<HOME>/.fireworks`` where ``<HOME>`` is your home directory (don't forget the ``.`` in the ``.fireworks`` directory!)
    iv. put the config file anywhere, but set the `FW_CONFIG_FILE` as an environment variable in your OS. The ``FW_CONFIG_FILE`` environment variable should be set to the **full** path (no relative links!) of your config file, including the filename.

    .. note:: The config file in the current directory will always take precedence.

2. To test whether your config file is activated, run any LaunchPad command::

    lpad version

You should see text printed to the Terminal saying ``successfully loaded your custom FW_config.yaml!``. You can remove this text by deleting the ``ECHO_TEST`` parameter from your ``FW_config.yaml`` file.


.. _configfile-label:

Specifying default locations for the config files
-------------------------------------------------

It can be annoying to manually type in the ``-l``, ``-w``, and ``-q`` parameters in FireWorks scripts (corresponding to the locations of the LaunchPad, FireWorker, and QueueAdapter files, respectively). You can set these parameters once and for all by specifying the following variables in your FWConfig::

    LAUNCHPAD_LOC: fullpath/to/my_launchpad.yaml
    FWORKER_LOC: fullpath/to/my_fworker.yaml
    QUEUEADAPTER_LOC: fullpath/to/my_qadapter.yaml

.. note:: be sure to use full paths, not relative paths or BASH shortcuts!

Specifying default locations for the config files (alternate)
-------------------------------------------------------------

An alternate strategy is to set a single parameter in FWConfig called ``CONFIG_FILE_DIR``. This should be the full path to a directory containing files named ``my_launchpad.yaml``, ``my_fworker.yaml``, and ``my_qadapter.yaml``. FireWorks looks for these files in the ``CONFIG_FILE_DIR`` if it cannot find them elsewhere. If unset in the FWConfig, the ``CONFIG_FILE_DIR`` is automatically set to the directory you are running your FW script in.

Linking to FireTasks in external packages
-----------------------------------------

If you've placed Python code for some of your own custom FireTasks in an external Python package named *my_package.firetasks*, you can notify FireWorks of the FireTasks in this directory by adding the packages to your config::

    ADD_USER_PACKAGES:
      - my_package.firetasks

.. note:: Make sure your package is in your PYTHONPATH! For example, typing ``from my_package import firetasks`` in an interactive Python terminal should succeed.

An alternative is to give your FireTasks a _fw_name such as ``{{package.subpackage.module.Class}}``. When enclosed in double braces, FireWorks will not search USER_PACKAGES and instead directly load the class. The disadvantage of this method is that you *must* update the *FW_NAME_UPDATES* key of the FWConfig if you refactor or move the class.

Parameters you might want to change
-----------------------------------

A few basic parameters that can be tweaked are:

* ``SORT_FWS: ''`` - set to ``FIFO`` if you want older FireWorks to be run first, ``FILO`` if you want recent FireWorks run first. Note that higher priority FireWorks are always run first.
* ``PRINT_FW_JSON: True`` - whether to print the ``FW.json`` file in your run directory
* ``PRINT_FW_YAML: False`` - whether to print the ``FW.yaml`` file in your run directory
* ``SUBMIT_SCRIPT_NAME: FW_submit.script`` - the name to give the script for submitting PBS/SLURM/etc. queue jobs
* ``FW_LOGGING_FORMAT: %(asctime)s %(levelname)s %(message)s`` - format for loggers (this String will be passed to ``logging.Formatter()``)
* ``ALWAYS_CREATE_NEW_BLOCK: False`` - set True if you want the Queue Launcher to always create a new block directory every time it is called, False if you want to re-use previous blocks
* ``TEMPLATE_DIR`` - where to store templates if you are using the :doc:`TemplateWriterTask <templatewritertask>`.
* ``REMOVE_USELESS_DIRS: False`` - tries to delete empty launch directories created when setting the ``_launch_dir`` in the spec of your Firework.
* ``EXCEPT_DETAILS_ON_RERUN: False`` - if True, when rerunning a FIZZLED Firework, the serialized exception details are added to the spec.
* ``WEBSERVER_HOST: 127.0.0.1`` - the default host on which to run the web server
* ``WEBSERVER_PORT: 5000`` - the default port on which to run the web server
* ``QUEUE_JOBNAME_MAXLEN: 20`` - the max length of the job name to send to the queuing system (some queuing systems limit the size of job names)

Parameters that you probably shouldn't change
---------------------------------------------

Some parameters that you can change, but probably shouldn't, are:

* ``QUEUE_RETRY_ATTEMPTS: 10`` - number of attempts to re-try communicating with queue server when communication fails
* ``QUEUE_UPDATE_INTERVAL: 5`` - max interval (seconds) needed for queue to update after submitting a job
* ``WFLOCK_EXPIRATION_SECS: 300`` -  wait this long (in seconds) for a WFLock before expiring. Must set *much* higher than DB update time for a WF.
* ``WFLOCK_EXPIRATION_KILL False`` - If True, kill WFLock on expiration. If False, raise Error instead.
* ``PING_TIME_SECS: 3600`` - means that the Rocket will ping the LaunchPad that it's alive every 3600 seconds. See the :doc:`failures tutorial <failures_tutorial>`.
* ``RUN_EXPIRATION_SECS: 14400`` - means that the LaunchPad will mark a Rocket FIZZLED if it hasn't received a ping in 14400 seconds. See the :doc:`failures tutorial <failures_tutorial>`.
* ``RESERVATION_EXPIRATION_SECS: 1209600`` - means that the LaunchPad will cancel the reservation of a Firework that's been in the queue for 1209600 seconds (14 days). See the :doc:`queue reservation tutorial <queue_tutorial_pt2>`.
* ``FW_BLOCK_FORMAT: %Y-%m-%d-%H-%M-%S-%f`` - the ``launcher_`` and ``block_`` directories written by the Rocket and Queue Launchers add a date stamp to the directory. You can change this if desired.
* ``QSTAT_FREQUENCY: 50`` - number of jobs submitted to queue before re-executing a qstat. 1 means always do qstat, higher avoids unnecessarily loading the qstat server. Set this low if you have multiple processes submitting jobs to the same queue.
* ``PW_CHECK_NUM: 10`` - how many FireWorks/Worflows can be changed with a single LaunchPad command (like ``rerun_fws``) before a password is required.

For a full list of parameters that can be changed, you can browse the ``fw_config.py`` file in the FireWorks source.