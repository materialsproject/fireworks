#!/usr/bin/env python

"""
A FireWork defines a workflow as a DAG (directed acyclical graph).

A Launch is a describes a FireWork's run on a computing resource.
"""
from fireworks.utilities.fw_serializers import FWSerializable, load_object
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


#TODO: make script plural?
#TODO: add ability to block ports

class FireWork(FWSerializable):
    
    def __init__(self, tasks, spec=None, fw_id=None, launch_data=None):
        """
        TODO: add more docs
        
        reserved spec keywords:
            _tasks - a list of FireTasks to run
            _priority - the priority of the FW
        
        :param tasks: a list of FireTasks
        :param spec: a dict specification of the job to run
        :param fw_id: the FW's database id to the LaunchPad
        :param launch_data: a list of Launch objects of this FireWork
        """
        # transform tasks into a list, if not in that format
        if not isinstance(tasks, list):
            tasks = [tasks]
        
        self.tasks = tasks
        self.spec = spec if spec else {}
        self.spec['_tasks'] = [t.to_dict() for t in tasks]
        self.fw_id = fw_id
        self.launch_data = launch_data if launch_data else []

    def to_dict(self):
        """
        This is a 'minimal' or 'compact' dict representation of the FireWork
        """
        return {'spec': self.spec, 'fw_id': self.fw_id, 'launch_data': [l.to_dict() for l in self.launch_data]}
    
    # consider using a kwarg on the to_dict method, and carrying that over to the serialization class (to_format, to_file)
    def to_db_dict(self):
        """
        This is a 'full' dict representation of a FireWork. It contains redundant fields that enhance information retrieval.
        """
        m_dict = self.to_dict()
        m_dict['state'] = self.state
        return m_dict
    
    @classmethod
    def from_dict(cls, m_dict):
        tasks = [load_object(t) for t in m_dict['spec']['_tasks']]
        fw_id = m_dict.get('fw_id', None)
        ld = m_dict.get('launch_data', None)
        if ld:
            ld = [Launch.from_dict(tmp) for tmp in ld]
        return FireWork(tasks, m_dict['spec'], fw_id, ld)
    
    @property
    def state(self):
        """
        Iterate through the launch_data, and find the Launch that is furthest ahead. \
        That is the state of the FireWork as a whole.
        """
        max_score = 0
        max_state = 'WAITING'
        
        for l in self.launch_data:
            if LAUNCH_RANKS[l.state] > max_score:
                max_score = LAUNCH_RANKS[l.state]
                max_state = l.state 
        
        return max_state
            
#TODO: add a working dir at least

class Launch(FWSerializable):
    
    def __init__(self, fworker, state=None, launch_id=None):
        """
        
        :param fworker: A FWorker object describing the worker
        :param state: the state of the Launch
        :param launch_id: the id of the Launch for the LaunchPad
        """
        if state not in LAUNCH_RANKS:
            raise ValueError("Invalid launch state: {}".format(state))
        
        self.fworker = fworker
        self.state = state
        self.launch_id = launch_id
    
    def to_dict(self):
        return {"fworker": self.fworker.to_dict(), "state": self.state, "launch_id": self.launch_id}
    
    @classmethod
    def from_dict(cls, m_dict):
        fworker = FWorker.from_dict(m_dict['fworker'])
        return Launch(fworker, m_dict['state'], m_dict['launch_id'])


class FWDecision():
    """
    A FWDecision returns one of several potential actions:
        -CONTINUE means continue to the next stage in the workflow, no changes are made to the firework
        -BRANCH means to insert new Fireworks into the workflow and forget about the current children
        -DETOUR means to insert new Fireworks into the workflow, and then run the current children
        -TERMINATE means to terminate this branch of the workflow (any children of this Stage will NOT be run).

    The output parameter is a dict that gets passed to the 'output' parameter of the LaunchInfo being analyzed.
    The output is a dict that:
        - stores any metadata about the decision
        - is used by Fuses of child FWs to determine how to proceed
         
    """
    actions = ["CONTINUE", "BRANCH", "DETOUR", "TERMINATE"]
    
    def __init__(self, action, stored_data=None, mod_spec=None, add_fws=None):
        
        if action not in FWDecision.actions:
            raise ValueError("Invalid decision: " + action)
        
        if action != "CONTINUE" and mod_spec:
            raise ValueError("You can only modify the spec if you decide to CONTINUE")
        
        if action not in ["BRANCH", "DETOUR"] and add_fws:
            raise ValueError("You cannot " + str(action) + " whilst also inserting fireworks")
        
        if action in ["BRANCH", "DETOUR"] and not add_fws:
            raise ValueError("If you " + str(action) + ", you must specify fireworks to insert!")
        
        self.action = action
        self.add_fws = add_fws
        self.mod_spec = mod_spec
        self.stored_data = stored_data if stored_data else {}
        
    def to_dict(self):
        return {"action": self.action, "stored_data": self.stored_data, "mod_spec": self.mod_spec, "add_fws": self.add_fws}
    
    @classmethod
    def from_dict(cls, m_dict):
        return FWDecision(m_dict['action'], m_dict['stored_data'], m_dict['mod_spec'], m_dict['add_fws'])