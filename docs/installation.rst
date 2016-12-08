====================
Installing FireWorks
====================

.. note:: We suggest that you use Python 2.7.3 or higher, especially in production. There is a `bug <https://groups.google.com/forum/#!topic/modwsgi/DW-SlIb07rE>`_ in Python 2.7.2 that could affect FireWorks (although we haven't seen any problems yet). As of FireWorks v0.7, Python 3.3 and higher should also work.

Install MongoDB
===============

FireWorks requires a single MongoDB instance to store and access your workflows. You can either install MongoDB yourself and run/maintain the server, or use a cloud provider (which often provide for small amounts of data for free). For testing things out locally, running MongoDB yourself and on your local machine may be your best bet. For production, or for running on supercomputing centers on which you are unable to install MongoDB, you likely want to use a cloud service provider. You could also maintain your own MongoDB server or contact your sysadmin for help.

To install MongoDB *locally*, follow the instructions at `MongoDB <http://www.mongodb.org>`_.

To access via a *cloud provider*, you might try `Mongolab <http://www.mongolab.com>`_ or search for a different one. If you are using Mongolab, here are a few notes:

    * Set up an account via the Mongolab web site instructions. When asked to pick a server type (e.g. Amazon, Google, etc) you can just choose free option of 500MB. This is more than enough to get started.
    * Mongolab will ask you to create a database; any name is fine, but make sure you write down what it is.
    * After creating a database, note that you'll need to create at least one admin user in order to access the database.
    * You can test your database connection using MongoDB's built-in command line tools. Or, you can continue with FireWorks installation and subsequently the tutorials, which will test the database connnection as part of the procedure.

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
    pip install paramiko  # (only needed if using built-in remote file transfer!)
    pip install fabric  # (only needed if using daemon mode of qlaunch!)
    pip install requests  # (only needed if you want to use the NEWT queue adapter!)

   .. note:: If you are getting permissions error, you might include the ``--user`` option, i.e., ``pip install --user FireWorks``. Another option is invoking administrator access, e.g., ``sudo pip install FireWorks``.
   .. note:: If installation fails with a message like "error: can't copy 'XXXXX': doesn't exist or not a regular file", try updating pip via ``pip install --upgrade pip``.

#. Separately, you can download the Firework tutorial files if you plan on going through the tutorials. You can download these from the `FireWorks Github page <https://github.com/materialsproject/fireworks>`_. All you need is the ``fw_tutorial`` directory, but it might be easiest to download the entire source and just copy the ``fw_tutorial`` directory somewhere else.

#. If you want, you can test connection to a remote server (see instructions below)

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

    pip install paramiko  # (only needed if using built-in remote file transfer!)
    pip install fabric  # (only needed if using daemon mode of qlaunch!)
    pip install requests  # (only needed if you want to use the NEWT queue adapter!)
    
Run unit tests
--------------
1. Staying in the directory containing setup.py, run the following command::

    python setup.py test
    
2. Ideally, a printout should indicate that all tests have passed. If not, you might try to debug based on the error indicated, or you can let us know the problem so we can improve the docs (see :ref:`contributing-label`).

.. _remote_test-label:

3. If you want, you can test connection to a remote server (see instructions below)

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

Testing connection to a remote server
=====================================
We've set up a test database to see if you can connect to it.

1. Create a file called ``my_launchpad_testing.yaml`` and put the following contents inside::

    host: ds049170.mongolab.com
    port: 49170
    name: fireworks
    username: test_user
    password: testing123

2. Execute the command::

    lpad -l my_launchpad_testing.yaml get_wflows

3. If successful, you should see a couple of results::

    [
        {
            "name": "Tracker FW--1",
            "state": "READY",
            "states_list": "REA",
            "created_on": "2014-10-27T15:00:25.408000"
        },
        {
            "name": "Tracker FW--2",
            "state": "READY",
            "states_list": "REA",
            "created_on": "2014-10-27T15:00:25.775000"
        }
    ]

Note that this is a read-only testing database. You can't run, add, or modify workflows - you'll only be able to do that on your own MongoDB setup.

.. _updating-label: