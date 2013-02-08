#!/usr/bin/env python

'''
TODO: add docs

Note: usernames and passwords are stored and output to files as plain text!

TODO: add logging
TODO: add methods for inserting FW, updating Engines, etc
TODO: add auto-initialize

'''
import datetime
from fireworks.utilities.fw_serializers import FWSerializable
from pymongo.mongo_client import MongoClient
from fireworks.core.firework import FireWork, Launch
from pymongo import DESCENDING

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 30, 2013"


class LaunchPad(FWSerializable):
    
    def __init__(self, host='localhost', port=27017, name='fireworks', id_prefix=None, username=None, password=None):
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
        
    def to_dict(self):
        d = {}
        d['host'] = self.host
        d['port'] = self.port
        d['name'] = self.name
        d['username'] = self.username
        d['password'] = self.password
        return d
    
    @classmethod
    def from_dict(self, d):
        return LaunchPad(d['host'], d['port'], d['name'], d['username'], d['password'])
    
    def initialize(self, password, require_password=True):
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if password == m_password or not require_password:
            self.fireworks.remove()
            self._restart_ids(1, 1)
        else:
            raise ValueError("Invalid safeguard password! Password is today's date: {}".format(m_password))
        
    def _restart_ids(self, next_fw_id, next_launch_id):
        '''
        TODO: add docs
        
        :param next_fw_id: make sure this is an INTEGER
        '''
        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id, "next_launch_id": next_launch_id})
 
    def _checkout_fw(self, query, fworker):
        query['state'] = {'$in': ['WAITING', 'FIZZLED']}
        
        # check out the matching firework
        m_fw_dict = self.fw_id_assigner.find_and_modify(query=query, update={'$set': {'state': 'RUNNING'}})
        # no matching fireworks...
        if not m_fw_dict:
            return None
        
        # create a launch
        launch_id = self.get_new_launch_id()
        m_launch = Launch(fworker, 'RUNNING', launch_id)
        
        # add launch to FW
        m_fw_dict = self.fw_id_assigner.find_and_modify(query=query, update={'$push': {'launch_data': m_launch.to_dict()}}, new=True)
        
        return (FireWork.from_dict(m_fw_dict), launch_id)
    
    def _complete_launch(self, fw, launch_id):
        
        m_fw = FireWork.from_dict({"fw_id": fw.fw_id})
        for launch in m_fw.launch_data:
            if launch.launch_id == launch_id:
                print 'found the launch!'
                launch.state = "COMPLETED"
                print m_fw.to_db_dict()
        
        self.upsert_fw(m_fw)
        
    def get_new_fw_id(self):
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']
    
    def get_new_launch_id(self):
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_launch_id': 1}})['next_launch_id']
    
    def upsert_fw(self, fw):
        # TODO: make sure no child fws
        
        # TODO: make this also apply to sub-fireworks
        # TODO: add logging
        if not fw.fw_id:
            fw.fw_id = self.get_new_fw_id()
        
        # TODO: make this also apply to sub-fireworks, add children and parent keys
        self.fireworks.update({"fw_id": fw.fw_id}, fw.to_db_dict(), upsert=True)
    
    def get_fw_by_id(self, fw_id, ignore_children=False):
        # TODO: implement children
        fw_dict = self.fireworks.find_one({"fw_id": fw_id})
        return FireWork.from_dict(fw_dict)

    def get_fw_ids(self, query=None):
        fw_ids = []
        criteria = query if query else {}
        
        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=[("fw_spec._priority", DESCENDING)]):
            fw_ids.append(fw["fw_id"])
        
        return fw_ids

if __name__ == "__main__":
    """
    TODO: add command line option parser for
    initialize <DB_FILE>
    upsert-firework <DB_FILE> <FW_FILE>
    get-firework <FW_ID>
    get-matching-fws <QUERY_JSON>
    """
    a = LaunchPad()
    a.to_file("../../fw_tutorial/launchpad.yaml")