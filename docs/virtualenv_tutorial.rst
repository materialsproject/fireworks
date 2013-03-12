=======================
Virtualenv installation
=======================

In this tutorial, we'll cover just the basics of setting up a *virtualenv* for your FireWorks installation. Using virtualenv you to isolate your FireWorks installation from your other Python installations. This is often done when there are conflicts (e.g., two codes require different versions of Python), and sometimes done just for cleanliness.

Introduction to virtualenv
==========================

Your virtualenv is stored inside a user-specified directory on your system. That directory will contain the Python 2.7.3 executable as well as all dependencies for the FireWorks code. When you activate your virtualenv, your "normal" Python executable will be bypassed in favor of the one in this directory. In addition, your normal *site packages* directory containing your external Python libraries will be bypassed in favor of the one in your virtualenv. When you deactivate your virtualenv, things will return back to their usual state.