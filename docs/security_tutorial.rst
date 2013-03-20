====================
Configuring Security
====================

The FireWorks tutorials so far have not configured any security on your LaunchPad. We strongly suggest that you password-protect your Mongo database. We'll walk you through this process in this tutorial.

There are several other actions you can take for added security, such as restricting the IPs that can connect to your Mongo instance. Additional details can be found in the `MongoDB official documentation <http://docs.mongodb.org/manual/administration/security/>`_.

Create a read and write user in the admin database
==================================================

On your FireServer (which hosts your Mongo database), you must set up at least one user for the admin database. Note that this involves a server restart, so you should not do this during production runs.

1. First, connect to your Mongo instance::

    mongo

    .. note:: If you are using a non-default port, make sure to specify it.

2. Connect to the admin database and add your user in the Mongo shell::

    use admin;
    db.addUser('write_user', 'my_password');
    db.shutdownServer();
    exit

3. Restart MongoDB, but use the ``--auth`` option to enable authentication::

    mongod --auth

    .. note:: If you are using the ``--dbpath`` option, make sure to set it.

Your admin user is now configured, and your Mongo instance is now protected from unauthorized access. Next we must set up your LaunchPad configuration file so that you can authenticate.

Add username and password keys to your LaunchPad file
=====================================================

Your LaunchPad file contains the location of the LaunchPad as well as any credentials needed to connect. To connect to an authenticated database::

1. Locate your ``my_launchpad.yaml`` file (perhaps from when you completed the :doc:`FireWorker tutorial <installation_tutorial_pt2>`). If you never created such a file, you can find a template called ``launchpad.yaml`` in ``<INSTALL_DIR>/fw_tutorials/installation_pt2``. You might copy it to ``my_launchpad.yaml`` and edit it as necessary.

2. Add your username and password to your launchpad file by adding the following lines::

    username: <your username, e.g. write_user>
    password: <your password, e.g. my_password>

3. **Make sure you put your LaunchPad file in a secure location with protected filesystem access.** It contains your password as plain text!

3. Whenever running any FireWork scripts, make sure to specify the ``-l`` option and link to your configuration file. For example::

    lpad -l my_launchpad.yaml get_fw_ids

   or::

    rlaunch -l my_launchpad.yaml singleshot

   .. note:: To save typing, you can set things up so that the ``-l`` option is automatically set to the correct value. For details, see the tutorial on managing configuration files.
