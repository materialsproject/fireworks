import os

from fireworks.core.firework import FiretaskBase
from fireworks.utilities.filepad import FilePad

__author__ = "Kiran Mathew, Johannes Hoermann"
__email__ = "kmathew@lbl.gov, johannes.hoermann@imtek.uni-freiburg.de"
__credits__ = "Anubhav Jain"


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

    _fw_name = "AddFilesTask"
    required_params = ["paths"]
    optional_params = ["identifiers", "directory", "filepad_file", "compress", "metadata"]

    def run_task(self, fw_spec):

        from glob import glob

        directory = os.path.abspath(self.get("directory", "."))

        if isinstance(self["paths"], list):
            paths = [os.path.abspath(p) for p in self["paths"]]
        else:
            paths = [os.path.abspath(p) for p in glob(f"{directory}/{self['paths']}")]

        # if not given, use the full paths as identifiers
        identifiers = self.get("identifiers", paths)

        assert len(paths) == len(identifiers)

        fpad = get_fpad(self.get("filepad_file", None))

        for p, l in zip(paths, identifiers):
            fpad.add_file(p, identifier=l, metadata=self.get("metadata", None), compress=self.get("compress", True))


class GetFilesTask(FiretaskBase):
    """
    A Firetask to fetch files from the filepad and write it to specified directory (current working
    directory if not specified)

    Required params:
        - identifiers ([str]): identifiers of files to fetch

    Optional params:
        - filepad_file (str): path to the filepad db config file
        - dest_dir (str): destination directory, default is the current working directory
        - new_file_names ([str]): if provided, the retrieved files will be renamed
    """

    _fw_name = "GetFilesTask"
    required_params = ["identifiers"]
    optional_params = ["filepad_file", "dest_dir", "new_file_names"]

    def run_task(self, fw_spec):
        fpad = get_fpad(self.get("filepad_file", None))
        dest_dir = self.get("dest_dir", os.path.abspath("."))
        new_file_names = self.get("new_file_names", [])
        for i, l in enumerate(self["identifiers"]):
            file_contents, doc = fpad.get_file(identifier=l)
            file_name = new_file_names[i] if new_file_names else doc["original_file_name"]
            if fpad.text_mode:
                with open(os.path.join(dest_dir, file_name), "w") as f:
                    f.write(file_contents.decode())
            else:
                with open(os.path.join(dest_dir, file_name), "wb") as f:
                    f.write(file_contents)


class GetFilesByQueryTask(FiretaskBase):
    """
    A Firetask to query files from the filepad and write them to specified
    directory (current working directory if not specified).

    Required params:
        - query (dict): mongo db query identifying files to fetch.
          Same as within fireworks.utilities.dict_mods, use '->' in dict keys
          for querying nested documents, instead of MongoDB '.' (dot) separator.
          Do use '.' and NOT '->' within the 'sort_key' field.

    Optional params:
        - sort_key (str): sort key, don't sort per default
        - sort_direction (int): sort direction, default 'pymongo.DESCENDING'
        - limit (int): maximum number of files to write, default: no limit
        - fizzle_empty_result (bool): fizzle if no file found, default: True
        - fizzle_degenerate_file_name (bool): fizzle if more than one of the
          resulting files are to be written to the same local file (i.e. the
          filepad's 'original_file_name' entries overlap), default: True
        - filepad_file (str): path to the filepad db config file
        - dest_dir (str): destination directory, default is the current working
          directory.
        - new_file_names ([str]): if provided, the retrieved files will be
          renamed. Not recommended as order and number of queried files not fixed.
        - meta_file (bool): default: False. If True, then metadata of queried files written to
          a .yaml file of same name as file itself, suffixed by...
        - meta_file_suffix (str): if not None, metadata for each file is written
          to a YAML file of the same name, suffixed by this string.
          Default: ".meta.yaml"

    The options 'fizzle_degenerate_file_name', 'limit', 'sort_key', and
    'sort_direction' are all inntended to help dealing with the following
    special case: Querying by metadata leads to an a priori unknown
    number of files in the general case. Thus, it is advisable to either
    'limit' the number of files and/or avoid explicitly specifying a list
    of 'new_file_names'. In the latter case, files will be written to
    'dest_dir' using their 'original_file_name' recorded within the
    attached FilePad object. When more than one queried file share the same
    'original_file_name', the order of processing matters: subsequent files will
    overwrite their predecessor of same name. 'sort_key' and 'sort_direction'
    can help to assure deterministic behavior, e.g. by always processing newer
    files later.
    """

    _fw_name = "GetFilesByQueryTask"
    required_params = ["query"]
    optional_params = [
        "dest_dir",
        "filepad_file",
        "fizzle_degenerate_file_name",
        "fizzle_empty_result",
        "limit",
        "meta_file",
        "meta_file_suffix",
        "new_file_names",
        "sort_direction",
        "sort_key",
    ]

    def run_task(self, fw_spec):
        import json

        import pymongo
        from ruamel.yaml import YAML

        from fireworks.utilities.dict_mods import arrow_to_dot

        fpad = get_fpad(self.get("filepad_file", None))
        dest_dir = self.get("dest_dir", os.path.abspath("."))
        new_file_names = self.get("new_file_names", [])
        query = self.get("query", {})
        sort_key = self.get("sort_key", None)
        sort_direction = self.get("sort_direction", pymongo.DESCENDING)
        limit = self.get("limit", None)
        fizzle_empty_result = self.get("fizzle_empty_result", True)
        fizzle_degenerate_file_name = self.get("fizzle_degenerate_file_name", True)
        meta_file = self.get("meta_file", False)
        meta_file_suffix = self.get("meta_file_suffix", ".meta.yaml")

        assert isinstance(query, dict)
        query = arrow_to_dot(query)

        l = fpad.get_file_by_query(query, sort_key, sort_direction)
        assert isinstance(l, list)

        if fizzle_empty_result and (len(l) == 0):
            raise ValueError(f"Query yielded empty result! (query: {json.dumps(query):s})")

        unique_file_names = set()  # track all used file names
        for i, (file_contents, doc) in enumerate(l[:limit]):
            file_name = new_file_names[i] if new_file_names else doc["original_file_name"]
            if fizzle_degenerate_file_name and (file_name in unique_file_names):
                raise ValueError(
                    f"The local file name {file_name} is used a second time by result {i}/{len(l)}! "
                    f"(query: {json.dumps(query)})"
                )

            unique_file_names.add(file_name)
            with open(os.path.join(dest_dir, file_name), "wb") as f:
                f.write(file_contents)

            if meta_file:
                meta_file_name = file_name + meta_file_suffix
                with open(os.path.join(dest_dir, meta_file_name), "w") as f:
                    yaml = YAML()
                    yaml.dump(doc["metadata"], f)


class DeleteFilesTask(FiretaskBase):
    """
    A Firetask to delete files from the filepad

    Required params:
        - identifiers ([str]): identifiers of files to delete

    Optional params:
        - filepad_file (str): path to the filepad db config file
    """

    _fw_name = "DeleteFilesTask"
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
