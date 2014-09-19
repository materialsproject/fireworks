===============================
Using the built-in FileIO Tasks
===============================

FireWorks comes with several built-in tasks for performing file I/O (writing, moving, and deleting files).

FileWriteTask
==============

The *FileWriteTask* is a simple way to write files (a more powerful version based on templating is the :doc:`TemplateWriterTask </templatewritertask>`).

Required parameters
-------------------

* files_to_write: ([{filename:(str), contents:(str)}]) - this is a list of dictionaries. each dictionary must have a filename (string) and contents (str). The contents are written to the corresponding filename.

Optional parameters
-------------------

* dest: (str) - the directory in which to write all the files (default is current working directory)

FileDeleteTask
==============

The *FileDeleteTask* lets you delete one or more files.

Required parameters
-------------------

* files_to_delete: ([(str)]) - a list of Strings corresponding to the filenames to delete

Optional parameters
-------------------

* dest: (str) - the directory in which to delete all the files (default is current working directory)

FileTransferTask
================

The FileTransferTask is a built-in FireTask for moving and copying files, perhaps to a remote server. Its usage is straightforward:

* a ``files`` key that contains a list of files to move or copy
* additional options control how directory names are interpreted, how to perform the move/copy, and what to do in case of errors

An example of a Firework that copies two files, ``file1.txt`` and ``file2.txt``, to the home directory looks as follows::

    spec:
      _tasks:
      - _fw_name: FileTransferTask
        files:
        - src: file1.txt
          dest: ~/file1.txt
        - src: file2.txt
          dest: ~/file2.txt
        mode: copy

In Python code, the same task would be defined as::

    firetask1 = FileTransferTask({'files': [{'src': 'file1.txt', 'dest': '~/file1.txt'}, {'src': 'file2.txt', 'dest': '~/file2.txt'}], 'mode': 'copy'})

The ``files`` parameter *must* be specified, and is an array of dictionaries with ``src`` and ``dest`` keys. The default mode of operation is to move files from the source to destination; by changing the ``mode`` to copy, we will copy the files instead. Note that you can put as many files (or directories) in the ``files`` list as you want; the same ``mode`` will be applied to all of them. If you want to move some files and copy others, you'd need to include two different ``FileTransferTask``s in your Firework.

A more compact representation for File Transfers can be given if several files are being moved/copied to the same directory::

    spec:
      _tasks:
      - _fw_name: FileTransferTask
        dest: dest_dir
        files:
        - file1.txt
        - file2.txt
        mode: copy

In Python code, this representation would be defined as::

    firetask1 = FileTransferTask({'files': ['file1.txt', 'file2.txt'], 'dest':'dest_dir', 'mode': 'copy'})

An example of the FileTransferTask in action is given in the :doc:`FireTask tutorial <firetask_tutorial>`.

FileTransferTask Options
------------------------

Below are the various options that can be set for the FileTransferTask.

**mode**

The potential values are:

* *move* - move a file or directory
* *copy* - copy a file/dir (including permissions) but do not include metadata
* *copy2* - copy a file/dir (including permissions); also include metadata
* *copytree* - recursively copy an entire directory copy
* *copyfile* - copy the contents of a file into another file (no metadata)
* *rtransfer* - do a remote transfer (this is covered later in this doc)

.. note:: With the exception of **rtransfer**, ``FileTransferTask`` is using Python's *shutil* module to do the move/copy. You can read more about these modes in `Python's *shutil* docs <http://docs.python.org/2/library/shutil.html`_.

**ignore_errors**

Either *True* or *False* (default=*False*). If True, a failed move/copy will just cause ``FileTransferTask`` to move to the next file in the ``files`` list. If False, a failed move/copy will raise an error.

**shell_interpret**

Either *True* or *False* (default=*True*). If False, the *src* and *dest* of files are taken literally. If *True*, the *src* and *dest* interpret environment variables and shortcuts like ``~`` and ``.``

.. note:: In remote transfer mode, some shortcuts like ``.`` and ``~`` are not interpreted for the destination. However, environment variables will still be interpreted if ``shell_interpret`` is True.

Remote Transfers
----------------

Remote transfers are handled via SFTP using the *paramiko* Python library (make sure you've installed it via ``pip install paramiko``). To do a remote transfer, you set ``files`` as before but:

* You'll first need to configure passwordless login via ssh between the two machines that are transferring files
* Set the **mode** of transfer to *rtransfer* (see previous section)
* You *must* set an additional option called **server** to the remote server hostname or IP
* Make sure the *dest* doesn't contain symbols that can't properly be interpreted on the local machine, like ``~`` or ``.``
* If you are using a non-standard keyfile location (e.g., not something like ``~/.ssh/id_dsa.pub``), you need to set the **key_filename** option to the location of your key filename.

If all this is configured properly, you should be able to transfer files to a remote machine via ``FileTransferTask``. Some potential hiccups:

* You require a password to SSH between machines and haven't configured passwordless SSH.
* You are using a non-standard SSH port
* Your ``known_hosts`` file is not located in ``~/.ssh/known_hosts``

The _use_global_spec option
---------------------------

By default, the parameters for the FileTransferTask should be defined within the ``_task`` section of the **spec** corresponding to the FileTransferTask, not as a root key of the **spec**. If you'd like to instead specify the parameters in the root of the **spec**, you can set ``_use_global_spec`` to True within the ``_task`` section. Note that ``_use_global_spec`` can simplify querying and communication of parameters between FireWorks but can cause problems if you have multiple FileTransferTasks within the same Firework.


CompressDirTask
===============

The *CompressDir* task allows you to compress each file in the current directory (e.g., via gzip).

Required parameters
-------------------

(none)

Optional parameters
-------------------

* compression: (str) - choose between "gz" (default) and "bz2" compression modes
* dest: (str) - destination location
* ignore_errors: (bool) - whether to ignore errors

ArchiveDirTask
===============

The *ArchiveDir* task allows you to archive the current working directory into a single file.

Required parameters
-------------------

* base_name: (str) the full file path of the output archive file
* format: (str) "zip", "tar", "bztar" or "gztar"

Optional parameters
-------------------

* format: (str) - choose between "zip", "tar", "bztar" or "gztar" (default).

