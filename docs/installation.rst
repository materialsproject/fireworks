============================
Basic FireWorks installation
============================

*Currently, we suggest that you install FireWorks in developer mode using the instructions below rather than using pip or easy-install.*

Preparing to Install
====================
To prepare for installation, you should:

1. Install `python 2.7 <http://www.python.org>`_ (preferably Python 2.7.3), if not already packaged with your system. To check your python version, use the command ``python --version``.
2. Install `git <http://git-scm.com>`_, if not already packaged with your system. This will allow you to download the latest source code.
3. Install `pip <http://www.pip-installer.org/en/latest/installing.html>`_, if not already packaged with your system. This will allow you to download required dependencies.

.. tip:: if you have easy_install configured, e.g. through `setuptools <http://pypi.python.org/pypi/setuptools>`_, you should be able to install pip using the command ``easy_install pip``.

Virtualenv installation option
------------------------------

Virtualenv is a tool that allows you to separate your FireWorks installation from your other Python installations. For example, you might want to use Python 2.7 for FireWorks, but Python 3+ for other Python codes you're interested in using. Or, you might have different versions of Python libraries supporting FireWorks and your other installations. This is often the case on shared machinesp. if you're interested in this option, you might consider a :doc:`virtualenv install </virtualenv_tutorial>`. Otherwise, just follow the installation tutorial below.

Download FireWorks and dependencies
===================================
1. Run the following code to download the FireWorks source::

    git clone git@github.com:materialsproject/fireworks.git

   .. note:: Make sure you have an account on GitHub set up, and have associated your SSH key on your computer with your GitHub account. Otherwise you might get a cryptic ``Permission denied (publickey)`` error.

2. Navigate inside the FireWorks directory containing the file setup.py::

    cd fireworks

3. Install the needed dependencies using pip with the following commands (with administrator privileges)::

    pip install nose
    pip install pyyaml
    pip install pymongo

.. tip:: If you have an old version of these libraries installed, you might need to run ``pip install --upgrade <PACKAGE>``. In particular, ensure that pymongo is >= 2.4.2 and includes MongoClient.

4. Run the following command (you might need administrator privileges, so pre-pend the word 'sudo' as needed)::

    python setup.py develop
    
Run unit tests
==============
1. Staying in the directory containing setup.py, run the following command::

    nosetests
    
2. Ideally, a printout should indicate that all tests have passed. If not, you might try to debug based on the error indicated, or you can let us know the problem so we can improve the docs (see :ref:`contributing-label`).

.. _updating-label:

Updating an existing FireWorks installation
===========================================

If you want to update an existing FireWorks installation, use the following steps:

1. Navigate inside your FireWorks source directory containing the file setup.py.

2. Run the following commands::

    git pull
    
    python setup.py develop
    
    nosetests
