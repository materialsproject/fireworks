#!/usr/bin/env python

'''
TODO: add docs

Note: usernames and passwords are stored and output to files as plain text!

TODO: add logging
TODO: add methods for inserting FW, updating Engines, etc

'''
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
    
    def __init__(self, host='localhost', port=27017, name='fireworks', username=None, password=None):
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password
        
        connection = MongoClient(host, port)
        self.database = connection[name]
        if username:
            self.database.authenticate(username, password)
        
    def to_dict(self):
        d = {}
        d['host'] = self.host
        d['port'] = self.port
        d['name'] = self.name
        d['username'] = self.username
        d['password'] = self.password
    
    def from_dict(self, d):
        return FWDatabase(d['host'], d['port'], d['name'], d['username'], d['password'])
    
if __name__ == "__main__":
    a = FWDatabase()