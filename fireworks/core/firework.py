#!/usr/bin/env python

"""
A FireWork defines a workflow step.

An FWorkflow connects FireWorks by their fw_ids.

A Launch is a describes a FireWork's run on a computing resource. The same Launch might apply to multiple FireWorks,
e.g. if they are identical.

A FWAction encapsulates the output of that launch.
"""

import datetime
from fireworks.core.firetask import Launch
from fireworks.utilities.fw_serializers import FWSerializable, recursive_serialize, recursive_deserialize

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


# TODO: add ability to block ports
# TODO: properly load object recursively, e.g. in the spec

class FireWork(FWSerializable):
    def __init__(self, tasks, spec=None, fw_id=-1, launches=None, state='WAITING', created_at=None):
        """
        TODO: add more docs
        
        reserved spec keywords:
            _tasks - a list of FireTasks to run
            _priority - the priority of the FW
            _dupefinder - a DupeFinder object, for avoiding duplicates
        
        :param tasks: a list of FireTasks
        :param spec: a dict specification of the job to run
        :param fw_id: the FW's database id to the LaunchPad. Negative numbers will be re-assigned dynamically when
        they are entered in the database through the LaunchPad.
        :param launches: a list of Launch objects of this FireWork
        :param state: the state of the FW (e.g. WAITING, RUNNING, COMPLETED, CANCELED)
        """
        # transform tasks into a list, if not in that format
        if not isinstance(tasks, list):
            tasks = [tasks]

        self.tasks = tasks
        self.spec = spec if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in tasks]
        self.fw_id = fw_id
        self.launches = launches if launches else []
        self.created_at = created_at if created_at else datetime.datetime.utcnow()
        self.state = state

    @recursive_serialize
    def to_dict(self):
        """
        This is a 'minimal' or 'compact' dict representation of the FireWork
        """
        m_dict = {'spec': self.spec, 'fw_id': self.fw_id, 'created_at': self.created_at}

        if len(self.launches) > 0:
            m_dict['launches'] = self.launches

        if self.state != 'WAITING':
            m_dict['state'] = self.state

        return m_dict

    def to_db_dict(self):
        """
        """
        m_dict = self.to_dict()
        m_dict['launches'] = [l.launch_id for l in self.launches]  # the launches are stored separately
        m_dict['state'] = self.state
        return m_dict

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        tasks = m_dict['spec']['_tasks']
        l = m_dict.get('launches', None)
        if l:
            l = [Launch.from_dict(tmp) for tmp in l]
        fw_id = m_dict.get('fw_id', -1)
        state = m_dict.get('state', 'WAITING')
        created_at = m_dict.get('created_at', None)

        return FireWork(tasks, m_dict['spec'], fw_id, l, state, created_at)