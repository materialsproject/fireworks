=================================
Dealing with Failures and Crashes
=================================

.. warning:: This documentation is written as a **tutorial** that starts from a clean FireWorks database. If you have an existing FireWorks database and need to deal with a failure or crash, do **not** reset your FireWorks database as the tutorial instructs. Instead, first read through this tutorial to get an idea on how failures work in FireWorks. Then, refer to the :doc:`database maintenance instructions </maintain_tutorial>`.

Job exceptions, node failures, and system outages are all unfortunate realities of executing workflows. You'll likely encounter some of these events when running FireWorks. This tutorial will simulate some of these events, so you can see how FireWorks detects job failures and what you can do about it.

Normal operation
================

Let's first introduce normal operation of a Firework that prints ``starting``, sleeps for 10 seconds, and then prints ``ending``. The Firework is completed successfully only if ``ending`` gets printed.

#. Move to the ``failures`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/failures

#. Look inside ``fw_sleep.yaml``. It should be pretty straightforward - we are printing text, sleeping, and printing text again.

   .. note:: You can increase or decrease the sleep time, depending on your patience level and reaction time later on in the tutorial.

#. Let's add and run this Firework. You'll have to wait 10 seconds for it to complete::

    lpad reset
    lpad add fw_sleep.yaml
    rlaunch singleshot

#. Hopefully, your patience was rewarded with ``ending`` printed to your terminal. If so, let's keep going!

Error during run - a *FIZZLED* Firework!
========================================

If your job throws an exception (error), FireWorks will automatically mark your job as *FIZZLED*. Any jobs that depend on this job will not run until you fix things. Let's simulate this situation.

#. Reset your database and add back the sleeping Firework::

    lpad reset
    lpad add fw_sleep.yaml

#. We'll run the Firework again, but this time you should interrupt its operation using the keyboard shortcut to stop execution(Ctrl+C). Make sure you hit that keyboard combo immediately after running the job, before you see the text ``ending``::

    rlaunch singleshot
    (Ctrl+C)

#. If you did this correctly, you'll have seen the text ``starting`` but not the text ``ending``. You might also see some error text printed to your terminal.

#. This behavior is what happens when your job throws an error (such as the *KeyboardInterrupt* error we just simulated). Let's see what became of this ill-fated Firework::

    lpad get_fws -i 1 -d all

#. You should notice the state of this Firework is automatically marked as *FIZZLED*. In addition, if you look at the **stored_data** key, you'll see that there's information about the error that was encountered during the run. If you're thorough, you'll see something about a *KeyboardInterruptError*.

   .. note:: If the exception thrown by the job implements the ``to_dict()`` method, this will be called to serialize customized information about the exception and add them to the ``stored_data``.

#. If at any point you want to review what FireWorks have *FIZZLED*, you can use the following query::

    lpad get_fws -s FIZZLED -d ids

Catastrophic Failure
====================

The previous failure was easy to detect; the job threw an error, and the Rocket was able to catch that error and tell the LaunchPad to mark the job as *FIZZLED*. However, more catastrophic failures are possible. For example, you might have a power failure in your computer center. In that case, there is no time for the Rocket to report to FireWorks that there is a failure. Let's see how to handle this case.

#. Reset your database and add back the sleeping Firework::

    lpad reset
    lpad add fw_sleep.yaml

#. We'll run the Firework again, but this time you should interrupt its operation by **forcibly closing your terminal window** (immediately after running the job, before you see the text ``ending``)::

    rlaunch singleshot
    ----(forcibly close your terminal window)

#. Now let's re-open a terminal window and see what FireWorks thinks is happening with this job::

    lpad get_fws -i 1 -d more

#. You should notice that FireWorks still thinks this job is *RUNNING*! We can fix this using the following command::

    lpad detect_lostruns --time 1 --fizzle

   .. note:: Instead of using ``--fizzle``, you could instead use ``--rerun``. This would mark the Launch as being FIZZLED and then rerun the Firework.
   .. note:: An additional constraint, ``--max_runtime``, can be used if you are looking for jobs that ran only a short time before failing. This can be useful to track down if a job was killed because it did not have walltime to run (if it was started in the middle of the queue job). Note that you should set this parameter to be in slightly larger intervals of the ping_time, since runtime is determined using pings.

#. This command will mark all jobs that have been running for more than 1 second as *FIZZLED*. We'll improve this in a bit, but for now let's check to make sure the command worked::

    lpad get_fws -i 1 -d more

#. The Firework should now be correctly listed as *FIZZLED*!

#. Of course, in production you'll never want to mark all jobs running for 1 second as being *FIZZLED*; this will mark jobs that are running properly as *FIZZLED*!

#. In production, you need not specify the ``--time`` parameter at all. FireWorks will automatically detect a job as *FIZZLED* after 4 hours of idle time when you run ``lpad detect_lostruns``. Jobs that are running properly, even if they take longer than 4 hours, will not be marked as *FIZZLED*. This is because the Rocket will automatically ping the LaunchPad that it's *alive* every hour. FireWorks will only mark jobs as *FIZZLED* when it does not receive this ping from the Rocket for 4 hours. You can test this feature with the following sequence of commands::


    lpad reset
    lpad add fw_sleep.yaml
    rlaunch singleshot
    ---(forcibly close your terminal window)
    ---(wait 4 or more hours!! or temporarily set your System Clock ahead by 5 hours)
    lpad detect_lostruns --fizzle
    lpad get_fws -i 1 -d all

.. note:: You can shorten the ping times and detection times by editing the settings in your :doc:`FW configuration </config_tutorial>`, but we suggest you leave them alone unless really needed.

.. note:: In production, you can use the :doc:`database maintenance instructions </maintain_tutorial>` instead of calling ``lpad_detect_lostruns --fizzle``.

Life after *FIZZLED*
====================

Once FireWorks has identified a job as *FIZZLED*, you might wonder what comes next. One option is to resubmit your workflow, perhaps with modifications to prevent any problems that might have caused job failure. If you've correctly enabled :doc:`duplicate checking </duplicates_tutorial>`, your new workflow will automatically pick up where you left off, and you won't do any extra calculations. This is the preferred way of dealing with failures. If you haven't enabled duplicate checking, then you can also :doc:`rerun your workflow </rerun_tutorial>`, starting from the failed job. If the ``EXCEPT_DETAILS_ON_RERUN`` option is enabled in your :doc:`FW configuration </config_tutorial>`, the exception details serialized during the last launch will be copied in the spec under the key ``_exception_details``. Customized exceptions can then be implemented to store information that help properly restart the job. The only caveat to this latter method is that dynamic actions already taken by your workflow will **not** be reset to their initial state.

You can also continue on with the Workflow even after *FIZZLED* by setting the ``_allow_fizzled_parents`` parameter in your **spec**. This will allow you to algorithmically fix errors using FireWorks' dynamic workflow features. This is a fairly advanced use case and will be covered in a future tutorial.

Database locks and inconsistencies
==================================

When updating the state of the Firework, FireWorks needs to acquire a lock on the database to safely update the state of the whole workflow. As this procedure may require some time, if many Fireworks belonging to the same Workflow try to update their state simultaneously the waiting time could easily reach the limit (see WFLOCK_EXPIRATION_SECS in :doc:`FW config </config_tutorial>`). If this happens, FireWorks by default will let the job stop, leaving the database in an inconsistent state. Like in the previous cases, these jobs could be identified running ``lpad detect_lostruns`` and the consistency in the database could be restored using the option ``--refresh``. This will refresh the state of the Workflow, applying the correct actions where needed.

Automatically report what parameters cause job failures (beta)
==============================================================

It is one thing to know that many jobs failed via the FIZZLED state, but it is better if one can identify the cause of failure. FireWorks can try to automatically detect what parameters are causing jobs to fail by introspecting the database and compiling a report of what keys in the FireWork ``spec`` and Workflow ``metadata`` are most associated with failed jobs. Thus, if you have a descriptive spec and metadata, it can be used to automatically classify jobs.

The introspect feature is in beta, but you can learn more via::

    lpad introspect -h

The introspect command can be very powerful when used in conjunction with the reporting features (``lpad report``). Contact FireWorks support for more information.