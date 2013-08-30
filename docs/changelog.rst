===================
FireWorks Changelog
===================

v0.24
-----

* TransferTask added
* fix ``_use_global_spec``

v0.23
-----

* delete useless dirs when setting ``_launch_dir``
* ScriptTask and TemplateWriterTask have ``_use_global_spec`` option

v0.22
-----

* allow user to control where a FW gets executed using ``_launch_dir``

v0.21
-----

* add TemplateWriterTask plus documentation
* check for duplicate serialized objects

v0.2
----

* initial (alpha) release of Web GUI from Morgan Hargrove

v0.196
------

* bugfix to detect_unreserved script
* fixes to pip installation and instructions

v0.18
-----

* add fizzle_bad_rc option to ScriptTask
* major doc additions and updates

v0.17
-----

* minor update to ping()
* major docs reorganization and updates
* document and better support 'pip' installation

v0.16
-----

* refactor AVOID_MANY_STATS into more tunable QSTAT_FREQUENCY
* speed up counting operations
* add more indices
* better log queue submission errors
* auto_load() function for LaunchPad
* queue launcher fills in previous block if not full (modifiable in FWConfig)
* many doc updates

v0.15
-----

* add ability to *ARCHIVE* FireWorks
* update docs regarding enhancements to querying FireWorks and Workflows
* option to avoid overloading the queue management system with status requests
* more robust PBS adapter implementation

v0.14
-----

* pin down and fix known issue of launches sometimes not being updated
* further refine display options and enhancements for ``get_fws`` and ``get_wfs``.
* minor enhancements to queue launcher and PBS adapter
* support user indices for workflows
* minor bugfixes and internal code cleanup

v0.13
-----

* multiple query and output display options and enhancements added for ``get_fws`` and ``get_wfs``.
* use FW's name to set more informative PBS job names
* make sure ping_launch only writes on running jobs (prevent race condition)
* minor bugfixes

v0.12
-----

.. caution:: The ``get_fw_id`` and ``get_fw`` LaunchPad commands were merged into ``get_fws``.

* better support for getting states of FireWorks and Workflows
* minor bugfix for dynamic FireWorks

v0.11
-----

* rerunning FireWorks
* misc fixes for categories

v0.1
----

* initial Release