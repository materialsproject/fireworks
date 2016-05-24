===================
FireWorks Changelog
===================

**v1.3.1**

* FileTransferTask has max_retry parameter (D. Dotson)
* Allow copying workflows but w/reset ids (D. Dotson)
* add ``max_loops`` option to rlaunch; this allows you to limit infinite mode to a few cycles

**v1.3.0**

* fix datetime import (fixes broken queue_launcher) - (D. Winston)
* fix datetime handler in __repr__
* always unreserve if queue submission goes wrong (G. Petretto)

**v1.2.9**

* add ``lpad admin unlock`` command to force unlock of workflows
* add ``--timeout`` option for rapidfire launches
* add ``user`` parameter for FileTransferTask (D. Dotson)
* fix bug in FileTransferTask (D. Dotson)

**v1.2.8**

* fix spelling of ``my_qadapter.yaml`` (thanks to specter119)

**v1.2.7**

* fix errant print statement

**v1.2.6**

* add FWorker auto_load
* add SSL cert support to LaunchPad (D. Cossey)
* improve offline recovery (G. Petretto)
* Add allow_gzipped option to Trackers

**v1.2.5**

* add defuse_workflow to FWAction (thanks to H. Rusche)
* New _add_fworker option in spec (D. Waroquiers)
* fix workflow state when allow_fizzled_parents option used (D. Waroquiers)
* doc updates and example workflows
* fix minor frontend coloring issues

**v1.2.4**

.. caution:: The deprecated ``FireWork`` class has been removed. Be sure to use ``Firework`` (see capitalization). Also, use ``Workflow.from_Firework()``.

* remove deprecated capitalization of FireWork
* better display of workflow info and reporting in frontend

**v1.2.3**

* Greatly improve refresh performance of large workflows (G. Petretto)
* FW Reporting now available on frontend
* Fix bug in Python 3 queue adapter (thanks to F. Zapata)
* Fix small bug in offline mode (G. Petretto)
* Fix bug in frontend pagination (G. Petretto)
* Improvements to wf.append (H. Rusche)

**v1.2.2**

* Flask and webgui are installed by default (no additional pip install needed)
* Fix small bug in squeue (thanks to M. Cahn for pointing it out)
* webgui improvements, including view for workflow metadata queries (D. Winston)
* remove display_wflows command and associated docs. It is unmaintained and the web GUI now plots WFs

**v1.2.1**

* attempt to fix further pip install issues in v1.2.0

**v1.2.0**

* attempt to fix pip install issues in v1.1.9

**v1.1.9**

* Workflow graph displayed visually in "lpad webgui" (C. Harris)
* Add ability to override queue commands (thanks to D. Waroquiers)
* detect_unreserved should only detect reserved fws (G. Petretto)

**v1.1.8**

* Some mods to adding a workflow to another workflow (thanks to H. Rusche & J. Montoya)
* LaunchPad handles LockedWorkflowException (P. Huck)
* prevent MSONable objects from being deserialized twice (thanks to J. Montoya)

**v1.1.7**

.. caution:: FWS now properly handles workflow states for ``allow_fizzled_parents``. Run ``lpad admin refresh -s FIZZLED`` to update your DB.

* fix WFLock causing inconsistent states in workflows; detect such cases in detect_lostruns; add --refresh as fix (G. Petretto)
* add ability to introspect launches
* fix for COMPLETED workflow state when `_allow_fizzled_parents` is True (D. Waroquiers, G. Petretto)
* allow FWS users to use as_dict() instead of to_dict() if they prefer (psuedo-compatibility with MSONable)
* add commas to counts in lpad GUI


**v1.1.6**

* add beta of ``lpad introspect`` (no docs yet)
* fix ``-q`` option of ``lpad report`` (D. Winston)

**v1.1.5**

.. caution:: FWS now decodes monty-style objects, e.g. pymatgen. If you encounter decoding issues, set DECODE_MONTY=False in your fw_config.

* completely reimplemented reporting (type ``lpad report`` for an example)
* both encode and decode for monty-style objects
* safer require_password=False option
* fix njobs for SLURM (P. Huck)
* fix bug in remove_useless_dirs (G. Petretto)
* fix bug in detect_lostruns (thanks to G. Petretto)
* add QUEUE_JOBNAME_MAXLEN config parameter, i.e. maximum char length for job names sent to queueing systems (D. Waroquiers)

**v1.1.4**

* added JS folder to pip install (should fix JSONview issues)
* optional max param for track_fws command
* performance updates
* doc updates

**v1.1.3**

* fix bug that caused FWorker queries to chain on themselves
* fix issue of Python runners that override sys.stdout, causing problems in ScriptTask
* fix unit tests

**v1.1.2**

* new special keyword _add_launchpad_and_fw_id allows accessing the LaunchPad in the FireTask
* new special keyword _pass_job_info makes it easy to pass run locations between jobs in a Workflow
* new special keyword _preserve_fworker makes it easy to run multiple jobs on the same FWorker
* default __repr__ for FWSerializable
* fix Hopper qstat bug
* Cobalt queue fixes (W. Scullin)
* SLURM template update (P. Huck)

**v1.1.1**

* greatly improve webgui: stability, clarity, functionality, and speed

**v1.1.0**

* fix bug in created_on for workflows (thanks to W. Zhao for pointing it out)
* fix bug in FWorker query for certain situations (P. Huck)
* Updates for Cobalt, Py3 (W. Scullin)
* Updates for IBM Loadsharing facility (Z. Ulissi)

**v1.08**
.. note:: v1.08 is not in pip due to version number issues, use Github to get this legacy version

* allow PyTask to return FWAction
* allow FWConfig to set web host and port for GUI
* make detect_lostruns more robust to failure halfway through
* minor fixes and typo corrections (jakirkham)

**v1.07**
.. note:: v1.07 is not in pip due to version number issues, use Github to get this legacy version

* fix bug in offline mode

**v1.06**
.. note:: v1.06 is not in pip due to version number issues, use Github to get this legacy version
.. caution:: Offline mode unusable in this release

* Pymongo3 compatibility
* fix double tab open on lpad webgui (G. Pettreto)
* show FW WAITING state
* unit test offline mode

**v1.05**
.. note:: v1.05 is not in pip due to version number issues, use Github to get this legacy version

.. caution:: The default behavior for PyTask handling of kwargs has changed. To maintain legacy behavior, update the "auto_kwargs" option to True in your FireTasks.
.. caution:: Offline mode unusable in this release

* Update PyTask kwargs handling (J. Kirkham)
* Fix writing of FW.json files with _launch_dir param (G. Petretto)
* update PBS template (K. Matthew)
* minor fixes (J. Kirkham)

**v1.04**

.. note:: v1.00-v1.03 are skipped due to problems in pip installation

* fix non-default host/port on Flask site
* remove base site (old frontend)
* address installation issues (MANIFEST.in, package_data)
* improve unit tests

**v0.99**

.. note:: v0.98 is skipped, as it has a faulty dependency.
.. note:: Users of the frontend will need to install Flask, ``pip install flask; pip install flask-paginate``. Django is no longer required for the frontend.

* Ability to add FireWorks to existing workflow (launchpad.add_wf_to_fwids)
* Better unit tests for task-level reruns (G. Petretto)
* Redesigned web site using Flask (M. Brafman)

**v0.97**

* Fix bug in adding multiple detours
* Task-level reruns (G. Petretto)
* Better Fworker default restrictions (G. Petretto)
* Make _launch_dir if doesn't exist (G. Petretto)
* Bug fixes (G. Petretto)

**v0.96**

* Address some installation issues (thanks to kpoman)
* fix minor issues and docs

**v0.95**

* Add decompressdir task (S.P. Ong)
* Fix bugs in offline launch (G. Petretto)
* Improve failure handling in case of FW system failure (G. Petretto)
* Allow embedding error message on FW rerun (G. Petretto)
* Minor testing improvements

**v0.94**

* Improve performance of get_wflows (S.P. Ong)
* Fix another bug due to performance improvements (B. Medasani)
* Fix bug in de-serialization of non dict-like FireTasks and other serialization issues

**v0.93**

* Fix bug in performance improvement cached state + unit tests (B. Medasani)
* minor bug fixes, installation changes
lpad
**v0.92**

.. caution:: This version has a minor bug affecting defusing of FWs and cached states for performance, fixed in v0.94

* Improve large workflow performance using a LazyFirework (B. Medasani, D. Gunter)
* some code cleanups and minor (rare) bugfix to datetime
* Add email option to PBS adapter (S.P. Ong)
* Support for pymatgen as_dict formulation (X. Qu)

**v0.91**

* Major: Rename FireWork to Firework. Should be fully backward-compatible for the moment, but users must switch by ~v1.0.
* Unicode compatibility for Py3k (S.P. Ong)

**v0.90**

* Introduce reporting tools via lpad report (W. Chen)
* Fix bug in locking
* Greatly speed up rlaunch rapidfire by removing artificial sleep
* Use monty CLoader (S.P. Ong)

**v0.89**

* Fix small FireTaskMeta issue (G. Petretto w/S.P. Ong)
* simplify some imports
* Add reservation display mode (S.P. Ong)
* add updated_on to FW which updates whenever FW changes state
* improve docs

**v0.88**

* Add many more unit tests (B. Medasani)
* Fix tracking when FireTask crashes (B. Medasani)
* Clean up some logging
* Don't rerun DEFUSED FWs - they must be reignited
* Allow defuse of COMPLETED FWs
* minor internal fixes

**v0.87**

* Fix major bug causing FIZZLED FWs to rerun spontaneously
* Make WFLock more nimble
* Forcibly remove WFLock after some time in case of catastrophe (tunable in FW_config)
* improve unit tests

**v0.86**

.. warning:: This version has a major bug that causes FIZZLED FWs to rerun, patched in v0.87

* add delete_wfs command (w/S.P. Ong)
* add update_fws command (S.P. Ong)
* add ignore_errors option in some default FireTasks (S.P. Ong)
* fix bug in Windows $HOME var (thanks to A. Berg)
* fig bug in reporting of lost FWs; rerun option should be OK in prev. versions
* change FIZZLED to have lower STATE_RANK than READY/RESERVED/RUNNING/etc

**v0.85**

* fix bug in running daemon mode locally with qlaunch rapidfire (B. Foster)
* better handling of duplicate path detection (S.P. Ong)
* add support for nodes keyword in SLURM adapter (S.P. Ong)

**v0.84**

* ability to define links when defining FireWorks rather than all at the Workflow level (based on conversation with H. Rusche)
* better handling of config files and better reporting on config file conflicts

**v0.83**

* misc multiprocessing improvements (X. Qu)
* better handling of dir creation conflicts (X. Qu)

**v0.82**

* add ability to define links via {fw1:fw2} objects rather than explicit IDs (based on conversation with H. Rusche)
* un-reserve a FW if queue submission goes badly and clean up queue launcher code
* internal cleanups (don't rerun ARCHIVED jobs, skip reruns of WAITING jobs)
* stop rapidfire upon error in queue launch
* rerun fw on unreserve
* add methods to work with queue ids (``cancel_qid``, ``--qid`` option in ``get_fws``, and ``get_qid``)

**v0.81**

.. note:: A major bugfix to dynamic and branching workflows was added in this release

* fix race condition bug in which two FW belonging to same WF simultaneously try to update the WF, and only one succeeds

**v0.80**

* rerun duplicated FWs on a rerun command (enabled by default), and return back all fw_ids that were rerun
* change default QUEUE_UPDATE_INTERVAL from 15 secs down to 5 secs
* add background tuneup option, and make it the default
* misc. cleanup (S.P. Ong)

**v0.79**

* Add support for IBM LoadLeveler Queue (F. Brockherde)

**v0.78**

* Fix spec copy bug as reported by Github user (F. Brockherde)
* Misc fixes (archiving FWs, tuple support)

**v0.77**

* Support/fix serialization of tuples as list instead of String (S.P. Ong)
* Introduce fw_env variables (S.P. Ong)

**v0.76**

* Better test for invalid WFs (S.P. Ong)
* Minor internal code cleanup (S.P. Ong)
* add internal profiling tools (D. Gunter)

**v0.75**

* Fix bug that randomly affected some dynamic workflows
* Add CompressDir and ArchiveDir tasks (S.P. Ong)
* Initial commit of PyTask (S.P. Ong)
* Initial networkx graphing of workflows via lpad (S.P. Ong)

**v0.72**

.. warning:: This version has a bug that can affect some dynamic workflows, patched in v0.75

* Include default base site files in pip install
* Optimizations for when WFs contains 1000s of root node FWs
* zopen tracker files

**v0.71**

* Include default templates in pip install
* Change default formatting in get_wfs (S.P. Ong)

v0.7
----

.. caution:: The default behavior is now that mod_spec and update_spec push updates to next Firework AND the next FireTask
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
* Remove ValueError upon not finding a Firework to run and handle this situation better

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