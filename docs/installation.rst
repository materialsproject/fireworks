====================
Installing FireWorks
====================

.. note:: We suggest that you use Python 2.7.3 or higher, especially in production (although Python 3+ is not tested). There is a `bug <https://groups.google.com/forum/#!topic/modwsgi/DW-SlIb07rE>`_ in Python 2.7.2 that could affect FireWorks (although we haven't seen any problems yet). As of FireWorks v0.7, Python 3.3 should also work.

Install MongoDB
===============

MongoDB powers the database backend of FireWorks. You need to install MongoDB on one machine to host the FireWorks database (the same machine can also be used to run jobs). Additional machines (i.e., that are used to run FireWorks jobs) do not require a MongoDB installation. FireWorks does not need to be installed on the same machine as your MongoDB installation.

To install MongoDB, follow the instructions at `MongoDB <http://www.mongodb.org>`_.

Preparing to Install FireWorks (Python and pip)
===============================================
To prepare for installation, you should:

#. Install `python 2.7 <http://www.python.org>`_ (preferably Python 2.7.3 or higher), if not already packaged with your system. To check your python version, use the command ``python --version``. As of FireWorks v0.7, Python 3.3 should also work.
#. Install `pip <http://www.pip-installer.org/en/latest/installing.html>`_, if not already packaged with your system. This will allow you to download required dependencies.

.. tip:: if you have easy_install configured, e.g. through `setuptools <http://pypi.python.org/pypi/setuptools>`_, you should be able to install pip using the command ``easy_install pip``. You should make sure that setuptools is installed using the proper Python version and probably without the ``--user`` option if running ``ez_setup.py``.

Virtualenv installation option
------------------------------

Virtualenv is a tool that allows you to separate your FireWorks installation from your other Python installations. For example, you might want to use Python 2.7 for FireWorks, but Python 3+ for other Python codes you're interested in using. Or, you might have different versions of Python libraries supporting FireWorks and your other installations. This is often the case on shared machines. if you're interested in this option, you might consider a :doc:`virtualenv install </virtualenv_tutorial>`. Otherwise, just follow the installation instructions below. A simpler option to setting up virtualenv that accomplishes some of the same goals is to use the ``--user`` flag when running ``python setup.py develop`` in the the Git version of installation (see Installation Method 2).

Installation Method 1: Use Pip
==============================

The easiest way to install FireWorks is to simply run a one-liner in pip. The downside of this method is that it is more difficult to view and edit the source code.

#. To install, simply type::

    pip install FireWorks
    pip install django  # (only needed if you want to use the built-in web frontend!)
    pip install paramiko  # (only needed if using built-in remote file transfer!)
    pip install fabric  # (only needed if using daemon mode of qlaunch!)
    pip install requests  # (only needed if you want to use the NEWT queue adapter!)

   .. note:: You may need administrator access, e.g. ``sudo pip install FireWorks``.

#. Separately, you can download the FireWork tutorial files if you plan on going through the tutorials. You can download these from the `FireWorks Github page <https://github.com/materialsproject/fireworks>`_. All you need is the ``fw_tutorial`` directory, but it might be easiest to download the entire source and just copy the ``fw_tutorial`` directory somewhere else.

Installation Method 2: Use Git to install in developer mode
===========================================================

The most comprehensive way to install FireWorks is in 'developer mode', which will allow you to easily view and modify the source code and fork the repo for development purposes. However, this method requires setting up an account on GitHub and properly setting up SSH keys.

#. Install `git <http://git-scm.com>`_, if not already packaged with your system. This will allow you to download the latest source code.

#. Run the following code to download the FireWorks source::

    git clone git@github.com:materialsproject/fireworks.git

   .. note:: Make sure you have an account on GitHub set up, and have associated your SSH key on your computer with your GitHub account. Otherwise you might get a cryptic ``Permission denied (publickey)`` error. Help on ssh keys can be found `here <https://help.github.com/articles/generating-ssh-keys>`_.

#. Navigate inside the FireWorks directory containing the file setup.py::

    cd fireworks

#. Run the following command (you might need administrator privileges, so pre-pend the word 'sudo' as needed)::

    python setup.py develop

#. Install optional dependencies using pip with the following commands (with administrator privileges)::

    pip install django  # (only needed if you want to use the built-in web frontend!)
    pip install paramiko  # (only needed if using built-in remote file transfer!)
    pip install fabric  # (only needed if using daemon mode of qlaunch!)
    pip install requests  # (only needed if you want to use the NEWT queue adapter!)

.. tip:: If you have an old version of these libraries installed, you might need to run ``pip install --upgrade <PACKAGE>``. In particular, ensure that Django is greater than v1.5.
    
Run unit tests
--------------
1. Staying in the directory containing setup.py, run the following command::

    python setup.py test
    
2. Ideally, a printout should indicate that all tests have passed. If not, you might try to debug based on the error indicated, or you can let us know the problem so we can improve the docs (see :ref:`contributing-label`).

.. _updating-label:

Updating an existing FireWorks installation
===========================================

If you want to update an existing FireWorks installation and used the simple pip install (Method 1), just run::

    pip install --upgrade FireWorks

If you installed FireWorks in developer mode:

#. Navigate inside your FireWorks source directory containing the file setup.py (you can type ``lpad version`` to tell you where this is).

#. Run the following commands::

    git pull
    
    python setup.py develop
    
    python setup.py test


.. note:: You can use the command ``python setup.py develop --user`` if you want to only install FireWorks for the local user