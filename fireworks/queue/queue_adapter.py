#!/usr/bin/env python

"""
This module contains contracts for defining adapters to various queueing systems, e.g. PBS/SLURM/SGE.
"""

import os
import string
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw
from fireworks.utilities.fw_utilities import get_fw_logger

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
    template_file = 'OVERRIDE_ME'
    defaults = {}

    def get_script_str(self, launch_dir):
        """
        returns a (multi-line) String representing the queue script, e.g. PBS script. \
        Uses the template_file along with internal parameters to create the script.

        :param launch_dir: (str) The directory the job will be launched in
        """
        with open(self.template_file) as f:
            a = QScriptTemplate(f.read())

            # set substitution dict for replacements into the template
            subs_dict = dict([(k,v) for k,v in dict(self).iteritems() if v is not None])  # clean null values

            for k, v in self.defaults:
                subs_dict[k] = subs_dict.get(k, v)

            subs_dict['job_name'] = subs_dict.get('job_name', 'FW_job')

            launch_dir = os.path.abspath(launch_dir)
            subs_dict['launch_dir'] = launch_dir

            unclean_template = a.safe_substitute(subs_dict)  # might contain unused parameters as leftover $$

            clean_template = []

            for line in unclean_template.split('\n'):
                if '$$' not in line:
                    clean_template.append(line)

            return '\n'.join(clean_template)

    def submit_to_queue(self, script_file):
        """
        submits the job to the queue, probably using subprocess or shutil

        :param script_file: (str) name of the script file to use (String)
        """
        raise NotImplementedError('submit_to_queue() not implemented for this queue adapter!')

    def get_njobs_in_queue(self, username=None):
        """
        returns the number of jobs in the queue, probably using subprocess or shutil to \
        call a command like 'qstat'. returns None when the number of jobs cannot be determined.

        :param username: (str) the username of the jobs to count (default is to autodetect)
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

    def get_qlogger(self, name):
        if self['logdir']:
            return get_fw_logger(name, self['logdir'])
        else:
            return get_fw_logger(name, stream_level='CRITICAL')


class QScriptTemplate(string.Template):
    delimiter = '$$'