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
* labels ([str]): list of labels, one for each file in the paths list.

Optional parameters
-------------------

* filepad_file (str): path to the filepad db config file
* compress (bool): whether or not to compress the file before inserting to gridfs
* metadata (dict): metadata to store along with the file, stored in 'metadata' key
* additional_data (dict): additional key: value pairs to be be added to the document

DeleteFilesTask
==============

The *DeleteFilesTask* lets you delete one or more files from the filepad.

Required parameters
-------------------

* labels: ([str]) file labels to delete

Optional parameters
-------------------

* filepad_file (str): path to the filepad db config file

