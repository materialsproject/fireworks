===============================================
Using FilePad for storing and retrieving files
===============================================


FilePad utility provides the api to add and delete arbitrary files of arbitray sizes to MongoDB(filepad).
The is achieved by inserting the entire file contents to GridFS and storing the id returned by the
GridFS insertion, the user provided identifier and the metadata in a document in the filepad. In the following
documentation, ``file contents`` refers to the file contents stored in GridFS and ``document`` refers to the
associated mongodb document that stores the ``file_id``, ``identifier`` and other miscellaneous information
pertaining to the file.

Adding files
==============

Create a FilePad object::

    fp = FilePad.from_db_file(<PATH_TO_DB_FILE>)

or:

    fp = FilePad.auto_load()  # if you have your configuration file paths set up for automatic loading

The db file needs to contain ``username`` and ``password`` keys. You should be able to reuse your existing ``my_launchpad.yaml`` file for this purpose.

To add a file::

    file_id, identifier = fp.add_file(<path>, <identifier>, compress=True/False, metadata=<metadata>)

where ``<path>`` is a string path to the file to be inserted, ``<identifier>`` is some
unique identifier that can be used to retrieve the file, the 'compress' argument value tells whether or not to compress
the file contents before insertion, ``<metadata>`` is a python dictionary input that will stored in the key 'metadata'.
A bare minimum document in the filepad database consists of keys ``file_id``(used
to store the string representation of the object id returned by GridFS), ``identifier``(used to store the
user assigned identifier for the file), ``original_file_name`` , ``original_file_path`` and ``metadata``.
On successful insertion the ``file_id`` and the ``identifier`` are returned.

Retrieving files
=================

Retrieve file contents and the associated document by the identifier::

    file_contents, doc = fp.get_file(<identifier>)

where the returned values ``file_contents`` and ``doc`` are the contents of the file with identifier ``<identifier>``
and the document attached to it respectively. Note that if you had set the ``compress`` option to True when
inserting the file, it will automatically be decompressed at this stage so that you will retrieve the
original file contents as expected.

Retrieve file contents and the associated document by the file id::

    file_contents, doc = fp.get_file_by_id(<file_id>)

where ``<file_id>`` is the file id associated with the file(the id returned during insertion)

Retrieve all the file contents and the associated documents by a general mongo query::

    all_files = fp.get_file_by_query(<query>)

where ``<query>`` is monogo query dict and the returned values ``all_files`` is a list of ``(file_contents, doc)``
tuples that match the query.


Deleting files
=================

To delete the contents of the file and the associated document by identifier::

    fp.delete_file(<identifier>)

To delete the file contents and the associated document by the file id::

    fp.delete_file_by_id(<file id>)

To delete all the file contents and the associated documents by a general mongo query::

    fp.delete_file_by_query(<query>)


