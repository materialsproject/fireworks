======
PyTask
======

The PyTask allows you to call any Python function. That function can (optionally) return a *FWAction* to perform dynamic actions (e.g., see the :doc:`Guide to Writing FireTasks </guide_to_writing_firetasks>`). Thus, with the PyTask you can basically do anything!

Required parameters
===================

* **func**: *(str)* - Fully qualified python method. e.g., json.dump, or shutil.copy, or a user function!

Optional parameters
===================

* **args**: *(list)* - a list of args to feed into the function
* **kwargs**: *(dict)* - Dictionary of keyword args. Default is empty.
* **auto_kwargs**: *(bool)* - If True, all other params not starting with "_" are automatically supplied as keyword args
* **stored_data_varname**: *(str)* If this is a string that does not evaluate to False, the output of the function will be stored as FWAction(stored_data={stored_data_varname: output}). The name is deliberately long to avoid potential name conflicts.

Example
=======

Here is an example of defining a PyTask that sleeps for 5 seconds::

    fw_timer = Firework(PyTask(func='time.sleep',args=[5]))

Note that you can call any Python function this way!
