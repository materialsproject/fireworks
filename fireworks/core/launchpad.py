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


class FWDatabase(FWSerializable):
    
    _fw_name = 'FireWorks Database'
    
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
        return FWDatabase(d['host'], d['port'], d['name'], d['id_prefix'], d['username'], d['password'])
    
    def _initialize(self):
        self.fireworks.remove()
        self._restart_ids(1)
        
    def _restart_ids(self, next_fw_id):
        '''
        TODO: add docs
        
        :param next_fw_id: make sure this is an INTEGER
        '''
        
        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": self.get_next_fw_id(force_id=next_fw_id)})
 
    def get_next_fw_id(self, force_id=None):
        next_id = force_id if force_id else self._id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']
        if self.id_prefix:
            return ('{}:{}'.format(self.id_prefix, next_id))


class LaunchPad():
    
    def __init__(self, fw_db=None):
        self.fw_db = fw_db if fw_db else FWDatabase()
    
    def initialize(self, password, require_password=True):
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')
        
        if password == m_password or not require_password:
            self.fw_db._initialize()
        else:
            raise ValueError("Invalid safeguard password! Password is today's date: {}".format(m_password))
    
    def upsert_fw(self):
        raise NotImplementedError()
    
    # TODO: methods to get status of FW, find matching FW, etc...
    
if __name__ == "__main__":
    """
    TODO: add command line option parser for
    initialize <DB_FILE>
    upsert-firework <DB_FILE> <FW_FILE>
    get-firework <FW_ID>
    get-matching-fws <QUERY_JSON>
    """
    a = FWDatabase()
    a.to_file("fw_database.yaml")