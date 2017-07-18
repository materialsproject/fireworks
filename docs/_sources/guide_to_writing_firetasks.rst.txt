========================================================
The Comprehensive Guide to Writing Firetasks with Python
========================================================

This guide covers in more detail how one can write their own Firetasks (and return dynamic actions), and assemble those Firetasks into FireWorks and Workflows. This guide will also cover the FWAction object, passing data, and dynamic workflow actions.

A "Hello World Example"
=======================

If you'd like to see a "Hello World" Example of a custom Firetask, you can go `here <https://github.com/materialsproject/fireworks/tree/master/fireworks/examples/custom_firetasks/hello_world>`_.

If you are able to run that example and want more details of how to modify and extend it, read on...

Writing a Basic Firetask
========================

Step 1: Choose existing Firetask(s) or write your own?
------------------------------------------------------

The first thing you should decide is whether to use an existing Firetask or write your own. FireWorks comes pre-packaged with many "default" Firetasks - in particular, the :doc:`PyTask <pytask>` allows you to call any Python function. There are also existing Firetasks for running scripts, remotely transferring files, etc. The quickest route to getting something running is to use an existing Firetask, i.e. use the :doc:`PyTask <pytask>` if you want to run a quick script.

Links to documentation on default Firetasks can be found in the :doc:`main page <index>` under the heading "built-in Firetasks".

A few reasons to *not* use the default Firetasks are:

* You want to give your Firetasks custom names
* You prefer a class-based method to defining tasks rather than the function-based method of :doc:`PyTask <pytask>`
* You want control over how the Firetask is constructed, e.g., define required parameters.

Step 2: Start with a Firetask template and modify it
----------------------------------------------------

The easiest way to understand a Firetask is to examine an example; for example, here's one implementation of a task to archive files::

 class ArchiveDirTask(FiretaskBase):
    """
    Wrapper around shutil.make_archive to make tar archives.

    Args:
        base_name (str): Name of the file to create.
        format (str): Optional. one of "zip", "tar", "bztar" or "gztar".
    """

    _fw_name = 'ArchiveDirTask'
    required_params = ["base_name"]
    optional_params = ["format"]

    def run_task(self, fw_spec):
        shutil.make_archive(self["base_name"], format=self.get("format", "gztar"), root_dir=".")


You can copy this code to a new place and make the following modifications in order to write your Firetask:

* In the first line, the name of the class (*ArchiveDirTask*) can be anything - it does not affect the operation of the code if you follow the structure above.
    * *Change the class name to anything you desire.*
* The class extends the *FiretaskBase* abstract class. This abstract class does some work under the covers and also requires that you define a ``run_task(self, fw_spec)`` method.
    * *Keep this intact.*
* The ``_fw_name`` is how this Firetask is identified. It must be a unique name that is always retained. See the Appendix section for working around this and an alternate formulations for identifying the Firetask.
    * *Change the ``fw_name`` value to a desired identifier for your Firetask, e.g. MyFavoriteTask.*
* The ``required_params`` and ``optional_params`` relate to how the Firetask is constructed. In the example above, an *ArchiveTask* could be instantiated using something like ``my_task = ArchiveTask(base_name="my_filename", format="bztar")``. Because ``base_name`` is in ``required_params``, it **must** be specified (``optional_params`` does not actually *do* anything).
    * *Add your required and optional parameters as desired.*
* The meat of the Firetask is the ``run_task(self, fw_spec)`` method. It has two sources of information: the keys in ``fw_spec`` and a dictionary of ``self`` (which includes parameters like ``base_name`` used to construct the object). In this case, it's tarring and gzipping some files according to the parameters the dictionary of itself, and ignoring anything in the ``fw_spec``.
    *Keep the run_task method header intact, but change the definition to your custom operation. Remember you can access dict keys of "fw_spec" as well as dict keys of "self"*

Step 3: Register your Firetask
------------------------------

When FireWorks bootstraps your Firetask from a database definition, it needs to know where to look for Firetasks.

**First**, you need to make sure your Firetask is defined in a file location that can be found by Python, i.e. is within Python's search path and that you can import your Firetask in a Python shell. If Python cannot import your code (e.g., from the shell), neither can FireWorks. This step usually means either installing the code into your ``site-packages`` directory (where many Python tools install code) or modifying your ``PYTHONPATH`` environment variable to include the location of the Firetask. You can see the locations where Python looks for code by typing ``import sys`` followed by ``print(sys.path)``. If you are unfamiliar with this topic, some more details about this process can be found `here <http://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch28s04.html>`_, or try Googling "how does Python find modules?"

**Second**, you must register your Firetask so that it can be found by the FireWorks software. There are a couple of options for registering your Firetask (you only need to do *one* of the below):

1. Use the **@explicit_serialize** decorator to define your FW name (see the Appendix). No further registration is needed if you use this option.
#. (or) if you have access to the FireWorks source directory, put your Firetask definition anywhere in ``fireworks.user_objects`` or it subdirectories - it will be automatically be found there.
#. (or) put the Firetask wherever you'd like. However, you need to modify the ``USER_PACKAGES`` variable of the :doc:`FW config <config_tutorial>` to include the package for where to find the Firetask, e.g. "mypackage.my_subpackage". Note that FireWorks will search within subpackages automatically, so you can just put a root package (but loading will be slightly slower).

You are now ready to use your Firetask!

Dynamic and message-passing Workflows
=====================================

In the previous example, the ``run_task`` method did not return anything, nor does it pass data to downstream Firetasks or FireWorks. Remember that the setting the ``_pass_job_info`` key in the Firework spec to True will automatically pass information about the current job to the child job - see :doc:`reference <reference>` for more details.

However, one can also return a ``FWAction`` object that performs many powerful actions including dynamic workflows.

Here's an example of a Firetask implementation that includes dynamic actions via the *FWAction* object::

 class FibonacciAdderTask(FiretaskBase):
    _fw_name = "Fibonacci Adder Task"

    def run_task(self, fw_spec):
        smaller = fw_spec['smaller']
        larger = fw_spec['larger']
        stop_point = fw_spec['stop_point']

        m_sum = smaller + larger
        if m_sum < stop_point:
            print('The next Fibonacci number is: {}'.format(m_sum))
            # create a new Fibonacci Adder to add to the workflow
            new_fw = Firework(FibonacciAdderTask(), {'smaller': larger, 'larger': m_sum, 'stop_point': stop_point})
            return FWAction(stored_data={'next_fibnum': m_sum}, additions=new_fw)

        else:
            print('We have now exceeded our limit; (the next Fibonacci number would have been: {})'.format(m_sum))
            return FWAction()

We discussed running this example in the :doc:`Dynamic Workflow tutorial <dynamic_wf_tutorial>` - if you have not gone through that tutorial, we strongly suggest you do so now (it also includes an example of message passing).

Note that this example is slightly different than the previous one:

* We did not define any required or optional parameters. The parameters are taken from the ``fw_spec`` rather than ``self``.
* We are explicitly returning *FWAction* objects. In one case, the object looks to be storing data and adding FireWorks.

Other than those differences, the code is the same format as earlier. The dynamicism comes only from the *FWAction* object; next, we will this object in more detail.

The FWAction object
===================

A Firetask (or a function called by :doc:`PyTask <pytask>`) can return a *FWAction* object that can perform many powerful actions. Note that the *FWAction* is stored in the FW database after execution, so you can always go back and see what actions were returned by different Firetasks. A diagram of the different FWActions is below:

.. image:: _static/fwactions.png
   :alt: FW actions
   :align: center

The parameters of FWAction are as follows:

* **stored_data**: *(dict)* data to store from the run. The data is put in the Launch database along with the rest of the FWAction. Does not affect the operation of FireWorks.
* **exit**: *(bool)* if set to True, any remaining Firetasks within the same Firework are skipped (like a ``break`` statement for a Firework).
* **update_spec**: *(dict)* A data dict that will update the spec for any remaining Firetasks *and* the following Firework. Thus, this parameter can be used to pass data between Firetasks or between FireWorks. Note that if the original fw_spec and the update_spec contain the same key, the original will be overwritten.
* **mod_spec**: ([dict]) This has the same purpose as update_spec - to pass data between Firetasks/FireWorks. However, the update_spec option is limited in that it can't increment variables or append to lists. This parameter allows one to update the child FW's spec using the DictMod language, a Mongo-like syntax that allows more fine-grained changes to the fw_spec.
* **additions**: ([Workflow]) a list of WFs/FWs to add as children to this Firework.
* **detours**: ([Workflow]) a list of WFs/FWs to add as children (they will inherit the current FW's children)
* **defuse_children**: (bool) defuse all the original children of this Firework
* **defuse_workflow**: (bool) defuse all incomplete FWs in this Workflow

The FWAction thereby allows you to *command* the workflow programmatically, allowing for the design of intelligent workflows that react dynamically to results.

Appendix 1: accessing the LaunchPad within the Firetask
=======================================================

It is generally not good practice to use the LaunchPad within the Firetask because this makes the task specification less explicit. For example, this could make duplicate checking more problematic. However, if you really need to access the LaunchPad within a Firetask, you can set the ``_add_launchpad_and_fw_id`` key of the Firework spec to be True. Then, your tasks will be able to access two new variables, ``launchpad`` (a LaunchPad object) and ``fw_id`` (an int), as members of your Firetask. One example is shown in the unit test ``test_add_lp_and_fw_id()``.


Appendix 2: alternate ways to identify the Firetask and changing the identification
===================================================================================

Other than explicitly defining a ``_fw_name`` parameter, there are two alternate ways to identify the Firetask:

* You can omit the ``_fw_name`` parameter altogether, and the code will then use the Class name as the identifier. However, note that this is dangerous as changing your Class name later on can break your code. In addition, if you have two Firetasks with the same name the code will throw an error.
* (or) You can omit the ``_fw_name`` **and** add an ``@explicit_serialize`` decorator to your Class. This will identify your class by the module name AND class name. This prevents namespace collisions, AND it allows you to skip registering your Firetask! However, the serialization is even more sensitive to refactoring: moving your Class to a different module will break the code, as will renaming it. Here's an example of how to use the decorator::

    from fireworks.utilities.fw_utilities import explicit_serialize

    @explicit_serialize
    class PrintFW(FiretaskBase):
        def run_task(self, fw_spec):
            print str(fw_spec['print'])

In both cases of removing ``_fw_name``, there is still a workaround if you refactor your code. The :doc:`FW config <config_tutorial>` has a parameter called ``FW_NAME_UPDATES`` that allows one to map old names to new ones via a dictionary of {<old name>:<new name>}. This method also works if you need to change your ``_fw_name`` for any reason.
