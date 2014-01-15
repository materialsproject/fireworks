import os
import shutil
import traceback

from os.path import expandvars, expanduser, abspath
from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain, David Waroquiers, Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = 'Jan 6, 2014'


class FileWriteTask(FireTaskBase, FWSerializable):
    """
    A FireTask to write files:
    Required params:
        - files_to_write: ([{filename:(str), contents:(str)}]) List of dicts with filenames and contents
    Optional params:
        - dest: (str) Shared path for files
    """
    required_params = ["files_to_write"]

    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for d in self["files_to_write"]:
            with open(os.path.join(pth, d["filename"]), "w") as f:
                f.write(d["contents"])


class FileDeleteTask(FireTaskBase, FWSerializable):
    """
    A FireTask to delete files:
    Required params:
        - files_to_delete: ([str]) Filenames to delete
    Optional params:
        - dest: (str) Shared path for files
    """
    required_params = ["files_to_delete"]


    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for f in self["files_to_delete"]:
            os.remove(os.path.join(pth, f))


class FileTransferTask(FireTaskBase, FWSerializable):
    """
    A FireTask to Transfer files:
    Required params:
        - mode: (str) - move, mv, copy, cp, copy2, copytree, copyfile, rtransfer
        - files: ([str]) - source files
        - dest: (str) destination directory
    Optional params:
        - server: (str) server host for remote transfer
        - key_filename: (str) optional SSH key location for remote transfer
    """
    required_params = ["mode", "files", "dest"]

    fn_list = {
            "move": shutil.move,
            "mv": shutil.move,
            "copy": shutil.copy,
            "cp": shutil.copy,
            "copy2": shutil.copy2,
            "copytree": shutil.copytree,
            "copyfile": shutil.copyfile,
    }

    def run_task(self, fw_spec):
        shell_interpret = self.get('shell_interpret', True)
        ignore_errors = self.get('ignore_errors')
        mode = self.get('mode', 'move')

        if mode == 'rtransfer':
            # remote transfers
            # Create SFTP connection
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.load_host_keys(expanduser(os.path.join("~", ".ssh", "known_hosts")))
            ssh.connect(self['server'], key_filename=self.get['key_filename'])
            sftp = ssh.open_sftp()

        for f in self["files"]:
            try:
                src = abspath(expanduser(expandvars(f['src']))) if shell_interpret else f['src']

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
                    dest = abspath(expanduser(expandvars(f['dest']))) if shell_interpret else f['dest']
                    FileTransferTask.fn_list[mode](src, dest)

            except:
                traceback.print_exc()
                if not ignore_errors:
                    raise ValueError(
                        "There was an error performing operation {} from {} "
                        "to {}".format(mode, src, dest))
        if mode == 'rtransfer':
            sftp.close()
            ssh.close()

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
