#!/usr/bin/env python

"""
A FireWork defines a workflow step.

An FWorkflow connects FireWorks by their fw_ids.

A Launch is a describes a FireWork's run on a computing resource. The same Launch might apply to multiple FireWorks,
e.g. if they are identical.

A FWDecision encapsulates the output of that launch.
"""
from StringIO import StringIO
from collections import defaultdict
import datetime
import tarfile
from fireworks.utilities.fw_serializers import FWSerializable, load_object
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"

# TODO: this module needs to be broken up for sure...

# TODO: add ability to block ports
# TODO: consider using Mongo oid as fw_id. How important is readability?
# TODO: add created date to FW


class FireWork(FWSerializable):
    def __init__(self, tasks, spec=None, fw_id=-1, launch_data=None, state='WAITING'):
        """
        TODO: add more docs
        
        reserved spec keywords:
            _tasks - a list of FireTasks to run
            _priority - the priority of the FW
        
        :param tasks: a list of FireTasks
        :param spec: a dict specification of the job to run
        :param fw_id: the FW's database id to the LaunchPad. Negative numbers will be re-assigned dynamically when
        they are entered in the database through the LaunchPad.
        :param launch_data: a list of Launch objects of this FireWork
        :param state: the state of the FW (e.g. WAITING, RUNNING, COMPLETED, CANCELED)
        """
        # transform tasks into a list, if not in that format
        if not isinstance(tasks, list):
            tasks = [tasks]

        self.tasks = tasks
        self.spec = spec if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in tasks]
        self.fw_id = fw_id
        self.launch_data = launch_data if launch_data else []
        self.state = state

    def to_dict(self):
        """
        This is a 'minimal' or 'compact' dict representation of the FireWork
        """
        m_dict = {'spec': self.spec, 'fw_id': self.fw_id}
        if len(self.launch_data) > 0:
            m_dict['launch_data'] = [l.to_dict() for l in self.launch_data]

        if self.state != 'WAITING':
            m_dict['state'] = self.state

        return m_dict

    # TODO: consider using a kwarg on the to_dict method, and carrying that over to the serialization class (
    # to_format, to_file)

    def to_db_dict(self):
        """
        This is a 'full' dict representation of a FireWork. It contains redundant fields that enhance information
        retrieval.
        """
        m_dict = self.to_dict()
        m_dict['launch_data'] = [l.to_db_dict() for l in self.launch_data]
        m_dict['state'] = self.state
        return m_dict

    @classmethod
    def from_dict(cls, m_dict):
        tasks = [load_object(t) for t in m_dict['spec']['_tasks']]
        fw_id = m_dict.get('fw_id', None)
        ld = m_dict.get('launch_data', None)
        if ld:
            ld = [Launch.from_dict(tmp) for tmp in ld]
        state = m_dict.get('state', 'WAITING')
        return FireWork(tasks, m_dict['spec'], fw_id, ld, state)


#TODO: add a decision to the Launch
class Launch(FWSerializable):
    # TODO: add an expiration date
    def __init__(self, fworker, host=None, ip=None, launch_dir=None, stored_data=None, start=None, end=None, state=None,
                 launch_id=None):
        """
        
        :param fworker: A FWorker object describing the worker
        :param host: the hostname where the launch took place (probably automatically set)
        :param ip: the ip address where the launch took place (probably automatically set)
        :param launch_dir: the directory on the host where the launch took place (probably automatically set)
        :param stored_data: data (as dict) to store
        :param state: the state of the Launch
        :param launch_id: the id of the Launch for the LaunchPad
        """
        if state not in LAUNCH_RANKS:
            raise ValueError("Invalid launch state: {}".format(state))

        self.fworker = fworker
        self.host = host
        self.ip = ip
        self.launch_dir = launch_dir
        self.stored_data = stored_data if stored_data else None
        self.start = start if start else datetime.datetime.utcnow()
        self.end = end
        self.state = state
        self.launch_id = launch_id

    def to_dict(self):
        return {'fworker': self.fworker.to_dict(), 'stored_data': self.stored_data, 'start': self.start,
                'end': self.end, 'host': self.host, 'ip': self.ip, 'launch_dir': self.launch_dir, 'state': self.state,
                'launch_id': self.launch_id}

    @property
    def time_secs(self):
        return (self.end - self.start).total_seconds() if self.end else None

    def to_db_dict(self):
        m_d = self.to_dict()
        m_d['time_secs'] = self.time_secs
        return m_d

    @classmethod
    def from_dict(cls, m_dict):
        fworker = FWorker.from_dict(m_dict['fworker'])
        return Launch(fworker, m_dict['host'], m_dict['ip'], m_dict['launch_dir'], m_dict['stored_data'],
                      m_dict['start'], m_dict['end'], m_dict['state'], m_dict['launch_id'])
