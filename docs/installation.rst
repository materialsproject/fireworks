Basic FireWorks installation
============================

*Currently, we suggest that you install FireWorks in developer mode using the instructions below rather than using pip or easy-install.*

Install required software
-------------------------
To prepare for installation, you should:

1. Install `git <http://git-scm.com>`_, if not already packaged with your system. This will allow you to download the latest source code.
2. Install `pip <http://www.pip-installer.org/en/latest/installing.html>`_, if not already packaged with your system. This will allow you to download required dependencies.

Download FireWorks and dependencies
-----------------------------------
1. Run the following code to download the FireWorks source::

    git clone git@github.com:materialsproject/fireworks.git

2. Navigate inside the FireWorks directory containing the file setup.py and run the following command (you might need administrator privileges, so pre-pend the word 'sudo' as needed)::

    python setup.py develop

3. Install the needed dependencies using pip with the following commands (with administrator privileges)::

    pip install nose
    pip install pyyaml
    pip install simplejson

Run unit tests
--------------
1. Staying in the directory containing setup.py, run the following command::

    nosetests
    
2. Ideally, a printout should indicate that all tests have passed. If not, you might try to debug based on the error indicated, or you can let us know the problem so we can improve the docs (see :ref:`contributing-label`).