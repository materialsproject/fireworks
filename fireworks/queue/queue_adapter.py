from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw, load_object

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 28, 2013'


class QueueAdapterBase(FWSerializable):
    """
    The QueueAdapter is responsible for all interactions with a specific \
    queue management system. This includes handling all details of queue \
    script format as well as queue submission and management.

    A user should extend this class with implementations that work on \
    specific queue systems.
    """

    _fw_name = 'QueueAdapterBase'

    def __init__(self, params, logging_dir='.'):
        """
        :param params: Additional parameters (dict) that the QueueAdapter might need.
        :param logging_dir: Directory (String) to write logs to
        """
        self.params = params
        self.logging_dir = logging_dir

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

    @serialize_fw
    def to_dict(self):
        return {'params': self.params, 'logging_dir': self.logging_dir}

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict['params'], m_dict['logging_dir'])