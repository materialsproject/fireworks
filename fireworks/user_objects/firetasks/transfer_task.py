"""
This module contains the TransferTask used to move and copy files. Remote transfer is also supported.
"""

import os
from os.path import expandvars, expanduser
import shutil
import traceback
import paramiko
from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain, David Waroquiers'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 29, 2013'


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
            "rtransfer": self._remotetransfer
        }

        if not parameters.get("use_root"):
            self._load_parameters(parameters)

    def run_task(self, fw_spec):
        if self.get("use_root"):
            self._load_parameters(fw_spec)

        o = self.options

        if o.get('mode') == 'rtransfer':
            # remote transfers
            pass

        else:
            # local transfers
            for f in self.files:
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

    def _rexists(sftp, path):
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

    def _remotetransfer(self, src, dest, o):
        # Connecting to the server
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(o['server'], username=o['username'], port=o['port'], key_filename=o['key_filename'])

        # Create SFTP connection
        sftp = ssh.open_sftp()

        # Local and remote directories
        try:
            # Transfer files from local directory to remote directory
            if not self._rexists(sftp, dest):
                sftp.mkdir(dest)

            sftp.put(src, dest)

        except:
            traceback.print_exc()
            raise ValueError('Error during remote transfer from {} to {} on server {} '.format(src, dest, o['server']))

        finally:
            # Close the connections
            sftp.close()
            ssh.close()