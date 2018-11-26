===============================
Using the built-in FilePad Tasks
===============================

FireWorks comes with several built-in tasks for performing file I/O (writing, moving, and deleting files).

AddFilesTask
==============

The *AddFilesTask* enables one to insert one or more files into MongoDb/GridFS using FilePad(see the documentation for FilePad :doc:`FilePad tutorial <filepad_tutorial>`.)

Required parameters
-------------------

* paths ([str]): list of paths to files to be added

Optional parameters
-------------------

* identifiers ([str]): list of identifiers, one for each file in the paths list.
* filepad_file (str): path to the filepad db config file
* compress (bool): whether or not to compress the file before inserting to gridfs
* metadata (dict): metadata to store along with the file, stored in 'metadata' key

GetFilesTask
==============

The *GetFilesTask* enables one to fetch one or more files into MongoDb/GridFS using FilePad and write
them to the given destination directory.

Required parameters
-------------------

* identifiers ([str]): list of identifiers, one for each file in the paths list.

Optional parameters
-------------------

* filepad_file (str): path to the filepad db config file.
* dest_dir (str): destination directory, default is the current working directory.
* new_file_names ([str]): if provided, the retrieved files will be renamed.

DeleteFilesTask
==============

The *DeleteFilesTask* lets you delete one or more files from the filepad.

Required parameters
-------------------

* identifiers: ([str]) file identifiers to delete

Optional parameters
-------------------

* filepad_file (str): path to the filepad db config file

