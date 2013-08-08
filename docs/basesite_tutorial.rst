========================================
Using the Web GUI *(alpha)*
========================================

An easy way to monitor FireWorks is to use its web interface (in *alpha* mode), which provides an overview of the state of your workflows and provides clickable links to see details on any FireWork or Workflow:

.. image:: _static/base_site.png
   :width: 600px
   :align: center
   :alt: Base Site screenshot

Launching the web framework
===========================

It is easy to launch the web framework using the LaunchPad::

    lpad webgui -b

if your LaunchPad file is automatically set via an environment variable on in the current directory (see the :doc:`config tutorial <config_tutorial>`), or::

    lpad -l my_launchpad.yaml webgui -b

if you need to explicitly specify the LaunchPad file to use.

The ``-b`` option opens up a browser on your machine and points it to the web GUI. You can omit this option if needed, e.g. to run a web server. Other options include ``--host`` and ``--port``, but you probably won't need to modify these.

Using the web framework
=======================

The current web framework is limited but simple - just click the links you are interested in. One thing to note is that the URLs can be easily modified to quickly bring up a particular FireWork, e.g.::

    http://127.0.0.1:8000/fw/1/

points to the data for FireWork id #1 (for the default host and port). You can easily modify this URL to check up on a particular FireWork.