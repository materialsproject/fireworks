"""
This module contains methods for launching several Rockets in a parallel environment
"""

import os
import threading
import time
from multiprocessing import Manager, Process

from fireworks.core.rocket_launcher import rapidfire
from fireworks.fw_config import (
    DS_PASSWORD,
    PING_TIME_SECS,
    RAPIDFIRE_SLEEP_SECS,
    FWData,
)
from fireworks.utilities.fw_utilities import (
    DataServer,
    get_fw_logger,
    get_my_host,
    log_multi,
)

__author__ = "Xiaohui Qu, Anubhav Jain"
__copyright__ = "Copyright 2013, The Material Project & The Electrolyte Genome Project"
__version__ = "0.1"
__maintainer__ = "Xiaohui Qu"
__email__ = "xqu@lbl.gov"
__date__ = "Aug 19, 2013"


def ping_multilaunch(port, stop_event):
    """
    A single manager to ping all launches during multiprocess launches

    Args:
        port (int): Listening port number of the DataServer
        stop_event (Thread.Event): stop event
    """
    ds = DataServer(address=("127.0.0.1", port), authkey=DS_PASSWORD)
    ds.connect()
    fd = FWData()

    lp = ds.LaunchPad()
    while not stop_event.is_set():
        for pid, lid in fd.Running_IDs.items():
            if lid:
                try:
                    os.kill(pid, 0)  # throws OSError if the process is dead
                    lp.ping_launch(lid)
                except OSError:  # means this process is dead!
                    fd.Running_IDs[pid] = None

        stop_event.wait(PING_TIME_SECS)


def rapidfire_process(
    fworker, nlaunches, sleep, loglvl, port, node_list, sub_nproc, timeout, running_ids_dict, local_redirect
):
    """
    Initializes shared data with multiprocessing parameters and starts a rapidfire.

    Args:
        fworker (FWorker): object
        nlaunches (int): 0 means 'until completion', -1 or "infinite" means to loop forever
        sleep (int): secs to sleep between rapidfire loop iterations
        loglvl (str): level at which to output logs to stdout
        port (int): Listening port number of the shared object manage
        password (str): security password to access the server
        node_list ([str]): computer node list
        sub_nproc (int): number of processors of the sub job
        timeout (int): # of seconds after which to stop the rapidfire process
        local_redirect (bool): redirect standard input and output to local file
    """
    ds = DataServer(address=("127.0.0.1", port), authkey=DS_PASSWORD)
    ds.connect()
    launchpad = ds.LaunchPad()
    FWData().DATASERVER = ds
    FWData().MULTIPROCESSING = True
    FWData().NODE_LIST = node_list
    FWData().SUB_NPROCS = sub_nproc
    FWData().Running_IDs = running_ids_dict
    sleep_time = sleep if sleep else RAPIDFIRE_SLEEP_SECS
    l_dir = launchpad.get_logdir() if launchpad else None
    l_logger = get_fw_logger("rocket.launcher", l_dir=l_dir, stream_level=loglvl)
    rapidfire(
        launchpad,
        fworker=fworker,
        m_dir=None,
        nlaunches=nlaunches,
        max_loops=-1,
        sleep_time=sleep,
        strm_lvl=loglvl,
        timeout=timeout,
        local_redirect=local_redirect,
    )
    while nlaunches == 0:
        time.sleep(1.5)  # wait for LaunchPad to be initialized
        launch_ids = FWData().Running_IDs.values()
        live_ids = list(set(launch_ids) - {None})
        if len(live_ids) > 0:
            # Some other sub jobs are still running
            log_multi(l_logger, f"Sleeping for {sleep_time} secs before resubmit sub job")
            time.sleep(sleep_time)
            log_multi(l_logger, "Resubmit sub job")
            rapidfire(
                launchpad,
                fworker=fworker,
                m_dir=None,
                nlaunches=nlaunches,
                max_loops=-1,
                sleep_time=sleep,
                strm_lvl=loglvl,
                timeout=timeout,
                local_redirect=local_redirect,
            )
        else:
            break
    log_multi(l_logger, "Sub job finished")


def start_rockets(
    fworker,
    nlaunches,
    sleep,
    loglvl,
    port,
    node_lists,
    sub_nproc_list,
    timeout=None,
    running_ids_dict=None,
    local_redirect=False,
):
    """
    Create each sub job and start a rocket launch in each one

    Args:
        fworker (FWorker): object
        nlaunches (int): 0 means 'until completion', -1 or "infinite" means to loop forever
        sleep (int): secs to sleep between rapidfire loop iterations
        loglvl (str): level at which to output logs to stdout
        port (int): Listening port number
        node_lists ([str]): computer node list
        sub_nproc_list ([int]): list of the number of the process of sub jobs
        timeout (int): # of seconds after which to stop the rapidfire process
        running_ids_dict (dict): Shared dict between process to record IDs
        local_redirect (bool): redirect standard input and output to local file
    Returns:
        ([multiprocessing.Process]) all the created processes
    """
    processes = [
        Process(
            target=rapidfire_process,
            args=(fworker, nlaunches, sleep, loglvl, port, nl, sub_nproc, timeout, running_ids_dict, local_redirect),
        )
        for nl, sub_nproc in zip(node_lists, sub_nproc_list)
    ]
    for p in processes:
        p.start()
        time.sleep(0.15)
    return processes


def split_node_lists(num_jobs, total_node_list=None, ppn=24):
    """
    Parse node list and processor list from nodefile contents

    Args:
        num_jobs (int): number of sub jobs
        total_node_list (list of str): the node list of the whole large job
        ppn (int): number of procesors per node

    Returns:
        (([int],[int])) the node list and processor list for each job
    """
    if total_node_list:
        orig_node_list = sorted(list(set(total_node_list)))
        nnodes = len(orig_node_list)
        if nnodes % num_jobs != 0:
            raise ValueError(f"can't allocate nodes, {nnodes} can't be divided by {num_jobs}")
        sub_nnodes = nnodes // num_jobs
        sub_nproc_list = [sub_nnodes * ppn] * num_jobs
        node_lists = [orig_node_list[i : i + sub_nnodes] for i in range(0, nnodes, sub_nnodes)]
    else:
        sub_nproc_list = [ppn] * num_jobs
        node_lists = [None] * num_jobs
    return node_lists, sub_nproc_list


# TODO: why is loglvl a required parameter??? Also nlaunches and sleep_time could have a sensible default??
def launch_multiprocess(
    launchpad,
    fworker,
    loglvl,
    nlaunches,
    num_jobs,
    sleep_time,
    total_node_list=None,
    ppn=1,
    timeout=None,
    exclude_current_node=False,
    local_redirect=False,
):
    """
    Launch the jobs in the job packing mode.

    Args:
        launchpad (LaunchPad)
        fworker (FWorker)
        loglvl (str): level at which to output logs
        nlaunches (int): 0 means 'until completion', -1 or "infinite" means to loop forever
        num_jobs(int): number of sub jobs
        sleep_time (int): secs to sleep between rapidfire loop iterations
        total_node_list ([str]): contents of NODEFILE (doesn't affect execution)
        ppn (int): processors per node (doesn't affect execution)
        timeout (int): # of seconds after which to stop the rapidfire process
        exclude_current_node: Don't use the script launching node as a compute node
        local_redirect (bool): redirect standard input and output to local file
    """
    # parse node file contents
    if exclude_current_node:
        host = get_my_host()
        l_dir = launchpad.get_logdir() if launchpad else None
        l_logger = get_fw_logger("rocket.launcher", l_dir=l_dir, stream_level=loglvl)
        if host in total_node_list:
            log_multi(l_logger, f'Remove the current node "{host}" from compute node')
            total_node_list.remove(host)
        else:
            log_multi(l_logger, "The current node is not in the node list, keep the node list as is")
    node_lists, sub_nproc_list = split_node_lists(num_jobs, total_node_list, ppn)

    # create shared dataserver
    ds = DataServer.setup(launchpad)
    port = ds.address[1]

    manager = Manager()
    running_ids_dict = manager.dict()
    # launch rapidfire processes
    processes = start_rockets(
        fworker,
        nlaunches,
        sleep_time,
        loglvl,
        port,
        node_lists,
        sub_nproc_list,
        timeout=timeout,
        running_ids_dict=running_ids_dict,
        local_redirect=local_redirect,
    )
    FWData().Running_IDs = running_ids_dict

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
