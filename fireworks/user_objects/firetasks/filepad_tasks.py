# coding: utf-8

from __future__ import unicode_literals

import os

from fireworks.core.firework import FiretaskBase
from fireworks.utilities.filepad import FilePad

__author__ = 'Kiran Mathew'
__email__ = 'kmathew@lbl.gov'
__credits__ = 'Anubhav Jain'


class AddFilesTask(FiretaskBase):
    """
    A Firetask to add files to the filepad.

    Required params:
        - paths (list/str): either list of paths or a glob pattern string.

    Optional params:
        - identifiers ([str]): list of identifiers, one for each file in the paths list
        - directory (str): path to directory where the pattern matching is to be done.
        - filepad_file (str): path to the filepad db config file
        - compress (bool): whether or not to compress the file before inserting to gridfs
        - metadata (dict): metadata to store along with the file, stored in 'metadata' key
    """
    _fw_name = 'AddFilesTask'
    required_params = ["paths"]
    optional_params = ["identifiers", "directory", "filepad_file", "compress", "metadata"]

    def run_task(self, fw_spec):

        from glob import glob

        directory = os.path.abspath(self.get("directory", "."))

        if isinstance(self["paths"], list):
            paths = [os.path.abspath(p) for p in self["paths"]]
        else:
            paths = [os.path.abspath(p) for p in glob("{}/{}".format(directory, self["paths"]))]

        # if not given, use the full paths as identifiers
        identifiers = self.get("identifiers", paths)

        assert len(paths) == len(identifiers)

        fpad = get_fpad(self.get("filepad_file", None))

        for p, l in zip(paths, identifiers):
            fpad.add_file(p, identifier=l, metadata=self.get("metadata", None),
                          compress=self.get("compress", True))


class GetFilesTask(FiretaskBase):
    """
    A Firetask to fetch files from the filepad and write it to specified directory(current working
    directory if not specified)

    Required params:
        - identifiers ([str]): identifiers of files to fetch

    Optional params:
        - filepad_file (str): path to the filepad db config file
        - dest_dir (str): destination directory, default is the current working directory
        - new_file_names ([str]): if provided, the retrieved files will be renamed
    """
    _fw_name = 'GetFilesTask'
    required_params = ["identifiers"]
    optional_params = ["filepad_file", "dest_dir", "new_file_names"]

    def run_task(self, fw_spec):
        fpad = get_fpad(self.get("filepad_file", None))
        dest_dir = self.get("dest_dir", os.path.abspath("."))
        new_file_names = self.get("new_file_names", [])
        for i, l in enumerate(self["identifiers"]):
            file_contents, doc = fpad.get_file(identifier=l)
            file_name = new_file_names[i] if new_file_names else doc["original_file_name"]
            with open(os.path.join(dest_dir, file_name), "w") as f:
                f.write(file_contents.decode())


class DeleteFilesTask(FiretaskBase):
    """
    A Firetask to delete files from the filepad

    Required params:
        - identifiers ([str]): identifiers of files to delete

    Optional params:
        - filepad_file (str): path to the filepad db config file
    """
    _fw_name = 'DeleteFilesTask'
    required_params = ["identifiers"]
    optional_params = ["filepad_file"]

    def run_task(self, fw_spec):
        fpad = get_fpad(self.get("filepad_file", None))
        for l in self["identifiers"]:
            fpad.delete_file(l)


def get_fpad(fpad_file):
    if fpad_file:
        return FilePad.from_db_file(fpad_file)
    else:
        return FilePad.auto_load()
