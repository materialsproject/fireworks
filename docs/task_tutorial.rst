============================
Defining Jobs with FireTasks
============================

In the :doc:`installation tutorial <installation_tutorial>`, we ran a simple script that performed ``echo "howdy, your job launched successfully!" >> howdy.txt"``. However, you might have already noticed some limitations of defining a job this way:

* The command (``echo``), its arguments (``"howdy, your job launched successfully!"``), and its output (``howdy.txt``) were all intermingled within the same line. Ideally, these components should be separated out. For example, separating components make it do a data-parallel task where the same command (e.g., ``echo``) is run for multiple arguments.
* It's difficult to define a multi-step procedure; for example, writing an input file and then running a code that parses it.
* Allowing a completely arbitrary script to run could pose security risks.

.. note:: The security issue can be addressed by turning off ALLOW_SUBPROCESS in ``fw_constants.py``. For this tutorial, we'll assume that it's turned on.

In this section, we'll introduce a *FireTask*, which is a better way to define a job.

Improving our code with the SubProcess FireTask
-----------------------------------------------