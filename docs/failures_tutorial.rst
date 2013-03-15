=================================
Dealing with Failures and Crashes
=================================

Job exceptions, node failures, and system outages are all unfortunate realities of executing workflows. You'll likely encounter some of these events when running FireWorks. This tutorial will simulate some of these events, so you can see how FireWorks detects job failures and what you can do about it.

Normal operation
================

Let's first introduce normal operation of a FireWork that prints ``starting``, sleeps for 10 seconds, and then prints ``ending``. The FireWork is completed successfully only if ``ending`` gets printed.

#. Move to the ``failures`` tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/failures

#. Look inside ``fw_sleep.yaml``. It should be pretty straightforward - we are printing text, sleeping, and printing text again.

   .. note:: You can increase or decrease the sleep time, depending on your patience level and reaction time later on in the tutorial.

#. Let's add and run this FireWork. You'll have to wait 10 seconds for it to complete::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_sleep.yaml
    rlauncher_run.py singleshot

#. Hopefully, your patience was rewarded with ``ending`` printed to your terminal. If so, let's keep going!

Error during run - a *FIZZLED* Firework!
========================================

If your job throws an exception (error), FireWorks will automatically mark your job as *FIZZLED*. Any jobs that depend on this job will not run until you fix things. Let's simulate this situation.

#. Reset your database and add back the sleeping FireWork::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_sleep.yaml

#. We'll run the FireWork again, but this time you should interrupt its operation using the keyboard shortcut to stop execution(Ctrl+C or Ctrl+\). Make sure you hit that keyboard combo immediately after running the job, before you see the text ``ending``::

    rlauncher_run.py singleshot
    (Ctrl+C or Ctrl+\)

#. If you did this correctly, you'll have seen the text ``starting`` but not the text ``ending``. You might also see some error text printed to your terminal.

#. This behavior is what happens when your job throws an error (such as the *KeyboardInterrupt* error we just simulated). Let's see what became of this ill-fated FireWork::

    lp_run.py get_fw 1

#. You should notice the state of this FireWork is automatically marked as *FIZZLED*. In addition, if you look at the **stored_data** key, you'll see that there's information about the error that was encountered during the run.

#. If at any point you want to review what FireWorks have *FIZZLED*, you can use the following query::

    lp_run.py get_fw_ids -q '{"state":"FIZZLED"}'

Catastrophic Failure
====================

The previous failure was fairly clean; the job threw an error, and FireWorks was able to automatically mark the job as *FIZZLED*. However, more catastrophic failures are possible. For example, you might have a power failure in your computer center. In that case, there is no time for the Rocket to report to FireWorks that there is a failure. Let's see how to handle this case.

#. Reset your database and add back the sleeping FireWork::

    lp_run.py reset <TODAY'S DATE>
    lp_run.py add fw_sleep.yaml

#. We'll run the FireWork again, but this time you should interrupt its operation by **forcibly closing your terminal window** (immediately after running the job, before you see the text ``ending``)::

    rlauncher_run.py singleshot
    (forcibly close your terminal window)

#. Now let's re-open a terminal window and see what FireWorks thinks is happening with this job::

    lp_run.py get_fw 1

#. You should notice that FireWorks still thinks this job is *RUNNING*!