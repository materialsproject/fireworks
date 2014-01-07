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
    _fw_name = "File Write Task"

    def __init__(self, parameters):
        """
        :param parameters: dict parameters. Required one is "files_to_write",
        which itself should be a list of dict, with [{"filename": "myfile",
        "contents": "hello\nworld"}, ...]. Optional is "dest", which should
        point to the location where the files are to be written. If left
        blank, the current working directory is used.
        """
        if parameters is not None:
            self.update(parameters)

    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for d in self["files_to_write"]:
            with open(os.path.join(pth, d["filename"]), "w") as f:
                f.write(d["contents"])


class FileDeleteTask(FireTaskBase, FWSerializable):
    _fw_name = "File Delete Task"

    def __init__(self, parameters=None):
        """
        :param parameters: Optional dict parameters. Required one is
        "files_to_delete", which itself should be a list of filenames.
        Optional is "dest", which should point to the location where the
        files are to be written. If left blank, the current working directory is used.
        """
        if parameters is not None:
            self.update(parameters)

    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        for f in self["files_to_delete"]:
            os.remove(os.path.join(pth, f))


class FileTransferTask(FireTaskBase, FWSerializable):
    # TODO: Need seriously better doc and unittests. No one knows
    # what parameters are supported here!

    _fw_name = "File Transfer Task"

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
            ssh.load_host_keys(expanduser(os.path.join("~", ".ssh", "known_hosts")))
            ssh.connect(self['server'], key_filename=self.get['key_filename'])
            sftp = ssh.open_sftp()

        for f in self.files:
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
                    self.fn_list[mode](src, dest)

            except:
                traceback.print_exc()
                if not ignore_errors:
                    raise ValueError(
                        "There was an error performing operation {} from {} "
                        "to {}".format(mode, src, dest))
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
