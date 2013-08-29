from os.path import expandvars, expanduser
import shutil

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 29, 2013'

"""
This module contains the MoverTask, which moves files and directories and supports remote file movement through SSH2 via paramiko
"""

from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 29, 2013'


class MoverTask(FireTaskBase, FWSerializable):
    _fw_name = "Mover Task"

    fn_list = {
        "move": shutil.move,
        "mv": shutil.move,
        "copy": shutil.copy,
        "cp": shutil.copy,
        "copy2": shutil.copy2,
        "copytree": shutil.copytree,
        "copyfile": shutil.copyfile,
    }

    def __init__(self, parameters):
        """
        :param parameters: (dict) parameters.
        """
        self.update(parameters)

        if not parameters.get("use_root"):
            self._load_parameters(parameters)

    def run_task(self, fw_spec):
        if self.get("use_root"):
            self._load_parameters(fw_spec)

        for f in self.files:
            o = self.options
            shell_interpret = o.get('shell_interpret', True)
            src = expanduser(expandvars(f['src'])) if shell_interpret else expandvars(f['src'])
            dest = expanduser(expandvars(f['dest'])) if shell_interpret else expandvars(f['dest'])
            ignore_errors = o.get('ignore_errors')
            mode = o.get('mode', 'move')

            try:
                self.fn_list[mode](src, dest)
            except:
                if not ignore_errors:
                    raise ValueError(
                        "There was an error performing operation {} from {} to {}".format(mode, src,
                                                                                          dest))

    def _load_parameters(self, params):
        self.options = params.get('options', {})
        self.files = params['files']
