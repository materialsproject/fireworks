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

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 30, 2013"


class LaunchPad(FWSerializable):
    
    def __init__(self, host='localhost', port=27017, name='fireworks', id_prefix='fw', username=None, password=None):
        if len(id_prefix) < 1:
            raise ValueError("Must enter a non-empty id prefix!")
        
        self.host = host
        self.port = port
        self.name = name
        self.id_prefix = id_prefix
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
        d['id_prefix'] = self.id_prefix
        d['username'] = self.username
        d['password'] = self.password
        return d
    
    @classmethod
    def from_dict(self, d):
        return LaunchPad(d['host'], d['port'], d['name'], d['id_prefix'], d['username'], d['password'])
    
    def initialize(self, password, require_password=True):
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if password == m_password or not require_password:
            self.fireworks.remove()
            self._restart_ids(1)
        else:
            raise ValueError("Invalid safeguard password! Password is today's date: {}".format(m_password))
        
    def _restart_ids(self, next_fw_id):
        '''
        TODO: add docs
        
        :param next_fw_id: make sure this is an INTEGER
        '''
        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id})
 
    def _get_new_id_num(self):
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']
    
    def get_new_fw_id(self):
        return ('{}:{}'.format(self.id_prefix, self._get_new_id_num()))
    
    def upsert_fw(self, fw):
        # TODO: make sure no child fws
        
        # TODO: make this also apply to sub-fireworks
        # TODO: add logging
        if not fw.fw_id:
            fw.fw_id = self.get_new_fw_id()
        
        # TODO: make this also apply to sub-fireworks, add children and parent keys
        self.fireworks.update({"fw_id": fw.fw_id}, fw.to_dict(), upsert=True)


if __name__ == "__main__":
    """
    TODO: add command line option parser for
    initialize <DB_FILE>
    upsert-firework <DB_FILE> <FW_FILE>
    get-firework <FW_ID>
    get-matching-fws <QUERY_JSON>
    """
    a = LaunchPad()
    a.to_file("launchpad.yaml")