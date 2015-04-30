=============================================
Using the TemplateWriterTask to write files
=============================================

A common task in scientific workflows is to write an input file in a format that can be read by a program, and then execute that program. When automating the same program for different inputs (like different molecules or sections of a galaxy), slight modifications to the input file are needed. This tutorial introduces the built-in *TemplateWriterTask* as a method for writing input files (or any other type of templated file).

We presented an example of using the *TemplateWriterTask* and subsequently running a program in the :doc:`FireTask tutorial <firetask_tutorial>`. If you didn't already complete the first part of that tutorial, we suggest you do that first. This tutorial contains more details on how the *TemplateWriterTask* works.

.. note:: The *TemplateWriterTask* is uses the Jinja2 templating engine, which provides a simple, extensible templating language.

A simple template - variable substitutions
==========================================

We introduced a simple template in the :doc:`FireTask tutorial <firetask_tutorial>`. Let's explore this template in more detail.

1. Navigate to the template writer tutorial directory on your FireServer::

    cd <INSTALL_DIR>/fw_tutorials/templatewritertask

#. Look inside the file ``simple_template_copy.txt``::

    option1 = {{opt1}}
    option2 = {{opt2}}

   .. note:: The template file can be any text file, with any extension (or no extension at all). The actual template file is stored within the FireWorks code, so modifying this copy of a file won't have any effect (more on this later in the tutorial).

#.  Most of the template file is interpreted literally and is static. However, the text inside double curly braces ``{{`` and ``}}`` are **variables** that will be replaced later on by other text.

#. We set the variables **opt1** and **opt2** using a *Context*. This is a dictionary that contains specific values for these parameters. Let's see how this is defined by looking inside ``fw_template.yaml``::

    spec:
      _tasks:
      - _fw_name: TemplateWriterTask
        template_file: simple_template.txt
        context:
          opt1: 5.0
          opt2: fast method
        output_file: inputs.txt

   Note that we have specified a ``template_file``, a ``context``, and an ``output_file``. All three of these parameters are needed to use the *TemplateWriterTask*.

#. In the Firework above, we are setting **opt1** to 5.0 and **opt2** to "fast method". If we wanted to change these parameters, we can create a file like ``fw_template2.yaml``::

    spec:
      _tasks:
      - _fw_name: TemplateWriterTask
        template_file: simple_template.txt
        context:
          opt1: 10.0
          opt2: stable method
        output_file: inputs.txt

#. This second Firework is identical to the first, except that we have changed the value of variables **opt1** and **opt2**. Thus, we have only changed the parameter values we care about when creating a new Firework. In addition, one could easily perform searches based on **opt1** and **opt2** values using MongoDB's built-in search capabilities.

#. Let's reset the database, add these FireWorks to the LaunchPad, and then execute them::

 	lpad reset
	lpad add fw_template.yaml
	lpad add fw_template2.yaml
	rlaunch --silencer rapidfire

#. If all went well, you should have two ``launcher_`` subdirectories. Each directory contains a file called ``inputs.txt`` that uses the same template file but different Contexts to create unique input files. Recall from the :doc:`FireTask tutorial <firetask_tutorial>` that you could use a multi-task Firework to subsequently run a code that processes the input file to produce useful outputs.

A more advanced template - *if/then* and *for*
==============================================

Template files are not restricted to simple variable substitutions with curly braces. You can also define *if/then* statements and *for loops* that process array-like items. This can make your templates more flexible, for example writing an input tag only if a certain variable is present in the Context.

1. Staying in the template writer tutorial directory, look inside the file ``advanced_template_copy.txt``::

    option1 = {{opt1}}
    option2 = {{opt2}}

    {% if optparam %}OPTIONAL PARAMETER
    {{ optparam }}{% endif %}

    LOOP PARAMETERS
    {% for param in param_list %}{{ param }}
    {% endfor %}

   .. note:: The actual template file is stored within the FireWorks code, so modifying this copy of a file won't have any effect (more on this later in the tutorial).

#. Note that this template contains some additional tags. In particular, in between ``{%`` and ``%}`` we have some code that contains *if/then* statements and a *for* loop.

#. A Context for this template is in ``fw_advanced.yaml``::

    spec:
      _tasks:
      - _fw_name: TemplateWriterTask
        context:
          opt1: 5.0
          opt2: fast method
          optparam: true
          param_list:
          - 1
          - 2
          - 3
          - 4
        output_file: inputs_advanced.txt
        template_file: advanced_template.txt

#. Let's run this Firework and examine what happens::

    lpad reset
    lpad add fw_advanced.yaml
    rlaunch --silencer singleshot

#. You'll notice that we've iterated over our loop, and the optional parameter is indeed written to ``inputs_advanced.txt``.

#. Now, try deleting the line containing the ``optparam`` and repeating the launch process. You'll see that the lines pertaining to the ``OPTIONAL PARAMETER`` are no longer written!

Therefore, with Jinja2's templating language we can write fairly general templates. While variable substitutions, *if/then* statements, and *for loops* should cover the majority of cases, you can see even more features in the `official Jinja2 documentation <http://jinja.pocoo.org>`_. For example, you can use template inheritance or insert templates into other templates.

Writing your own templates
==========================

When writing your own templates, you have a few options on where to store the templates so they can be read by FireWorks. Note that all the worker computers using the templates must have the most recent templates installed locally.

Option 1: The user_objects directory of the FireWorks code
----------------------------------------------------------

The default place that FireWorks looks for templates is in the ``user_objects/firetasks/templates`` directory of your FireWorks installation. Indeed, the ``simple_template.txt`` and ``advanced_template.txt`` files used in this tutorial are stored there (that's why modifying the tutorial files has no effect on the result). Any templates you put in this directory (or its subdirectories) will be read by FireWorks; just put the relative path of your template as the ``template_file`` parameter.

.. note:: If you do not know how to find the correct directory, type ``lpad version``. Then navigate to the install directory, then ``cd fireworks/user_objects/firetasks/templates``.

Option 2: Set the template directory in FWConfig
------------------------------------------------

If you do not want to store your templates within the FireWorks code, you can set a template directory in the :doc:`FWConfig <config_tutorial>`. Just set the parameter ``TEMPLATE_DIR`` to point to the location of your templates. Then the ``template_file`` parameter you pass to your FireWorks will be relative to this path. Remember to do this for all your workers!

Additional options
==================

In addition to ``template_file``, ``context``, and ``output_file``, the following options can be passed into ``TemplateWriterTask``:

   * ``append`` - append to the output file, rather than overwriting it
   * ``template_dir`` - this is actually a third option for setting your template dir

The _use_global_spec option
===========================

By default, the parameters for the TemplateWriterTask should be defined within the ``_task`` section of the **spec** corresponding to the TemplateWriterTask, not as a root key of the **spec**. If you'd like to instead specify the parameters in the root of the **spec**, you can set ``_use_global_spec`` to True within the ``_task`` section. Note that ``_use_global_spec`` can simplify querying and communication of parameters between FireWorks but can cause problems if you have multiple TemplateWriterTasks within the same Firework.

Python example
==============

A runnable Python example illustrating the use of templates was given in the :doc:`FireTask tutorial <firetask_tutorial>`.

