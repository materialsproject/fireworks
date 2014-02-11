============
Contributors
============

FireWorks was developed primarily by Anubhav Jain at Lawrence Berkeley National Lab, using research funding from Kristin Persson for the `Materials Project <http://www.materialsproject.org>`_.

Michael Kocher and Dan Gunter initiated the architecture of a central MongoDB database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code was refashioned for the QueueLauncher and the PBS QueueAdapter.

Shyue Ping Ong contributed to several aspects of FireWorks, and was additionally extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, continuous integration, etc. Shyue's custodian_ library was adapted (with permission) to create the DictMod language option for updating child FireWorks. Incidentally, the custodian library is a nice complement to FireWorks for use in FireTasks that is employed by the Materials Project.

Xiaohui Qu wrote the multi job launcher, with help from Anubhav Jain and advice from Dan Gunter.

David Waroquiers wrote the SLURM queue adapter, helped write the FileTransferTask, and provided useful feedback.

Morgan Hargrove wrote the "base site" web frontend as part of a summer project at LBL.

William Davidson Richards Waroquiers wrote the SGE queue adapter and provided useful feedback.

Wei Chen was the first test pilot of FireWorks, and contributed greatly to improving the docs and ensuring that FireWorks installation went smoothly for others. In addition, he made many suggestions to improve the usability of the code.

Thanks to Marat Valiev for suggesting Jinja2 as a lightweight templating alternative to Django, and Stephen Bailey for helpful discussions.

.. _pymatgen: http://packages.python.org/pymatgen/
.. _custodian: https://pypi.python.org/pypi/custodian