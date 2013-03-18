====================
Configuring Security
====================

The FireWorks tutorials so far have not configured any security on your LaunchPad. Anyone that knows the location of your database could in theory connect to it and modify its contents. The first step to securing your database, which we strongly suggest, is password-protecting your Mongo database. We'll walk you through this process in this tutorial.

There are several other actions you can take, such as restricting the IPs that can connect to your Mongo instance. Additional details can be found in the `MongoDB official documentation <http://docs.mongodb.org/manual/administration/security/>`_.

Step 1. Add a write user to your Mongo instance
===============================================





