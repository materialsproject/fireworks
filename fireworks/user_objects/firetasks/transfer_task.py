"""
This module contains the TransferTask used to move and copy files. Remote transfer is also supported.
"""

import os
from os.path import expandvars, expanduser
import shutil
import traceback
from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain, David Waroquiers'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 29, 2013'

# TODO: write some unit tests - this is really an untested FireTask

class TransferTask(FireTaskBase, FWSerializable):
    _fw_name = "Transfer Task"

    def __init__(self, parameters):
        """
        :param parameters: (dict) parameters.
        """
        self.update(parameters)

        self.fn_list = {
            "move": shutil.move,
            "mv": shutil.move,
            "copy": shutil.copy,
            "cp": shutil.copy,
            "copy2": shutil.copy2,
            "copytree": shutil.copytree,
            "copyfile": shutil.copyfile,
        }

        if not parameters.get("use_global_spec"):
            self._load_parameters(parameters)

    def run_task(self, fw_spec):
        if self.get("use_global_spec"):
            self._load_parameters(fw_spec)

        shell_interpret = self.get('shell_interpret', True)
        ignore_errors = self.get('ignore_errors')
        mode = self.get('mode', 'move')

        if mode == 'rtransfer':
            # remote transfers
            # Create SFTP connection
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
            ssh.connect(self['server'], key_filename=self.get['key_filename'])
            sftp = ssh.open_sftp()

        for f in self.files:
            try:
                src = os.path.abspath(expanduser(expandvars(f['src']))) if shell_interpret else f['src']

                if mode == 'rtransfer':
                    dest = f['dest']
                    if os.path.isdir(src):
                        if not self._rexists(sftp, dest):
                            sftp.mkdir(dest)

                        for f in os.listdir(src):
                            if os.path.isfile(os.path.join(src,f)):
                                sftp.put(os.path.join(src, f), os.path.join(dest, f))
                    else:
                        sftp.put(src, dest)

                else:
                    dest = os.path.abspath(expanduser(expandvars(f['dest']))) if shell_interpret else f['dest']
                    self.fn_list[mode](src, dest)

            except:
                traceback.print_exc()
                if not ignore_errors:
                    raise ValueError(
                        "There was an error performing operation {} from {} to {}".format(mode, src,
                                                                                          dest))
        if mode == 'rtransfer':
            sftp.close()
            ssh.close()

    def _load_parameters(self, params):
        self.files = params['files']

    def _rexists(self, sftp, path):
        """
        os.path.exists for paramiko's SCP object
        """
        try:
            sftp.stat(path)
        except IOError, e:
            if e[0] == 2:
                return False
            raise
        else:
            return True