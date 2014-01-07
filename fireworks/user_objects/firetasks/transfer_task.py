"""
This module contains the TransferTask used to move and copy files. Remote transfer is also supported.
"""

from .fileio_tasks import FileTransferTask

__author__ = 'Anubhav Jain, David Waroquiers'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 29, 2013'


class TransferTask(FileTransferTask):
    _fw_name = "Transfer Task"
    """
    .. deprecated:

        Use :class:`fireworks.user_objects.firetasks.fileio_tasks
        .FileTransferTask` instead.
    """

