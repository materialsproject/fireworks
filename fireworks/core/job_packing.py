"""
Support module for job packing.
This module contains function to prepare and launch the process.
Also, there is a PackingManager class which provides share objects
Between processes.
"""
from multiprocessing import Process
from multiprocessing.managers import BaseManager
import multiprocessing
import os
from fireworks.core.fw_config import FWConfig
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import rapidfire

__author__ = 'Xiaohui'
__copyright__ = 'Copyright 2013, The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Aug 19, 2013'


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

def create_launchpad(launchpad_file, strm_lvl):
    '''
    Function to create the server side LaunchPad instance.
    This function will be called only once, only by the
    Manager server process.

    :param launchpad_file: (str) path to launchpad file
    :param strm_lvl: (str) level at which to output logs to stdout
    :return: (LaunchPad) object
    '''
    if launchpad_file:
        launchpad = LaunchPad.from_file(launchpad_file)
    else:
        launchpad = LaunchPad(strm_lvl=strm_lvl)
    return launchpad


def manager_initializer():
    '''
    The intialization function for Manager server process.
    :return:
    '''
    fw_conf = FWConfig()
    fw_conf.MULTIPROCESSING = None # don't confuse the server process


def run_manager_server(lauchpad_file, strm_lvl, port, password):
    '''
    Start the Manager server process. The shared LaunchPad object proxy will
    be available after calling this function. Nothing to do with process
    management.

    :param lauchpad_file: (str) path to launchpad file
    :param strm_lvl: (str) level at which to output logs
    :param port: (int) Listening port number
    :param password: (str) security password to access the server
    :return: (PackingManager) object
    '''
    PackingManager.register('LaunchPad', callable=lambda: create_launchpad(lauchpad_file, strm_lvl))
    m = PackingManager(address=('127.0.0.1', port), authkey=password)
    m.start(initializer=manager_initializer)
    return m


def rapidfire_process(fworker, nlaunches, sleep, loglvl, port, password, node_list, lock):
    '''
    Starting point of a sub job launching process.

    :param fworker: (FWorker) object
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number
    :param password: (str) security password to access the server
    :param node_list: (list of str) computer node list
    :param lock: (multiprocessing.Lock) Mutex
    :return:
    '''
    fw_conf = FWConfig()
    fw_conf.MULTIPROCESSING = True
    fw_conf.PACKING_MANAGER_PORT = port
    fw_conf.PACKING_MANAGER_PASSWORD = password
    fw_conf.NODE_LIST = node_list
    fw_conf.PROCESS_LOCK = lock
    m = PackingManager(address=('127.0.0.1', port), authkey=password)
    m.connect()
    launchpad = m.LaunchPad()
    rapidfire(launchpad, fworker, None, nlaunches, -1, sleep, loglvl)


def launch_rapidfire_processes(fworker, nlaunches, sleep, loglvl, port, password, node_lists):
    '''
    Create the sub job launching processes

    :param fworker: (FWorker) object
    :param nlaunches: nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number
    :param password: (str) security password to access the server
    :param node_lists: (list of str) computer node list
    :return: (List of multiprocessing.Process) all the created processes
    '''
    lock = multiprocessing.Lock()
    processes = [Process(target=rapidfire_process, args=(fworker, nlaunches, sleep, loglvl, port, password, nl, lock))
                 for nl in node_lists]
    for p in processes:
        p.start()
    return processes


def split_node_lists(num_rockets):
    '''
    Allocate node list of the large job to the sub jobs
    :param num_rockets: (int) number of sub jobs
    :return: (list of list) NODELISTs
    '''
    if 'PBS_NODEFILE' in os.environ:
        node_file = os.environ['PBS_NODEFILE']
        with open(node_file) as f:
            orig_node_list = [line.strip() for line in f.readlines()]
        n = len(orig_node_list)
        step = n/num_rockets
        if step*num_rockets != n:
            raise ValueError("can't allocate nodes, {} can't be divided by {}".format(n, num_rockets))
        node_lists = [orig_node_list[i:i+step] for i in range(0, n, step)]
    else:
        node_lists = [None] * num_rockets
    return node_lists