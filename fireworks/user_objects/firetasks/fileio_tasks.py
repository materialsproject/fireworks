# coding: utf-8

from __future__ import unicode_literals

import os
import shutil
import traceback

from os.path import expandvars, expanduser, abspath

import time

from fireworks.core.firework import FireTaskBase
from monty.shutil import compress_dir, decompress_dir

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
        - ignore_errors (bool): Whether to ignore errors. Defaults to True.
    """
    _fw_name = 'FileDeleteTask'
    required_params = ["files_to_delete"]


    def run_task(self, fw_spec):
        pth = self.get("dest", os.getcwd())
        ignore_errors = self.get('ignore_errors', True)
        for f in self["files_to_delete"]:
            try:
                os.remove(os.path.join(pth, f))
            except Exception as ex:
                if not ignore_errors:
                    raise OSError(str(ex))


class FileTransferTask(FireTaskBase):
    """
    A FireTask to Transfer files. Note that
    Required params:
        - mode: (str) - move, mv, copy, cp, copy2, copytree, copyfile, rtransfer
        - files: ([str]) or ([(str, str)]) - list of source files, or dictionary containing 'src' and 'dest' keys
        - dest: (str) destination directory, if not specified within files parameter
    Optional params:
        - server: (str) server host for remote transfer
        - user: (str) user to authenticate with on remote server
        - key_filename: (str) optional SSH key location for remote transfer
        - max_retry: (int) number of times to retry failed transfers; defaults to `0` (no retries)
        - retry_delay: (int) number of seconds to wait between retries; defaults to `10`
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
        max_retry = self.get('max_retry', 0)
        retry_delay = self.get('retry_delay', 10)
        mode = self.get('mode', 'move')

        if mode == 'rtransfer':
            # remote transfers
            # Create SFTP connection
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.load_host_keys(expanduser(os.path.join("~", ".ssh", "known_hosts")))
            ssh.connect(self['server'], username=self.get('user'), key_filename=self.get('key_filename'))
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
                        if not self._rexists(sftp, dest):
                            sftp.mkdir(dest)

                        sftp.put(src, os.path.join(dest, os.path.basename(src)))

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
                if max_retry:

                    # we want to avoid hammering either the local or remote machine
                    time.sleep(retry_delay)
                    self['max_retry'] -= 1
                    self.run_task(fw_spec)

                elif not ignore_errors:
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


class CompressDirTask(FireTaskBase):
    """
    Compress all files in a directory.

    Args:
        dest (str): Optional. Path to compress.
        compression (str): Optional. Can only be gz or bz2. Defaults to gz.
        ignore_errors (bool): Optional. Whether to ignore errors. Defaults to
            False.
    """

    _fw_name = 'CompressDirTask'
    optional_params = ["compression", "dest", "ignore_errors"]

    def run_task(self, fw_spec):
        ignore_errors = self.get('ignore_errors', False)
        dest = self.get("dest", os.getcwd())
        compression = self.get("compression", "gz")
        try:
            compress_dir(dest, compression=compression)
        except:
            if not ignore_errors:
                raise ValueError(
                    "There was an error performing compression {} in {}."
                    .format(compression, dest))


class DecompressDirTask(FireTaskBase):
    """
    Decompress all files in a directory. Autodetects gz, bz2 and z file
    extensions.

    Args:
        dest (str): Optional. Path to decompress.
        ignore_errors (bool): Optional. Whether to ignore errors. Defaults to
            False.
    """

    _fw_name = 'DecompressDirTask'
    optional_params = ["dest", "ignore_errors"]

    def run_task(self, fw_spec):
        ignore_errors = self.get('ignore_errors', False)
        dest = self.get("dest", os.getcwd())
        try:
            decompress_dir(dest)
        except:
            if not ignore_errors:
                raise ValueError(
                    "There was an error performing decompression in %s." % dest)


class ArchiveDirTask(FireTaskBase):
    """
    Wrapper around shutil.make_archive to make tar archives.

    Args:
        base_name (str): Name of the file to create, including the path,
        minus any
            format-specific extension.
        format (str): Optional. one of "zip", "tar", "bztar" or "gztar".
            Defaults to gztar.
    """

    _fw_name = 'ArchiveDirTask'
    required_params = ["base_name"]
    optional_params = ["format"]

    def run_task(self, fw_spec):
        shutil.make_archive(self["base_name"],
                            format=self.get("format", "gztar"),
                            root_dir=".")
