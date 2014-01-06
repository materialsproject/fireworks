import os
from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = 'Jan 6, 2014'


class FileWriterTask(FireTaskBase, FWSerializable):
    _fw_name = "File Writer Task"

    def __init__(self, parameters=None):
        """
        :param parameters: Optional dict parameters. The only supported one
        is "dest", which should point to the location where the files are to
        be written. If left blank, the current working directory is used.
        """
        if parameters is not None:
            self.update(parameters)

    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for d in fw_spec["input_files"]:
            with open(os.path.join(pth, d["filename"]), "w") as f:
                f.write(d["contents"])
