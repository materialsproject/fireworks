===============================
Running Tasks in the Background
===============================

When running a Firework, the FireTasks are run sequentially in the main thread. One way to run a background thread would be to write a FireTask that spawns a new Thread to perform some work. However, FireWorks also has a built-in method to run background tasks via BackgroundTasks. Each BackgroundTask is run in its own thread, in *parallel* to the main FireTasks, and can be repeated at stated intervals.

BackgroundTasks parameters
==========================

BackgroundTasks have the following properties:

* **tasks** - a list of FireTasks to execute in sequence. The FireTasks can read the initial spec of the Firework. Any action returned by FireTasks within a BackgroundTask is *NOT* interpreted (including instructions to store data).
* **num_launches** - the total number of times to repeat the BackgroundTask. 0 or less indicates infinite repeats.
* **sleep_time** - amount of time in seconds to sleep before repeating the BackgroundTask
* **run_on_finish** - if True, the BackgroundTask will be run one last time at the end of the Firework

Setting one or more BackgroundTasks (via file)
==============================================

The easiest way to set BackgroundTasks is via the Python code. However, if you are using flat files, you can define BackgroundTasks via the ``_background_tasks`` reserved keyword in the FW spec::

    spec:
      _background_tasks:
      - _fw_name: BackgroundTask
        num_launches: 0
        run_on_finish: false
        sleep_time: 10
        tasks:
        - _fw_name: ScriptTask
          script:
          - echo "hello from BACKGROUND thread #1"
          use_shell: true
      - _fw_name: BackgroundTask
        num_launches: 0
        run_on_finish: true
        sleep_time: 5
        tasks:
        - _fw_name: ScriptTask
          script:
          - echo "hello from BACKGROUND thread #2"
          use_shell: true
      _tasks:
      - _fw_name: ScriptTask
        script:
        - echo "starting"; sleep 30; echo "ending"
        use_shell: true

The specification above has two BackgroundTasks, one which repeats every 10 seconds and another which repeats every 5 seconds.

Setting one or more BackgroundTasks (via Python)
================================================

You can define a BackgroundTask via::

    bg_task = BackgroundTask(ScriptTask.from_str('echo "hello from BACKGROUND thread"'), num_launches=0, sleep_time=5, run_on_finish=True)

and add it to a Firework via::

    fw = Firework([my_firetasks], spec={'_background_tasks':[bg_task]})

Python example
==============

The following code runs a script that, in the main thread, prints 'starting', sleeps, then prints 'ending'. In separate threads, two background threads run at different intervals. The second BackgroundTask has ``run_on_finish`` set to True, so it also runs after the main thread finishes::

    from fireworks import Firework, FWorker, LaunchPad, ScriptTask
    from fireworks.features.background_task import BackgroundTask
    from fireworks.core.rocket_launcher import rapidfire

    # set up the LaunchPad and reset it
    launchpad = LaunchPad()
    launchpad.reset('TODAYS DATE')  # set TODAYS DATE to be something like 2014-02-10

    firetask1 = ScriptTask.from_str('echo "starting"; sleep 30; echo "ending"')
    bg_task1 = BackgroundTask(ScriptTask.from_str('echo "hello from BACKGROUND thread #1"'), sleep_time=10)
    bg_task2 = BackgroundTask(ScriptTask.from_str('echo "hello from BACKGROUND thread #2"'), num_launches=0, sleep_time=5, run_on_finish=True)

    # create the Firework consisting of a custom "Fibonacci" task
    firework = Firework(firetask1, spec={'_background_tasks': [bg_task1, bg_task2]})

    ## store workflow and launch it locally
    launchpad.add_wf(firework)
    rapidfire(launchpad, FWorker())
