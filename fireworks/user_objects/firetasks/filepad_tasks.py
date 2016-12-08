# coding: utf-8

from __future__ import unicode_literals

from fireworks.core.firework import FiretaskBase
from fireworks.utilities.filepad import FilePad

__author__ = 'Kiran Mathew'
__email__ = 'kmathew@lbl.gov'


class AddFilesTask(FiretaskBase):
    """
    A Firetask to write files to the filepad

    Required params:
        - paths ([str]): list of paths to files to be added
        - labels ([str]): list of labels, one for each file in the paths list

    Optional params:
        - filepad_file (str): path to the filepad db config file
        - compress (bool): whether or not to compress the file before inserting to gridfs
        - metadata (dict): metadata to store along with the file, stored in 'metadata' key
        - additional_data (dict): additional key: value pairs to be be added to the document
    """
    _fw_name = 'AddFilesTask'
    required_params = ["paths", "labels"]
    optional_params = ["filepad_file", "compress", "metadata", "additional_data"]

    def run_task(self, fw_spec):
        if len(self["paths"]) != len(self["labels"]):
            raise ValueError("number of paths not equal to number of labels")
        fpad = get_fpad(self.get("filepad_file", None))
        for p, l in zip(self["paths"], self["labels"]):
            fpad.add_file(p, label=l, metadata=self.get("metadata", None),
                          compress=self.get("compress", True),
                          additional_data=self.get("additional_data", None))


class DeleteFilesTask(FiretaskBase):
    """
    A Firetask to delete files from the filepad

    Required params:
        - labels: ([str]) file labels to delete

    Optional params:
        - filepad_file (str): path to the filepad db config file
    """
    _fw_name = 'DeleteFilesTask'
    required_params = ["labels"]
    optional_params = ["filepad_file"]

    def run_task(self, fw_spec):
        fpad = get_fpad(self.get("filepad_file", None))
        for l in self["labels"]:
            fpad.delete_file(l)


def get_fpad(fpad_file):
    if fpad_file:
        return FilePad.from_db_file(fpad_file)
    else:
        return FilePad.auto_load()