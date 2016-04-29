# coding: utf-8

from __future__ import unicode_literals

"""
This module contains methods for launching several Rockets in a parallel environment
"""

from multiprocessing import Process
import os
import threading
import time
from fireworks.fw_config import FWData, PING_TIME_SECS, DS_PASSWORD
from fireworks.core.rocket_launcher import rapidfire
from fireworks.utilities.fw_utilities import DataServer


__author__ = 'Xiaohui Qu, Anubhav Jain'
__copyright__ = 'Copyright 2013, The Material Project & The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Aug 19, 2013'


def ping_multilaunch(port, stop_event):
    """
    A single manager to ping all launches during multiprocess launches

    :param port: (int) Listening port number of the DataServer
    :param stop_event: (Thread.Event) stop event
    """

    ds = DataServer(address=('127.0.0.1', port), authkey=DS_PASSWORD)
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

        stop_event.wait(PING_TIME_SECS)


def rapidfire_process(fworker, nlaunches, sleep, loglvl, port, node_list, sub_nproc, timeout):
    """
    Initializes shared data with multiprocessing parameters and starts a rapidfire

    :param fworker: (FWorker) object
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number of the shared object manage
    :param password: (str) security password to access the server
    :param node_list: ([str]) computer node list
    :param sub_nproc: (int) number of processors of the sub job
    :param timeout: (int) # of seconds after which to stop the rapidfire process
    """
    ds = DataServer(address=('127.0.0.1', port), authkey=DS_PASSWORD)
    ds.connect()
    launchpad = ds.LaunchPad()
    FWData().DATASERVER = ds
    FWData().MULTIPROCESSING = True
    FWData().NODE_LIST = node_list
    FWData().SUB_NPROCS = sub_nproc
    rapidfire(launchpad, fworker=fworker, m_dir=None, nlaunches=nlaunches,
              max_loops=-1, sleep_time=sleep, strm_lvl=loglvl, timeout=timeout)


def start_rockets(fworker, nlaunches, sleep, loglvl, port, node_lists, sub_nproc_list, timeout=None):
    """
    Create each sub job and start a rocket launch in each one

    :param fworker: (FWorker) object
    :param nlaunches: nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param sleep: (int) secs to sleep between rapidfire loop iterations
    :param loglvl: (str) level at which to output logs to stdout
    :param port: (int) Listening port number
    :param node_lists: ([str]) computer node list
    :param sub_nproc_list: ([int]) list of the number of the process of sub jobs
    :param timeout: (int) # of seconds after which to stop the rapidfire process
    :return: ([multiprocessing.Process]) all the created processes
    """

    processes = [Process(target=rapidfire_process, args=(fworker, nlaunches, sleep, loglvl, port, nl, sub_nproc, timeout))
                 for nl, sub_nproc in zip(node_lists, sub_nproc_list)]
    for p in processes:
        p.start()
        time.sleep(0.15)
    return processes


def split_node_lists(num_jobs, total_node_list=None, ppn=24):
    """
    Parse node list and processor list from nodefile contents

    :param num_jobs: (int) number of sub jobs
    :param total_node_list: (list of str) the node list of the whole large job
    :param ppn: (int) number of procesors per node
    :return: (([int],[int])) the node list and processor list for each job
    """
    if total_node_list:
        orig_node_list = sorted(list(set(total_node_list)))
        nnodes = len(orig_node_list)
        if nnodes%num_jobs != 0:
            raise ValueError("can't allocate nodes, {} can't be divided by {}".format(nnodes, num_jobs))
        sub_nnodes = nnodes/num_jobs
        sub_nproc_list = [sub_nnodes * ppn] * num_jobs
        node_lists = [orig_node_list[i:i+sub_nnodes] for i in range(0, nnodes, sub_nnodes)]
    else:
        sub_nproc_list = [ppn] * num_jobs
        node_lists = [None] * num_jobs
    return node_lists, sub_nproc_list


def launch_multiprocess(launchpad, fworker, loglvl, nlaunches, num_jobs, sleep_time,
                        total_node_list=None, ppn=1, timeout=None):
    """
    Launch the jobs in the job packing mode.
    :param launchpad: (LaunchPad) object
    :param fworker: (FWorker) object
    :param loglvl: (str) level at which to output logs
    :param nlaunches: (int) 0 means 'until completion', -1 or "infinite" means to loop forever
    :param num_jobs: (int) number of sub jobs
    :param sleep_time: (int) secs to sleep between rapidfire loop iterations
    :param total_node_list: ([str]) contents of NODEFILE (doesn't affect execution)
    :param ppn: (int) processors per node (doesn't affect execution)
    :param timeout: (int) # of seconds after which to stop the rapidfire process
    """
    # parse node file contents
    node_lists, sub_nproc_list = split_node_lists(num_jobs, total_node_list, ppn)

    # create shared dataserver
    ds = DataServer.setup(launchpad)
    port = ds.address[1]

    # launch rapidfire processes
    processes = start_rockets(fworker, nlaunches, sleep_time, loglvl, port, node_lists,
                              sub_nproc_list, timeout=timeout)

    # start pinging service
    ping_stop = threading.Event()
    ping_thread = threading.Thread(target=ping_multilaunch, args=(port, ping_stop))
    ping_thread.start()

    # wait for completion
    for p in processes:
        p.join()
    ping_stop.set()
    ping_thread.join()
    ds.shutdown()
