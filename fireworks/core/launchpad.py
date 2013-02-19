#!/usr/bin/env python

"""
The LaunchPad manages the FireWorks database.
"""
import datetime
from fireworks.user_objects.firetasks.subprocess_task import SubprocessTask
from fireworks.utilities.fw_serializers import FWSerializable
from pymongo.mongo_client import MongoClient
from fireworks.core.firework import FireWork, Launch, FWorkflow
from pymongo import DESCENDING

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'

#TODO: add logging throughout


class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """
    
    def __init__(self, host='localhost', port=27017, name='fireworks', id_prefix=None, username=None, password=None):
        """
        
        :param host:
        :param port:
        :param name:
        :param id_prefix:
        :param username:
        :param password:
        """
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password
        
        connection = MongoClient(host, port)
        self.database = connection[name]
        if username:
            self.database.authenticate(username, password)
        
        self.fireworks = self.database.fireworks
        self.fw_id_assigner = self.database.fw_id_assigner
        self.wfconnections = self.database.wfconnections
        
    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        d = {}
        d['host'] = self.host
        d['port'] = self.port
        d['name'] = self.name
        d['username'] = self.username
        d['password'] = self.password
        return d
    
    @classmethod
    def from_dict(cls, d):
        return LaunchPad(d['host'], d['port'], d['name'], d['username'], d['password'])
    
    def initialize(self, password, require_password=True):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! \
        To safeguard against accidentally erasing an existing database, a password must \
        be entered.
        :param password: A String representing today's date, e.g. '2012-12-31'
        :param require_password: Whether a password is required to initialize the DB. Highly \
        recommended to leave this set to True, otherwise you are inviting dangerous behavior!
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if password == m_password or not require_password:
            self.fireworks.remove()
            self.wfconnections.remove()
            self._restart_ids(1, 1)
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))
        
    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        (internal method) Used to reset id counters
        :param next_fw_id: id to give next FireWork (int)
        :param next_launch_id: id to give next Launch (int)
        """

        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id, "next_launch_id": next_launch_id})
 
    def _checkout_fw(self, fworker):
        """
        (internal method) Finds a FireWork that's ready to be run, marks it as running, and returns it to the caller. \
        The caller should run this FireWork.
        
        :param fworker: A FWorker instance
        """
        m_query = dict(fworker.query)  # make a copy of the query
        m_query['state'] = {'$in': ['WAITING', 'FIZZLED']}
        
        # check out the matching firework, depending on the query set by the FWorker
        m_fw = self.fireworks.find_and_modify(query=m_query, fields={"fw_id": 1}, update={'$set': {'state': 'RUNNING'}}, sort=[("spec._priority", DESCENDING)])
        
        if not m_fw:
            return (None, None)
        
        # create a launch
        launch_id = self.get_new_launch_id()
        m_launch = Launch(fworker, 'RUNNING', launch_id)
        
        # add launch to FW
        m_fw_dict = self.fireworks.find_and_modify(query={'fw_id': m_fw['fw_id']}, update={'$push': {'launch_data': m_launch.to_dict()}}, new=True)
        
        # return FW
        return (FireWork.from_dict(m_fw_dict), launch_id)
    
    def _complete_launch(self, m_fw, launch_id):
        """
        (internal method) used to mark a FireWork's Launch as completed.
        :param m_fw:
        :param launch_id:
        """
        # TODO: what happens when multiple FireWorks share the same launch? Technically _complete_launch should only depend on the launch_id.
        # You could implement this using a "launches_to_watch" key in FireWorks, and updating all FireWorks where the launch_id matches.
            
        for launch in m_fw.launch_data:
            if launch.launch_id == launch_id:
                launch.state = "COMPLETED"
                break
        
        self.upsert_fw(m_fw)
        
    def get_new_fw_id(self):
        """
        Checkout the next FireWork id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']
    
    def get_new_launch_id(self):
        """
        Checkout the next Launch id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_launch_id': 1}})['next_launch_id']

    '''
    def upsert_fw(self, fw):
        """
        Given a FireWork, either insert it into the database or update the FireWork with the same id.
        
        :param fw: A FireWork instance
        """
        # TODO: make sure no child fws
        # TODO: make this also apply to sub-fireworks
        # TODO: make this to be INsert FW, not UPsert. Much safer that way unless you really need upsert.
        # TODO: add logging
        if not fw.fw_id or fw.fw_id < 0:
            fw.fw_id = self.get_new_fw_id()
        
        # TODO: make this also apply to sub-fireworks, add children and parent keys
        self.fireworks.update({"fw_id": fw.fw_id}, fw.to_db_dict(), upsert=True)
    '''

    def insert_wf(self, fwf):
        """

        :param fwf: an FWorkflow object.
        """

        if isinstance(fwf, FireWork):
            fwf = FWorkflow.from_FireWork(fwf)

        # mapping between old and new FireWork ids
        old_new = {}

        # insert the FireWorks
        for fw in fwf.id_fw.itervalues():
            # TODO: update the connections dict!!!

            if not fw.fw_id or fw.fw_id < 0:
                new_id = self.get_new_fw_id()
                old_new[str(fw.fw_id)] = str(new_id)
                fw.fw_id = new_id

            self.fireworks.insert(fw.to_db_dict())

        print old_new
        # redo the FWorkflow based on new mappings
        fwf._reassign_ids(old_new)
        self.wfconnections.insert(fwf.to_db_dict())

    def get_fw_by_id(self, fw_id, ignore_children=False):
        """
        Given a FireWork id, give back a FireWork object
        :param fw_id: FireWork id (int)
        :param ignore_children: if True, does not return parent or child FireWorks, just a single workflow step.
        """
        # TODO: implement children / parents / ignore_children parameter
        fw_dict = self.fireworks.find_one({"fw_id": fw_id})
        return FireWork.from_dict(fw_dict)

    def get_fw_ids(self, query=None):
        """
        Return all the fw ids that match a query
        :param query: a dict representing a Mongo query
        """
        fw_ids = []
        criteria = query if query else {}
        
        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=[("spec._priority", DESCENDING)]):
            fw_ids.append(fw["fw_id"])
        
        return fw_ids

if __name__ == "__main__":
    a = LaunchPad()
    a.initialize('2013-02-19')
    b = FireWork(SubprocessTask.from_str('hello'), {}, fw_id=-1)
    c = FWorkflow.from_FireWork(b)
    a.insert_wf(c)
