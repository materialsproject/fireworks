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


class PackingManager(BaseManager):
    '''
    Customized Manager class.
    It spawns a child process which can be used as a server process to
    provide shared objects.
    When registered with the LaunchPad typeid, it will be able to return
    a proxy for the LaunchPad running in the server process. All the access
    for other processes will be forward to the instance in the server process.
    This is how the inter-process Singleton is implemented. Please be noted
    that the decorator singleton pattern only works for single process programs.
    Also, please noted this class has nothing to do with process management. Its
    only role is to provide shared objects.
    Example:
        m = PackingManager(address=('127.0.0.1', port), authkey=password)
        m.connect()
        launchpad = m.LaunchPad()
    '''
    pass


PackingManager.register('LaunchPad')
PackingManager.register('Running_IDs')

def acquire_jp_lock():
    jp_conf = JPConfig()
    if jp_conf.MULTIPROCESSING:
        jp_conf.PROCESS_LOCK.acquire()

def release_jp_lock():
    jp_conf = JPConfig()
    if jp_conf.MULTIPROCESSING:
        jp_conf.PROCESS_LOCK.release()