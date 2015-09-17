==============================
Contributing Code to FireWorks
==============================

FireWorks is an open-source codebase, and one if its advantages is the possibility for community contribution and improvement. If you are interested in contributing code to FireWorks, we'd be very happy to have you join the team! As a contributor, your code will be made available to the entire FireWorks community, and your name will be added to our :doc:`list of contributors </contributors>`.

We ask that all potential collaborators review our contribution criteria. You might also contact us directly at |Mail| to let us know what you're planning to contribute; we can discuss your plans and how to integrate your code for public release.

.. |Mail| image:: _static/mail.png
   :alt: developer contact
   :align: bottom

Criteria for Inclusion
======================

Our criteria for inclusion of your code depends on the type of contribution you plan to submit.

Adding new Queue Adapters, FireTasks, etc.
------------------------------------------

If you've written Queue Adapters, FireTasks, Duplicate Finders, or other "plug-in" type objects that do not modify existing code, we would be very happy to include them in the main repo. The main condition for inclusion is that they be useful to a broad section of the FireWorks community.

Adding new features or performance enhancements
-----------------------------------------------

We encourage you to submit new features and enhancements to the FireWorks code. That said, please be mindful that there exists a delicate balance between adding features and maintaining simplicity and usability.

We request that contributors begin by submitting the simplest version of their new feature or enhancement (hopefully about 500 lines of code or less). Simple codes are easy to use, flexible to adapt later, more durable against unforeseen errors, and easier to maintain and debug. More complex features should be built on top of the simplest version in a modular way. If your feature requires thousands of lines of code to be useful at all, you might re-evaluate your implementation.

Modifying core modules
----------------------

The core FireWorks modules are the most important of all, as they affect all users. One of our major goals is to keep the core of FireWorks lightweight, simple to use and understand, and difficult to "break". Proposed extensions or modifications to the core modules will therefore be evaluated quite strictly; they will be accepted only if they can be implemented very cleanly (i.e., generally in under 40 lines of code) and if they are of great interest to the majority of users.

Documentation, coding style, and tests
--------------------------------------

We ask for reasonably clear documentation of modules, classes, methods, and tricky code sections (hopefully not too many of the last item!) Where possible, code within a method or class should be easy to understand without the need for additional documentation. In some cases, we may request a tutorial to clarify usage of your code to the community. In terms of programming style, some guidelines are given in `PEP 8 <http://www.python.org/dev/peps/pep-0008/>`_, but we mainly ask that you try to follow the style of the FireWorks core modules. Depending on the complexity of the contribution, tests might need to be included along with your code.

However, when starting you should not be as concerned with these issues as with writing clear, succint, and functional code. If we feel that issues such as documentation or style are preventing merging of your code with the main repo, a core developer may request your permission to re-document and/or re-style your code, and add his/her name to either the ``__credits__`` or ``__authors__`` field of your code header (your name will still be retained in the ``__authors__`` field).

Licensing
---------

If you haven't already, please read the FireWorks :doc:`license <license>`. Your contributions will also be distributed under this license.

How to contribute
=================

If you're ready to contribute, awesome! The best way is to fork the FireWorks repo on Github and develop your feature independently in your own repository. Then, when you are ready to merge back, you can submit a merge request through Github.

Two great tutorials for how to do this are:

* The `Pymatgen Collaborative Workflow Guide <http://pymatgen.org/contributing.html>`_.
* (more detailed) The `Eqqon Collaborative Github Workflow <http://www.eqqon.com/index.php/Collaborative_Github_Workflow>`_.


If you encounter trouble, please let us know. We look forward to your merge request!




