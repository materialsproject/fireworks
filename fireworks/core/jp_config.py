'''
A set of global variables for job packing
'''

__author__ = 'Xiaohui'
__copyright__ = 'Copyright 2013, The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Sep 2, 2013'



def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class JPConfig(object):
    def __init__(self):
        self.MULTIPROCESSING = None # default single process framework

        self.PACKING_MANAGER_PORT = '27016'   # the internet port of the packing manager service

        self.PACKING_MANAGER_PASSWORD ='123'  # the password to connect to packing manager service

        self.PROCESS_LOCK = None # the shared Lock between processes

        self.NODE_LIST = None # the node list for sub jobs

        self.PACKING_MANAGER = None # the shared object manager