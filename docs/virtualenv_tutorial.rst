=======================
Virtualenv installation
=======================

In this tutorial, we'll cover just the basics of setting up a *virtualenv* for your FireWorks installation. Virtualenv allows you to isolate your FireWorks installation from your other Python installations. This is often done when there are conflicts (e.g., two codes require different versions of Python), and sometimes done just for cleanliness or to host separate testing and production environments. Another reason to use virtualenv is when you don't have permission to access the global Python "site-packages" directory, e.g. on a shared machine like a supercomputing center.

Introduction to virtualenv
==========================

Your virtualenv is stored inside a user-specified directory on your system. That directory will contain the Python 2.7.3 executable needed for FireWorks as well as all dependencies for the FireWorks code. When you activate your virtualenv, your "normal" Python executable will be bypassed in favor of the one in this directory. In addition, your normal "site packages" directory that contains your external Python libraries will be bypassed in favor of the one you set up in your virtualenv. Finally, your "pip" and "easy_install" will be bypassed so that they install packages to your virtualenv. When you deactivate your virtualenv, things will return back to their usual state.

If you'd like more details on virtualenv, you can read the `official documentation <https://pypi.python.org/pypi/virtualenv>`_ or see some basic setup instructions `here <http://pythoncentral.org/setting-up-the-python-environment-with-virtualenv/>`_, `or here <http://iamzed.com/2009/05/07/a-primer-on-virtualenv/>`_, `or also here <http://simononsoftware.com/virtualenv-tutorial/>`_.

Setting up virtualenv
=====================

1. First, download and install virtualenv with pip::

    pip install virtualenv

   .. note:: You may need administrator privileges, i.e. ``sudo pip install virtualenv``. At supercomputing centers, virtualenv might be available as a module and loadable using ``module load virtualenv``. Contact your system administrator if you have questions about this.

2. Create a directory that will contain your virtualenv files (Python exe and libraries for FireWorks). We'll call this ``FW_env`` but you can name it whatever you like::

    mkdir FW_env

3. Set up a clean virtual env into this directory::

    virtualenv --no-site-packages FW_env

4. Activate your virtual environment::

    source FW_env/bin/activate

Your bash prompt should change to show what environment you're in after you've activated the virtualenv. You can now continue with the :doc:`FireWorks installation instructions </installation>` in your virtual environment.

.. note:: If you ever want to deactivate and go back to normal, just type ``deactivate``.




