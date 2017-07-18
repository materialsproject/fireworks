========================================
Tracking an output file during execution
========================================

You can track the last few lines of file during Firework execution. For example, you can monitor an output file to make sure the run is progressing as expected. Setting one or more such *trackers* is simple.

Adding a tracker (via files)
============================

To add a tracker, set a key called ``_tracker`` in your *fw_spec* to be an array of objects with ``filename`` and ``nlines`` keys. Each tracker will track the desired number of final lines of a particular file. The example below has two trackers, one for ``inputs.txt`` and another for ``words.txt`` (see the ``_trackers`` section at the bottom)::

    name: Tracker FW
    spec:
      _tasks:
      - _fw_name: TemplateWriterTask
        context:
          opt1: 5.0
          opt2: fast method
        output_file: inputs.txt
        template_file: simple_template.txt
      - _fw_name: ScriptTask
        script: wc -w < inputs.txt > words.txt
        use_shell: true
      _trackers:
      - filename: words.txt
        nlines: 25
      - filename: inputs.txt
        nlines: 25

You can see this example in <INSTALL_DIR>/fw_tutorials/tracker.

Adding a tracker (via code)
===========================

The following code example creates the Firework above with two trackers::

    from fireworks import Firework, Tracker, ScriptTask, TemplateWriterTask

    # create the Firework consisting of multiple tasks
    firetask1 = TemplateWriterTask({'context': {'opt1': 5.0, 'opt2': 'fast method'}, 'template_file': 'simple_template.txt', 'output_file': 'inputs.txt'})
    firetask2 = ScriptTask.from_str('wc -w < inputs.txt > words.txt')
    # define the trackers
    tracker1 = Tracker('words.txt', nlines=25)
    tracker2 = Tracker('inputs.txt', nlines=25)
    fw = Firework([firetask1, firetask2], spec={"_trackers": [tracker1, tracker2]})

    fw.to_file('fw_tracker.yaml')


Viewing the tracked file
========================

You can view the tracked files for all FireWorks (during or after execution) with the command::

    lpad track_fws

which will print out data like::

    # FW id: 1
    ## Launch id: 1
    ### Filename: words.txt
           7
    ### Filename: inputs.txt
    option1 = 5.0
    option2 = fast method

Choosing the Firework(s) for which to view the tracked files
------------------------------------------------------------
Besides for the <FW_ID>, there are additional options for specifying the Firework(s) that you want to get the tracked data for. For example, you can search for the tracker data of a particular Firework id or of all *FIZZLED* FireWorks via::

    lpad track_fws -i <FW_ID>
    lpad track_fws -s FIZZLED

Type ``lpad track_fws -h`` to see all the options, including advanced queries.

Choosing the tracked files to display
-------------------------------------

The ``--include`` (or ``-c``) and ``--exclude`` (or ``-x``) options can be used to filter what files are displayed in the Tracker Report. The ``--include`` option means to only display those files, whereas the ``--exclude`` option means to filter out those files from the report::

    lpad track_fws --include words.txt
    lpad track_fws --exclude words.txt

You can separate multiple filenames by spaces.

Frequency of monitoring
=======================

The output file is monitored for changes at every update ping interval, as well as at the beginning and completion of execution. By default, the ping interval is set to be every hour; this is to avoid overloading the database with pings if tens of thousands of runs are happening simultaneously. You can change the ping interval (``PING_TIME_SECS``) in the :doc:`FW config <config_tutorial>`.

A note about nlines
===================

The tracker is meant to give basic debug information about a job, not to permanently store output files. There is a limit of 1000 lines to keep the Mongo document size reasonable, and to keep FireWorks performing well. We suggest you leave nlines to be less than 100 lines and only use this feature for basic debugging.