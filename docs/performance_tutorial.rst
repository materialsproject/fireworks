===============================
Improving FireWorks performance
===============================

For the most part, you shouldn't need to tinker with Firework's performance. One issue you might run into is speed of querying FireWorks by their spec or workflows by a field in their metadata. This issue might also manifest itself as slow duplicate checking queries. You can add *indices* to certain fields of your Firework specification in order to improve query performances.

How to add an index to a FW spec
================================

If you are initializing the LaunchPad using Python, set the ``user_indices`` argument to contain an array the fields you want to index. Make sure to prefix the names with ``spec``. For example, you might put ``["spec.parameter1", "spec.parameter2"]``.

If you are using a ``my_launchpad.yaml`` file, add the array in YAML format to a key called ``user_indices``. e.g., add the following::

    user_indices:
    - spec.parameter1
    - spec.parameter2

How to add an index to Workflow metadata
========================================

If you are initializing the LaunchPad using Python, set the ``wf_user_indices`` argument to contain an array the fields you want to index. Make sure to prefix the names with ``metadata``. For example, you might put ``["metadata.parameter1", "metadata.parameter2"]``.

If you are using a ``my_launchpad.yaml`` file, add the array in YAML format to a key called ``wf_user_indices``. e.g., add the following::

    wf_user_indices:
    - metadata.parameter1
    - metadata.parameter2

Further performance tweaks
==========================

A few other (very minor) performance tuning parameters are available via the :doc:`FW configuration <config_tutorial>`, although in most cases you shouldn't need to change these.