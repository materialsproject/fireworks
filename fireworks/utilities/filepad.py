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
                 password=None, filepad_coll="filepad", gridfs_collection="fpad_gfs", logdir=None,
                 strm_lvl=None):
        """
        Args:
            host (str): hostname
            port (int): port number
            database (str): database name
            username (str)
            password (str)
            filepad_coll (str): filepad collection name
            gridfs_collection (str): gridfs collection name
            logdir (str): path to the log directory
            strm_lvl (str): the logger stream level
        """
        self.host = host
        self.port = int(port)
        self.database = database
        self.username = username
        self.password = password
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
        self.filepad = self.db[filepad_coll]
        self.gridfs = gridfs.GridFS(self.db, gridfs_collection)

        # logging
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.logger = get_fw_logger('filepad', l_dir=self.logdir, stream_level=self.strm_lvl)

    def add_file(self, path, label=None, compress=True, metadata=None):
        """
        Insert the file specified by the path into gridfs. The id and label(if provided) are returned.
        Note: label must be unique i.e no insertion if the label already exists in the db.

        Args:
            path (str): path to the file
            label (str): file label
            compress (bool): compress or not
            metadata (dict): file metadata

        Returns:
            (str, str): the id returned by gridfs, label
        """
        # skip if the label exists
        if label is not None:
            file_contents, doc = self.get_file(label)
            if file_contents is not None and doc is not None:
                self.logger.warning("label: {} exists. Skipping insertion".format(label))
                return doc["file_id"], doc["label"]
        path = os.path.abspath(path)
        root_data = {"label": label,
                     "original_file_name": os.path.basename(path),
                     "original_file_path": path,
                     "metadata": metadata}
        with open(path, "r") as f:
            contents = f.read()
            return self._insert_contents(contents, label, root_data, compress)

    def get_file(self, label):
        """
        Get file by label.

        Args:
            label (str): the file label

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        doc = self.filepad.find_one({"label": label})
        return self._get_file_contents(doc)

    def delete_file(self, label):
        """
        Delete the document with the matching label. The contents in the gridfs as well as the
        associated document in the filepad are deleted.

        Args:
            label (str): the file label
        """
        doc = self.filepad.find_one({"label": label})
        if doc is None:
            self.logger.warning("The file doesn't exist")
        else:
            self.delete_file_by_id(doc["file_id"])

    def update_file(self, label, path, delete_old=False, compress=True):
        """
        Update the filecontents in the gridfs, update the file_id in the document and retain the
        rest.

        Args:
            label (str): the unique file label
            path (str): path to the new file whose contents will replace the existing one.
            delete_old (bool): if set to true, the old stufff from the gridfs will be deleted
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        doc = self.filepad.find_one({"label": label})
        return self._update_file_contents(doc, path, delete_old, compress)

    def _insert_contents(self, contents, label, root_data, compress):
        """
        Insert the file contents(string) to gridfs and store the file info doc in filepad

        Args:
            contents (str): file contents or any arbitrary string to be stored in gridfs
            label (str): file label
            compress (bool): compress or not
            root_data (dict): key:value pairs to be added to the document root

        Returns:
            (str, str): the id returned by gridfs, label
        """
        file_id = self._insert_to_gridfs(contents, compress)
        root_data["file_id"] = file_id
        self.filepad.insert_one(root_data)
        return file_id, label

    def _insert_to_gridfs(self, contents, compress):
        if compress:
            contents = zlib.compress(contents.encode(), compress)
        # insert to gridfs
        return str(self.gridfs.put(contents))

    def get_file_by_id(self, file_id):
        """
        Args:
            file_id (str): the file id

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        doc = self.filepad.find_one({"file_id": file_id})
        return self._get_file_contents(doc)

    def _get_file_contents(self, doc):
        """
        Args:
            doc (dict)

        Returns:
            (str, dict): the file content as a string, document dictionary
        """
        from bson.objectid import ObjectId

        if doc:
            gfs_id = doc['file_id']
            file_contents = zlib.decompress(self.gridfs.get(ObjectId(gfs_id)).read())
            return file_contents, doc
        else:
            return None, None

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

    def delete_file_by_id(self, file_id):
        """
        Args:
            file_id (str): the file id
        """
        self.gridfs.delete(file_id)
        self.filepad.delete_one({"file_id": file_id})

    def delete_file_by_query(self, query):
        """
        Args:
            query (dict): pymongo query dict
        """
        for d in self.filepad.find(query):
            self.delete_file_by_id(d["file_id"])

    def update_file_by_id(self, file_id, path, delete_old=False, compress=True):
        """
        Update the file in the gridfs with the given id and retain the rest of the document.

        Args:
            file_id (str): the file id
            path (str): path to the new file whose contents will replace the existing one.
            delete_old (bool): if set to true, the old stufff from the gridfs will be deleted
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        doc = self.filepad.find_one({"file_id": file_id})
        return self._update_file_contents(doc, path, delete_old, compress)

    def _update_file_contents(self, doc, path, delete_old, compress):
        """
        Args:
            doc (dict)
            path (str): path to the new file whose contents will replace the existing one.
            delete_old (bool): if set to true, the old stufff from the gridfs will be deleted
            compress (bool): whether or not to compress the contents before inserting to gridfs

        Returns:
            (str, str): old file id , new file id
        """
        if doc is None:
            return None, None
        old_file_id = doc["file_id"]
        if delete_old:
            self.gridfs.delete(old_file_id)
        file_id = self._insert_to_gridfs(open(path, "r").read(), compress)
        doc["file_id"] = file_id
        return old_file_id, file_id

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

        return cls(creds.get("host", "localhost"), int(creds.get("port", 27017)),
                   creds.get("name", "fireworks"), user, password, creds.get("filepad", "filepad"),
                   creds.get("filepad_gridfs", "fpad_gfs"))

    @classmethod
    def auto_load(cls):
        """
        Returns FilePad object
        """
        if LAUNCHPAD_LOC:
            return FilePad.from_db_file(LAUNCHPAD_LOC)
        return FilePad()
