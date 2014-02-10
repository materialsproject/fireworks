import os
import shutil
import traceback

from os.path import expandvars, expanduser, abspath
from fireworks.core.firework import FireTaskBase

__author__ = 'Anubhav Jain, David Waroquiers, Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = 'Jan 6, 2014'


class FileWriteTask(FireTaskBase):
    """
    A FireTask to write files:
    Required params:
        - files_to_write: ([{filename:(str), contents:(str)}]) List of dicts with filenames and contents
    Optional params:
        - dest: (str) Shared path for files
    """
    _fw_name = 'FileWriteTask'
    required_params = ["files_to_write"]

    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for d in self["files_to_write"]:
            with open(os.path.join(pth, d["filename"]), "w") as f:
                f.write(d["contents"])


class FileDeleteTask(FireTaskBase):
    """
    A FireTask to delete files:
    Required params:
        - files_to_delete: ([str]) Filenames to delete
    Optional params:
        - dest: (str) Shared path for files
    """
    _fw_name = 'FileDeleteTask'
    required_params = ["files_to_delete"]


    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for f in self["files_to_delete"]:
            os.remove(os.path.join(pth, f))


class FileTransferTask(FireTaskBase):
    """
    A FireTask to Transfer files. Note that
    Required params:
        - mode: (str) - move, mv, copy, cp, copy2, copytree, copyfile, rtransfer
        - files: ([str]) or ([(str, str)]) - list of source files, or dictionary containing 'src' and 'dest' keys
        - dest: (str) destination directory, if not specified within files parameter
    Optional params:
        - server: (str) server host for remote transfer
        - key_filename: (str) optional SSH key location for remote transfer
    """
    _fw_name = 'FileTransferTask'
    required_params = ["mode", "files"]

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
                if 'src' in f:
                    src = os.path.abspath(expanduser(expandvars(f['src']))) if shell_interpret \
                        else f['src']
                else:
                    src = abspath(expanduser(expandvars(f))) if shell_interpret else f

                if mode == 'rtransfer':
                    dest = self['dest']
                    if os.path.isdir(src):
                        if not self._rexists(sftp, dest):
                            sftp.mkdir(dest)

                        for f in os.listdir(src):
                            if os.path.isfile(os.path.join(src,f)):
                                sftp.put(os.path.join(src, f), os.path.join(dest, f))
                    else:
                        sftp.put(src, dest)

                else:
                    if 'dest' in f:
                        dest = abspath(expanduser(expandvars(f['dest']))) if shell_interpret \
                            else f['dest']
                    else:
                        dest = abspath(expanduser(expandvars(self['dest']))) if shell_interpret \
                            else self['dest']
                    FileTransferTask.fn_list[mode](src, dest)

            except:
                traceback.print_exc()
                if not ignore_errors:
                    raise ValueError(
                        "There was an error performing operation {} from {} "
                        "to {}".format(mode, self["files"], self["dest"]))
        if mode == 'rtransfer':
            sftp.close()
            ssh.close()

    def _rexists(self, sftp, path):
        """
        os.path.exists for paramiko's SCP object
        """
        try:
            sftp.stat(path)
        except IOError as e:
            if e[0] == 2:
                return False
            raise
        else:
            return True
