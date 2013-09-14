"""
Support module for job packing.
This module contains function to prepare and launch the process.
Also, there is a DataServer class which provides share objects
Between processes.
"""
from multiprocessing import Process
import multiprocessing
import os
import threading
import time
from fireworks.core.fw_config import FWConfig, FWData
from fireworks.core.rocket_launcher import rapidfire
from fireworks.utilities.fw_utilities import DataServer


__author__ = 'Xiaohui Qu, Anubhav Jain'
__copyright__ = 'Copyright 2013, The Material Project & The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Aug 19, 2013'


def ping_launch_jp(port, stop_event):
    '''
    The process version of ping_launch

    :param port: (int) Listening port number of the DataServer
    :param stop_event:
    :return:
    '''

    ds = DataServer(address=('127.0.0.1', port), authkey=FWConfig().DS_PASSWORD)
    ds.connect()

    lp = ds.LaunchPad()
    while not stop_event.is_set():
        for pid, lid in ds.Running_IDs().items():
            if lid:
                try:
                    os.kill(pid, 0)  # throws OSError if the process is dead
                    lp.ping_launch(lid)
                except OSError:
                    pass  # means this process is dead!

        stop_event.wait(FWConfig().PING_TIME_SECS)


def rapidfire_process(fworker, nlaunches, sleep, loglvl, port, node_list, sub_nproc, lock):
    '''
    Starting point of a sub job launching process.

    :param fworker: (FWorker) object
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number of the shared object manage
    :param password: (str) security password to access the server
    :param node_list: (list of str) computer node list
    :param sub_nproc: (int) number of processors of the sub job
    :param lock: (multiprocessing.Lock) Mutex
    :return:
    '''
    jp_conf = FWData()
    jp_conf.MULTIPROCESSING = True
    jp_conf.NODE_LIST = node_list
    jp_conf.SUB_NPROCS = sub_nproc
    jp_conf.PROCESS_LOCK = lock
    ds = DataServer(address=('127.0.0.1', port), authkey=FWConfig().DS_PASSWORD)
    ds.connect()
    launchpad = ds.LaunchPad()
    jp_conf.DATASERVER = ds
    rapidfire(launchpad, fworker, None, nlaunches, -1, sleep, loglvl)


def launch_rapidfire_processes(fworker, nlaunches, sleep, loglvl, port, node_lists, sub_nproc_list):
    '''
    Create the sub job launching processes

    :param fworker: (FWorker) object
    :param nlaunches: nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number
    :param node_lists: (list of str) computer node list
    :param sub_nproc_list: (list of int) list of the number of the process of sub jobs
    :return: (List of multiprocessing.Process) all the created processes
    '''
    lock = multiprocessing.Lock()
    processes = [Process(target=rapidfire_process, args=(fworker, nlaunches, sleep, loglvl, port, nl, sub_nproc, lock))
                 for nl, sub_nproc in zip(node_lists, sub_nproc_list)]
    for p in processes:
        p.start()
        time.sleep(0.15)
    return processes


def split_node_lists(num_rockets, total_node_list=None, ppn=24, serial_mode=False):
    '''
    Allocate node list of the large job to the sub jobs

    :param num_rockets: (int) number of sub jobs
    :param total_node_list: (list of str) the node list of the whole large job
    :param ppn: (int) number of procesors per node
    :return: (list of list) NODELISTs
    '''
    if serial_mode:
        if total_node_list:
            orig_node_list = sorted(list(set(total_node_list)))
            nnodes = len(orig_node_list)
            job_per_node = num_rockets/nnodes
            if job_per_node*nnodes != num_rockets:
                raise ValueError("can't allocate processes, {} can't be divided by {}".format(num_rockets, nnodes))
            sub_nproc_list = [1] * num_rockets
            node_lists = [[node] for node in orig_node_list * job_per_node]
        else:
            sub_nproc_list = [1] * num_rockets
            node_lists = [None] * num_rockets
    else:
        if total_node_list:
            orig_node_list = sorted(list(set(total_node_list)))
            nnodes = len(orig_node_list)
            sub_nnodes = nnodes/num_rockets
            if sub_nnodes*num_rockets != nnodes:
                raise ValueError("can't allocate nodes, {} can't be divided by {}".format(nnodes, num_rockets))
            sub_nproc_list = [sub_nnodes * ppn] * num_rockets
            node_lists = [orig_node_list[i:i+sub_nnodes] for i in range(0, nnodes, sub_nnodes)]
        else:
            sub_nproc_list = [ppn] * num_rockets
            node_lists = [None] * num_rockets
    return node_lists, sub_nproc_list


def launch_job_packing_processes(launchpad, fworker, loglvl, nlaunches,
                                 num_rockets, sleep_time,
                                 total_node_list=None, ppn=24, serial_mode=False):
    '''
    Launch the jobs in the job packing mode.
    :param fworker: (FWorker) object
    :param launchpad_file: (str) path to launchpad file
    :param loglvl: (str) level at which to output logs
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param num_rockets: (int) number of sub jobs
    :param sleep_time: (int) secs to sleep between rapidfire loop iterations
    :return:
    '''
    node_lists, sub_nproc_list = split_node_lists(num_rockets, total_node_list, ppn, serial_mode)
    # create dataserver
    ds = DataServer.setup(launchpad)
    port = ds.address[1]
    # launch rapidfire processes
    processes = launch_rapidfire_processes(fworker, nlaunches, sleep_time, loglvl,
                                           port, node_lists, sub_nproc_list)

    # start pinging service
    ping_stop = threading.Event()
    ping_thread = threading.Thread(target=ping_launch_jp, args=(port, ping_stop))
    ping_thread.start()

    # wait for completion
    for p in processes:
        p.join()
    ping_stop.set()
    ping_thread.join()
    ds.shutdown()