============
Contributors
============

FireWorks was developed primarily by Anubhav Jain at Lawrence Berkeley National Lab, using research funding from Kristin Persson for the `Materials Project <http://www.materialsproject.org>`_.

Shyue Ping Ong contributed to several aspects and features of FireWorks, and was additionally extremely helpful in providing guidance and feedback, as well as the nitty gritty of getting set up with Sphinx documentation, PyPI, continuous integration, etc. Shyue's custodian_ library was adapted (with permission) to create the DictMod language option for updating child FireWorks. Incidentally, the custodian library is a nice complement to FireWorks for use in FireTasks that is employed by the Materials Project.

Wei Chen added the reporting package. He was the first test pilot of FireWorks, and contributed greatly to improving the docs and ensuring that FireWorks installation went smoothly for others. In addition, he made many suggestions to improve the usability of the code.

Bharat Medasani and Dan Gunter added many unit tests and improved performance and scalability for large workflows.

Xiaohui Qu wrote the multi job launcher, with help from Anubhav Jain and advice from Dan Gunter.

Michael Kocher and Dan Gunter initiated the architecture of a central MongoDB database with multiple workers that queued 'placeholder' scripts responsible for checking out jobs. Some of Michael's code was refashioned for the QueueLauncher and the PBS QueueAdapter.

Guido Petretto added useful features, including task-level reruns, and helped detect and fix bugs.

Morgan Hargrove wrote the "base site" web frontend as part of a summer project at LBL (later superceded by Flask site). Miriam Brafman did the intial port of the web frontend to Flask and reworked the CSS.

David Waroquiers wrote the SLURM queue adapter, helped write the FileTransferTask, and provided useful feedback.

Chris Harris helped spruce up the frontend using Cytoscape.

William Davidson Richards wrote the SGE queue adapter and provided useful feedback and bug fixes.

Felix Brockherde added support for the IBM LoadLeveler queueing system and helped stomp bugs.

Zach Ulissi added support for IBM LoadSharing facility.

William Scullin added ALCF Cobalt support and helped stomp bugs.

Brian Foster, kpoman, jakirkham, Ganesh Panchapakesan, Patrick Huck, Donny Winston, Joey Montoya, Henrik Rusche, David Cossey, David Dotson, specter119, Kiran Mathew, Felix Zapata, and Dale Stansberry helped stomp bugs and provide improvements.

Thanks to Marat Valiev for suggesting Jinja2 as a lightweight templating alternative to Django and Stephen Bailey and Deborah Bard for helpful discussions.

We thank JetBrains for providing PyCharm IDE licenses for FireWorks developers.

.. _pymatgen: http://packages.python.org/pymatgen/
.. _custodian: https://pypi.python.org/pypi/custodian
