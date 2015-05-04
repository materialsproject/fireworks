========================================
Using the ScriptTask to execute commands
========================================

The ScriptTask is a FireTask built-in to FireWorks to help run non-Python programs through the command line. For example, you could use the ScriptTask to execute a Java "JAR" file or a C++ code. Internally,ScriptTask runs your script through a thin Python wrapper (the ScriptTask is really just another FireTask and doesn't have any special privileges).

The advantage of the built-in ScriptTask is that a lot of features and options have already been implemented. Let's examine these now.

Required parameter
==================

The ScriptTask parameter requires setting the *script* parameter:

* ``script`` - *(str)* or *[(str)]* - a String script to run, or an array of scripts to run in sequence

ScriptTask options
==================

The ScriptTask can take in many parameters. We already examined the ``script`` parameter of ScriptTask in the :doc:`Introductory tutorial <introduction>`; this parameter sets the script to run. It is the only required parameter. Other optional parameters are:

* ``defuse_bad_rc`` - *(default:False)* - if set True, a non-zero returncode from the Script (indicating error) will cause FireWorks to defuse the child FireWorks rather than continuing.
* ``fizzle_bad_rc`` - *(default:False)* - if set True, a non-zero returncode from the Script (indicating error) will cause the Firework to raise an error and FIZZLE.
* ``use_shell`` - *(default:True)* - whether to execute the command through the current shell (e.g., BASH or CSH). If true, you will be able to use environment variables and shell operators; but, this method can be less secure.
* ``shell_exe`` - *(default:None)* - path to shell executable, e.g. */bin/bash*. Generally you do not need to set this unless you want to run through a non-default shell.
* ``stdin_file`` - *(default:None)* - feed this filepath as standard input to the script
* ``stdin_key`` - *(default:None)* - feed this String as standard input to the script
* ``store_stdout`` *(default:False)* - store the entire standard output in the Firework Launch object's *stored_data*
* ``stdout_file`` - *(default:None)* - store the entire standard output in this filepath. If None, the standard out will be streamed to *sys.stdout*
* ``store_stderr`` - *(default:False)* - store the entire standard error in the Firework Launch object's *stored_data*
* ``stderr_file`` - *(default:None)* - store the entire standard error in this filepath. If None, the standard error will be streamed to  *sys.stderr*

.. note:: These parameters do not go in the root of the FW **spec**. Rather, they go as parameters to the ``ScriptTask`` in the ``_tasks`` section of the **spec** (in the same section as the ``script`` parameter in the :doc:`Introductory tutorial <introduction>`).

Manually setting the ScriptTask FWAction
========================================

The built-in ScriptTask options might not be flexible enough to handle all your needs. For example, you might want to return a complex *FWAction* that stores custom data from your job and modifies the Workflow in a complex way (within, for example your Java or C++ code).

To accomplish this, your script can write a file called ``FWAction.json`` or ``FWAction.yaml`` in the launch directory, and that contains a serialization of the *FWAction* object. FireWorks will read this file and replace the simple *FWAction* returned by ScriptTask with the one you specify in this file.

The _use_global_spec option
===========================

By default, the parameters for the ScriptTask should be defined within the ``_task`` section of the **spec** corresponding to the ScriptTask, not as a root key of the **spec**. If you'd like to instead specify the parameters in the root of the **spec**, you can set ``_use_global_spec`` to True within the ``_task`` section. Note that ``_use_global_spec`` can simplify querying and communication of parameters between FireWorks but can cause problems if you have multiple ScriptTasks within the same Firework.




