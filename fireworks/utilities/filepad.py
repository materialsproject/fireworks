# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

"""
This module defines the FilePad class. FilePad is a convenient api to mongodb/gridfs to
add/delete/update any file of any size.
"""

import zlib
import os

from pymongo import MongoClient
import gridfs

from monty.serialization import loadfn
from monty.json import MSONable

from fireworks.fw_config import LAUNCHPAD_LOC
from fireworks.utilities.fw_utilities import get_fw_logger


__author__ = 'Kiran Mathew'
__email__ = 'kmathew@lbl.gov'
__credits__ = 'Anubhav Jain'


class FilePad(MSONable):

    def __init__(self, host='localhost', port=27017, database='fireworks', username=None,
                 password=None, filepad_coll_name="filepad", gridfs_coll_name="filepad_gfs", logdir=None,
                 strm_lvl=None):
        """
        Args:
            host (str): hostname
            port (int): port number
            database (str): database name
            username (str)
            password (str)
            filepad_coll_name (str): filepad collection name
            gridfs_coll_name (str): gridfs collection name
            logdir (str): path to the log directory
            strm_lvl (str): the logger stream level
        """
        self.host = host
        self.port = int(port)
        self.database = database
        self.username = username
        self.password = password
        self.gridfs_coll_name = gridfs_coll_name
        try:
            self.connection = MongoClient(self.host, self.port)
            self.db = self.connection[database]
        except:
            raise Exception("connection failed")
        try:
            if self.username:
                self.db.authenticate(self.username, self.password)
        except:
            raise Exception("authentication failed")

        # set collections: filepad and gridfs
        self.filepad = self.db[filepad_coll_name]
        self.gridfs = gridfs.GridFS(self.db, gridfs_coll_name)

        # logging
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.logger = get_fw_logger('filepad', l_dir=self.logdir, stream_level=self.strm_lvl)

        # build indexes
        self.build_indexes()

    def build_indexes(self, indexes=None, background=True):
        """
        Build the indexes.

        Args:
            indexes (list): list of single field indexes to be built.
            background (bool): Run in the background or not.
        """
        indexes = indexes if indexes else ["identifier", "gfs_id"]
        for i in indexes:
            self.filepad.create_index(i, unique=True, background=background)

    def add_file(self, path, identifier=None, compress=True, metadata=None):
        """
        Insert the file specified by the path into gridfs. The gridfs id and identifier are returned.
        Note: identifier must be unique, i.e, no insertion if the identifier already exists in the db.

        Args:
            path (str): path to the file
            identifier (str): file identifier. If identifier = None then the identifier is set to the object id
                returned by gridfs insertion.
            compress (bool): compress or not
            metadata (dict): file metadata

        Returns:
            (str, str): the id returned by gridfs, identifier
        """
        if identifier is not None:
            _, doc = self.get_file(identifier)
            if doc is not None:
                self.logger.warning("identifier: {} exists. Skipping insertion".format(identifier))
                return doc["gfs_id"], doc["identifier"]

        path = os.path.abspath(path)
        root_data = {"identifier": identifier,
                     "original_file_name": os.path.basename(path),
                     "original_file_path": path,
                     "metadata": metadata,
                     "compressed": compress}
        with open(path, "r") as f:
            contents = f.read()
            return self._insert_contents(contents, identifier, root_data, compress)

    def get_file(self, identifier):
        """
        Get file by identifier

        Args:
            identifier (str): the file identifier

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        doc = self.filepad.find_one({"identifier": identifier})
        return self._get_file_contents(doc)

    def get_file_by_id(self, gfs_id):
        """
        Args:
            gfs_id (str): the gridfs id for the file.

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        doc = self.filepad.find_one({"gfs_id": gfs_id})
        return self._get_file_contents(doc)

    def get_file_by_query(self, query):
        """

        Args:
            query (dict): pymongo query dict

        Returns:
            list: list of all (file content as a string, document dictionary)
        """
        all_files = []
        for d in self.filepad.find(query):
            all_files.append(self._get_file_contents(d))
        return all_files

    def delete_file(self, identifier):
        """
        Delete the document with the matching identifier. The contents in the gridfs as well as the
        associated document in the filepad are deleted.

        Args:
            identifier (str): the file identifier
        """
        doc = self.filepad.find_one({"identifier": identifier})
        if doc is None:
            self.logger.warning("The file doesn't exist")
        else:
            self.delete_file_by_id(doc["gfs_id"])

    def update_file(self, identifier, path, compress=True):
        """
        Update the filecontents in the gridfs, update the gfs_id in the document and retain the
        rest.

        Args:
            identifier (str): the unique file identifier
            path (str): path to the new file whose contents will replace the existing one.
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        doc = self.filepad.find_one({"identifier": identifier})
        return self._update_file_contents(doc, path, compress)

    def delete_file_by_id(self, gfs_id):
        """
        Args:
            gfs_id (str): the file id
        """
        self.gridfs.delete(gfs_id)
        self.filepad.delete_one({"gfs_id": gfs_id})

    def delete_file_by_query(self, query):
        """
        Args:
            query (dict): pymongo query dict
        """
        for d in self.filepad.find(query):
            self.delete_file_by_id(d["gfs_id"])

    def update_file_by_id(self, gfs_id, path, compress=True):
        """
        Update the file in the gridfs with the given id and retain the rest of the document.

        Args:
            gfs_id (str): the gridfs id for the file.
            path (str): path to the new file whose contents will replace the existing one.
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        doc = self.filepad.find_one({"gfs_id": gfs_id})
        return self._update_file_contents(doc, path, compress)

    def _insert_contents(self, contents, identifier, root_data, compress):
        """
        Insert the file contents(string) to gridfs and store the file info doc in filepad

        Args:
            contents (str): file contents or any arbitrary string to be stored in gridfs
            identifier (str): file identifier
            compress (bool): compress or not
            root_data (dict): key:value pairs to be added to the document root

        Returns:
            (str, str): the id returned by gridfs, identifier
        """
        gfs_id = self._insert_to_gridfs(contents, compress)
        identifier = identifier or gfs_id
        root_data["gfs_id"] = gfs_id
        self.filepad.insert_one(root_data)
        return gfs_id, identifier

    def _insert_to_gridfs(self, contents, compress):
        if compress:
            contents = zlib.compress(contents.encode(), compress)
        # insert to gridfs
        return str(self.gridfs.put(contents))

    def _get_file_contents(self, doc):
        """
        Args:
            doc (dict)

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        from bson.objectid import ObjectId

        if doc:
            gfs_id = doc['gfs_id']
            file_contents = self.gridfs.get(ObjectId(gfs_id)).read()
            if doc["compressed"]:
                file_contents = zlib.decompress(file_contents)
            return file_contents, doc
        else:
            return None, None

    def _update_file_contents(self, doc, path, compress):
        """
        Args:
            doc (dict)
            path (str): path to the new file whose contents will replace the existing one.
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        if doc is None:
            return None, None
        old_gfs_id = doc["gfs_id"]
        self.gridfs.delete(old_gfs_id)
        gfs_id = self._insert_to_gridfs(open(path, "r").read(), compress)
        doc["gfs_id"] = gfs_id
        doc["compressed"] = compress
        return old_gfs_id, gfs_id

    @classmethod
    def from_db_file(cls, db_file, admin=True):
        """
        Args:
            db_file (str): path to the filepad cred file

        Returns:
            FilePad object
        """
        creds = loadfn(db_file)

        if admin:
            user = creds.get("admin_user")
            password = creds.get("admin_password")
        else:
            user = creds.get("readonly_user")
            password = creds.get("readonly_password")

        coll_name = creds.get("filepad", "filepad")
        gfs_name = creds.get("filepad_gridfs", "filepad_gfs")

        return cls(creds.get("host", "localhost"), int(creds.get("port", 27017)),
                   creds.get("name", "fireworks"), user, password, coll_name,
                   gfs_name)

    @classmethod
    def auto_load(cls):
        """
        Returns FilePad object
        """
        if LAUNCHPAD_LOC:
            return FilePad.from_db_file(LAUNCHPAD_LOC)
        return FilePad()

    def reset(self):
        """
        Reset filepad and the gridfs collections
        """
        self.filepad.delete_many({})
        self.db[self.gridfs_coll_name].files.delete_many({})
        self.db[self.gridfs_coll_name].chunks.delete_many({})
        self.build_indexes()

    def count(self, filter=None, **kwargs):
        """
        Get the number of documents in filepad.

        Args:
            filter (dict)
            kwargs (dict): see pymongo.Collection.count for the supported
                keyword arguments.

        Returns:
            int: the count
        """
        return self.filepad.count(filter, **kwargs)
