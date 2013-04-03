from collections import defaultdict
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw, load_object

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 28, 2013'


class QueueAdapterBase(dict, FWSerializable):
    """
    The QueueAdapter is responsible for all interactions with a specific \
    queue management system. This includes handling all details of queue \
    script format as well as queue submission and management.

    A user should extend this class with implementations that work on \
    specific queue systems.
    """

    _fw_name = 'QueueAdapterBase'

    def get_script_str(self, launch_dir):
        """
        returns a (multi-line) String representing the queue script, e.g. PBS script. \
        All details of the queue script must be specified in self.params

        :param launch_dir: The directory the job will be launched in
        """
        raise NotImplementedError('get_script_str() not implemented for this queue adapter!')

    def submit_to_queue(self, script_file):
        """
        submits the job to the queue, probably using subprocess or shutil
        :param script_file: name of the script file to use (String)
        """
        raise NotImplementedError('submit_to_queue() not implemented for this queue adapter!')

    def get_njobs_in_queue(self, username=None):
        """
        returns the number of jobs in the queue, probably using subprocess or shutil to \
        call a command like 'qstat'. returns None when the number of jobs cannot be determined.

        :param username: the username of the jobs to count (default is to autodetect)
        """
        raise NotImplementedError('get_njobs_in_queue() not implemented for this queue adapter!')

    def __getitem__(self, key):
        """
        Reproduce a simple defaultdict-like behavior - any unset parameters return None
        """
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None

    @serialize_fw
    def to_dict(self):
        return dict(self)

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict)