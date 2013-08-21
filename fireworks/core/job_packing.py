"""
Support modules for job packing.
PackingManager provides share objects for all the processing.
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
    pass


PackingManager.register('LaunchPad')

def create_launchpad(launchpad_file, strm_lvl):
    if launchpad_file:
        launchpad = LaunchPad.from_file(launchpad_file)
    else:
        launchpad = LaunchPad(strm_lvl=strm_lvl)
    return launchpad


def manager_initializer():
    fw_conf = FWConfig()
    fw_conf.MULTIPROCESSING = None # don't confuse the server process


def run_manager_server(lauchpad_file, strm_lvl, port, password):
    PackingManager.register('LaunchPad', callable=lambda: create_launchpad(lauchpad_file, strm_lvl))
    m = PackingManager(address=('127.0.0.1', port), authkey=password)
    m.start(initializer=manager_initializer)
    return m


def rapidfire_process(fworker, nlaunches, sleep, loglvl, port, password, node_list, lock):
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
    lock = multiprocessing.Lock()
    processes = [Process(target=rapidfire_process, args=(fworker, nlaunches, sleep, loglvl, port, password, nl, lock))
                 for nl in node_lists]
    for p in processes:
        p.start()
    return processes


def split_node_lists(num_rockets):
    node_lists = None
    if 'PBS_NODEFILE' in os.environ:
        node_file = os.environ['PBS_NODEFILE']
        orig_node_list = None
        with open(node_file) as f:
            orig_node_list = [line.strip() for line in f.readlines()]
        n = len(orig_node_list)
        step = n/num_rockets
        node_lists = [orig_node_list[i:i+step] for i in range(0, num_rockets, step)]
    else:
        node_lists = [None] * num_rockets
    return node_lists