===================
FireWorks Changelog
===================

**v0.72**

* Include default base site files in pip install
* Optimizations for when WFs contains 1000s of root node FWs
* zopen tracker files

**v0.71**

* Include default templates in pip install
* Change default formatting in get_wfs (S.P. Ong)

v0.7
----

.. caution:: The default behavior is now that mod_spec and update_spec push updates to next FireWork AND the next FireTask
.. caution:: The FWConfig parameters are no longer called via a FWConfig() class instantiation; you can import these parameters directly now.

* Python 3 support! via 'six' library (S.P. Ong)
* BackgroundTasks introduced
* Performance improvements to get_wf command (S.P. Ong)
* Deserialization warnings and added stability (S.P. Ong)
* Reservation mode and silencer works in remote launch (S.P. Ong)
* Restore old FileTransferTask behavior
* Tutorial updates
* Various internal improvements, e.g. to FWConfig (S.P. Ong)
* Bug fixes (A. Jain, S.P. Ong)

**v0.66**

.. warning:: This version changes the default serialization for custom FireWorks without _fw_name to <project>::<Class> instead of <Class>. If you have custom FireTasks from v0.62-v0.65 that did not specify _fw_name explicitly, this introduces a backward incompatibility. Contact the support list if this affects you - an easy fix is available.

* Fix major bug in dynamic workflows with multiple additions/detours
* Fixed lpad reset that became broken in recent release
* Change default _fw_name for FireTasks to <project>::<Class>, e.g. fireworks::MyTask

**v0.65**

* Fix bug in qlaunch singleshot introduced in previous release (S.P. Ong)
* Add qlaunch cleanup (S.P. Ong)
* Setup different default config dirs (S.P. Ong)

**v0.64**

.. warning:: This version introduced a major bug in ``qlaunch singleshot`` via the command line (fixed in v0.65)
.. warning:: This version introduced a bug in ``lpad reset`` via the command line (fixed in v0.66)

.. caution:: The ``add_dir`` command is incorporated into the ``add`` command. e.g. ``lpad add my_dir/*.yaml``. Many command line options that allowed comma-separated lists are now space-separated lists to better employ argparse (see updated docs).

* clean up argument parsing (S.P. Ong)
* remote qlaunch handles multiple configs (S.P. Ong)


**v0.63**

* fix bug in rtransfer mode of FileTransferTask (S.P. Ong)
* improvements to remote qlaunch (S.P. Ong)

**v0.62**

.. caution:: The TransferTask is renamed to FileTransferTask (however, existing FireWorks databases should be backwards-compatibile). The names of the default FireTasks no longer have spaces; however, existing FireWorks databases and code should be backwards-compatible.

* Add FIFO and FILO sort options for equal priority FireWorks
* Remove database locks in multiprocessing mode
* Allow multiple scripts in ScriptTask (S.P. Ong)
* Add additional File I/O FireTasks (S.P. Ong)
* Changes to FireTask base implementation (S.P. Ong)
* Allow config file in $HOME/.fireworks (S.P. Ong)
* Add remote options to qlaunch via fabric library (S.P. Ong)
* _fw_name automatically set to class name if unspecified (S.P. Ong)
* Remove ValueError upon not finding a FireWork to run and handle this situation better

**v0.61**

* Include text files needed for queue adapters in distribution (D. Gunter)

v0.6
----

.. caution:: The QueueAdapter code has been refactored in a way that is not fully backward compatible. Chances are, you will have to modify any ``my_qadapter.yaml`` files you have so that the ``_fw_name`` is set to *CommonAdapter* and a new ``_fw_q_type`` parameter is set to *PBS*, *SGE*, or *SLURM*.

* Major refactor of QueueAdapters so it is easy to change template files without adding new code (S.P. Ong)
* restore lpad.maintain()
* minor doc updates

**v0.54**

* Add ``--exclude`` and ``--include`` options to Trackers + minor formatting changes
* use config file in current dir if possible

**v0.53**

* Display name in trackers
* Fix some bugs relating to multiprocessing & offline mode (Xiaohui Qu)
* Don't require password when tracking many FWs
* Default 25 lines in trackers

**v0.52**

* add *trackers*, or the ability to monitor output files

**v0.51**

* make set_priority work as intended through command line
* invert the -b option on webgui (new -s option skips opening browser)

v0.5
----

.. caution:: The command/function ``detect_fizzled`` has changed to ``detect_lostruns``, changed old arguments and added additional ones
.. caution:: The command/function ``detect_unreserved`` has changed - refactored "mark" to "fizzle"

* add option to "rerun" when detecting lost runs
* add option to only detect short-lived lost jobs (useful for job packing type failures)
* refactored argument names and method names for clarity

**v0.46**

* add NEWT queue adapter

**v0.45**

* allow user to confirm database reset and multi-FW changes via an input prompt rather than password parameter

**v0.44**

* make it easier to define new queueadapters, and add documentation

**v0.43**

* fix bug introduced in v0.4 that caused rlaunch rapidfire to stop working

**v0.42**

* fix bug introduced in v0.4 that caused update_time to be NULL for launches

**v0.41**

* add ``set_priority`` function to LaunchPad
* minor bug fixes related to multi-launcher and default queue params

v0.4
----

* add offline mode

**v0.37**

.. caution:: The default behavior in ScriptTask is now ``fizzle_bad_rc``.

* add ``lpad add_scripts``
* ``fizzle_bad_rc`` by default in ScriptTask
* add FWorker() by default in rlaunch


**v0.36**

.. caution:: The ``rerun_fw``, ``defuse_fw``, and ``reignite_fw`` commands are now pluralized, ``refresh_wf`` is simply ``refresh``, and ``rerun_fizzled`` has been incorporated into ``rerun_fws``.

* much more powerful control for ``rerun_fws``, ``defuse``, ``archive``, ``reignite``, ``defuse_fws``, ``reignite_fws``, ``refresh``.

**v0.35**

* restore behavior back to v0.33

**v0.34**

* *deprecated* - rename FIZZLED to FAILED

**v0.33**

* concatenate the update_spec and mod_spec of all FireTasks, instead of exiting as soon as a FireTask updates a spec.

**v0.32**

* change templating language to Jinja2 (and remove heavyweight dependency to Django)
* add ability to manually refresh workflows

**v0.31**

* fix bug related to interaction between multi job packer and job checkout optimization


v0.3
----

* multi job launcher to 'pack' jobs (Xiaohui Qu)

**v0.25**

* make paramiko optional as it can cause install problems

**v0.24**

* TransferTask added
* fix ``_use_global_spec``

**v0.23**

* delete useless dirs when setting ``_launch_dir``
* ScriptTask and TemplateWriterTask have ``_use_global_spec`` option

**v0.22**

* allow user to control where a FW gets executed using ``_launch_dir``

**v0.21**

* add TemplateWriterTask plus documentation
* check for duplicate serialized objects

v0.2
----

* initial (alpha) release of Web GUI from Morgan Hargrove

**v0.196**

* bugfix to detect_unreserved script
* fixes to pip installation and instructions

**v0.18**

* add fizzle_bad_rc option to ScriptTask
* major doc additions and updates

**v0.17**

* minor update to ping()
* major docs reorganization and updates
* document and better support 'pip' installation

**v0.16**

* refactor AVOID_MANY_STATS into more tunable QSTAT_FREQUENCY
* speed up counting operations
* add more indices
* better log queue submission errors
* auto_load() function for LaunchPad
* queue launcher fills in previous block if not full (modifiable in FWConfig)
* many doc updates

**v0.15**

* add ability to *ARCHIVE* FireWorks
* update docs regarding enhancements to querying FireWorks and Workflows
* option to avoid overloading the queue management system with status requests
* more robust PBS adapter implementation

**v0.14**

* pin down and fix known issue of launches sometimes not being updated
* further refine display options and enhancements for ``get_fws`` and ``get_wfs``.
* minor enhancements to queue launcher and PBS adapter
* support user indices for workflows
* minor bugfixes and internal code cleanup

**v0.13**

* multiple query and output display options and enhancements added for ``get_fws`` and ``get_wfs``.
* use FW's name to set more informative PBS job names
* make sure ping_launch only writes on running jobs (prevent race condition)
* minor bugfixes

**v0.12**

.. caution:: The ``get_fw_id`` and ``get_fw`` LaunchPad commands were merged into ``get_fws``.

* better support for getting states of FireWorks and Workflows
* minor bugfix for dynamic FireWorks

**v0.11**

* rerunning FireWorks
* misc fixes for categories

v0.1
----

* initial Release