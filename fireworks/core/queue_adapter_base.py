#!/usr/bin/env python

'''
This module contains the QueueAdapterBase class.
'''


from fireworks.utilities.fw_serializers import FWSerializable,\
    serialize_fw, load_object

__author__ = 'Anubhav Jain'
__credits__ = 'Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class QueueAdapterBase(FWSerializable):
    '''
    The QueueAdapter is responsible for all interactions with a specific \
    queue management system. This includes handling all details of queue \
    script format as well as queue submission and management.
    
    A user should extend this class with implementations that work on \
    specific queue systems.
    '''
    
    _fw_name = 'QueueAdapterBase'
    
    def get_script_str(self, job_parameters, launch_dir):
        '''
        returns a (multi-line) String representing the queue script, e.g. PBS script. \
        All details of the queue script must be specified in the JobParameters().
        
        :param job_parameters: A JobParameters() instance
        :param launch_dir: The directory the job will be launched in
        '''
        raise NotImplementedError('get_script_str() not implemented for this queue adapter!')
    
    def submit_to_queue(self, job_parameters, script_file):
        '''
        submits the job to the queue, probably using subprocess or shutil
        :param job_parameters: A JobParameters() instance
        :param script_file: name of the script file to use (String)
        '''
        raise NotImplementedError('submit_to_queue() not implemented for this queue adapter!')

    def get_njobs_in_queue(self, job_parameters, username=None):
        '''
        returns the number of jobs in the queue, probably using subprocess or shutil to \
        call a command like 'qstat'. returns None when the number of jobs cannot be determined.
        
        :param job_parameters: a JobParameters() instance
        :param username: the username of the jobs to count (default is to autodetect)
        '''
        raise NotImplementedError('get_njobs_in_queue() not implemented for this queue adapter!')
    
    @serialize_fw
    def to_dict(self):
        return {}
    
    @classmethod
    def from_dict(self, m_dict):
        return self()
    
    
class JobParameters(FWSerializable):
    '''
    A JobParameters instance contains all the information needed to write a queue file \
    and submit to a queue system. Details of the queue file format and queue submission \
    commands should be included in the QueueAdapterBase object. Specific parameters used \
    by the QueueAdapterBase should be included in the params variable.
    '''
    def __init__(self, queue_adapter, params, logging_dir='.'):
        '''
        :param queue_adapter: An implementation of QueueAdapterBase()
        :param params: Additional parameters (dict) that the QueueAdapter might need.
        :param logging_dir: Directory (String) to write logs to
        '''
        self.qa = queue_adapter
        self.params = params
        self.logging_dir = logging_dir
    
    def to_dict(self):
        '''
         Note: the QueueAdapter is being serialized using the FW name alone \
         This keeps the serialization compact and easy to edit by humans. \
         The from_dict() will dynamically find the correct QueueAdapter using its fw_name.
         '''
        return {'qa_name': self.qa.fw_name, 'params': self.params, 'logging_dir': self.logging_dir}
            
    @classmethod
    def from_dict(self, m_dict):
        '''
        Note: The QueueAdapter is loaded based on its fw_name alone
        See the docs for to_dict() for more details
        '''
        qa_dict = {'_fw_name': m_dict['qa_name']}
        
        # load the QueueAdapter object dynamically
        qa = load_object(qa_dict)
        return JobParameters(qa, m_dict['params'], m_dict['logging_dir'])