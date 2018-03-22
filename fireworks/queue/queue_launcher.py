# coding: utf-8

from __future__ import unicode_literals

"""
This module is used to submit jobs to a queue on a cluster. It can submit a single job, or
if used in "rapid-fire" mode, can submit multiple jobs within a directory structure.
The details of job submission and queue communication are handled using Queueadapter,
which specifies a QueueAdapter as well as desired properties of the submit script.
"""

import os
import glob
import time
from datetime import datetime

from monty.os import cd, makedirs_p

from fireworks.core.fworker import FWorker
from fireworks.utilities.fw_serializers import load_object
from fireworks.utilities.fw_utilities import get_fw_logger, log_exception, create_datestamp_dir, get_slug
from fireworks.fw_config import SUBMIT_SCRIPT_NAME, ALWAYS_CREATE_NEW_BLOCK, QUEUE_RETRY_ATTEMPTS, \
    QUEUE_UPDATE_INTERVAL, QSTAT_FREQUENCY, RAPIDFIRE_SLEEP_SECS, QUEUE_JOBNAME_MAXLEN

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


def launch_rocket_to_queue(launchpad, fworker, qadapter, launcher_dir='.', reserve=False,
                           strm_lvl='INFO', create_launcher_dir=False, fill_mode=False,
                           fw_id=None):
    """
    Submit a single job to the queue.

    Args:
        launchpad (LaunchPad)
        fworker (FWorker)
        qadapter (QueueAdapterBase)
        launcher_dir (str): The directory where to submit the job
        reserve (bool): Whether to queue in reservation mode
        strm_lvl (str): level at which to stream log messages
        create_launcher_dir (bool): Whether to create a subfolder launcher+timestamp, if needed
        fill_mode (bool): whether to submit jobs even when there is nothing to run
            (only in non-reservation mode)
        fw_id (int): specific fw_id to reserve (reservation mode only)
    """
    fworker = fworker if fworker else FWorker()
    launcher_dir = os.path.abspath(launcher_dir)
    l_logger = get_fw_logger('queue.launcher', l_dir=launchpad.logdir, stream_level=strm_lvl)

    l_logger.debug('getting queue adapter')
    qadapter = load_object(qadapter.to_dict())  # make a defensive copy, mainly for reservation mode

    fw, launch_id = None, None  # only needed in reservation mode

    if not os.path.exists(launcher_dir):
        raise ValueError('Desired launch directory {} does not exist!'.format(launcher_dir))

    if '--offline' in qadapter['rocket_launch'] and not reserve:
        raise ValueError("Must use reservation mode (-r option) of qlaunch "
                         "when using offline option of rlaunch!!")

    if reserve and 'singleshot' not in qadapter.get('rocket_launch', ''):
        raise ValueError('Reservation mode of queue launcher only works for singleshot Rocket Launcher!')

    if fill_mode and reserve:
        raise ValueError("Fill_mode cannot be used in conjunction with reserve mode!")

    if fw_id and not reserve:
        raise ValueError("qlaunch for specific fireworks may only be used in reservation mode.")

    if fill_mode or launchpad.run_exists(fworker):
        launch_id = None
        try:
            if reserve:
                if fw_id:
                    l_logger.debug('finding a FW to reserve...')
                fw, launch_id = launchpad.reserve_fw(fworker, launcher_dir, fw_id=fw_id)
                if not fw:
                    l_logger.info('No jobs exist in the LaunchPad for submission to queue!')
                    return False
                l_logger.info('reserved FW with fw_id: {}'.format(fw.fw_id))

                # update qadapter job_name based on FW name
                job_name = get_slug(fw.name)[0:QUEUE_JOBNAME_MAXLEN]
                qadapter.update({'job_name': job_name})

                if '_queueadapter' in fw.spec:
                    l_logger.debug('updating queue params using Firework spec..')
                    qadapter.update(fw.spec['_queueadapter'])

                # reservation mode includes --fw_id in rocket launch
                qadapter['rocket_launch'] += ' --fw_id {}'.format(fw.fw_id)

                # update launcher_dir if _launch_dir is selected in reserved fw
                if '_launch_dir' in fw.spec:
                    fw_launch_dir = os.path.expandvars(fw.spec['_launch_dir'])

                    if not os.path.isabs(fw_launch_dir):
                        fw_launch_dir = os.path.join(launcher_dir, fw_launch_dir)

                    launcher_dir = fw_launch_dir

                    makedirs_p(launcher_dir)

                    launchpad.change_launch_dir(launch_id, launcher_dir)
                elif create_launcher_dir:
                    # create launcher_dir
                    launcher_dir = create_datestamp_dir(launcher_dir, l_logger, prefix='launcher_')
                    launchpad.change_launch_dir(launch_id, launcher_dir)

            elif create_launcher_dir:
                # create launcher_dir
                launcher_dir = create_datestamp_dir(launcher_dir, l_logger, prefix='launcher_')

            # move to the launch directory
            l_logger.info('moving to launch_dir {}'.format(launcher_dir))

            with cd(launcher_dir):

                if '--offline' in qadapter['rocket_launch']:
                    setup_offline_job(launchpad, fw, launch_id)

                l_logger.debug('writing queue script')
                with open(SUBMIT_SCRIPT_NAME, 'w') as f:
                    queue_script = qadapter.get_script_str(launcher_dir)
                    f.write(queue_script)

                l_logger.info('submitting queue script')
                reservation_id = qadapter.submit_to_queue(SUBMIT_SCRIPT_NAME)
                if not reservation_id:
                    raise RuntimeError('queue script could not be submitted, check queue '
                                       'script/queue adapter/queue server status!')
                elif reserve:
                    launchpad.set_reservation_id(launch_id, reservation_id)
            return reservation_id

        except:
            log_exception(l_logger, 'Error writing/submitting queue script!')
            if reserve and launch_id is not None:
                try:
                    l_logger.info('Un-reserving FW with fw_id, launch_id: {}, {}'.format(
                        fw.fw_id, launch_id))
                    launchpad.cancel_reservation(launch_id)
                    launchpad.forget_offline(launch_id)
                except:
                    log_exception(l_logger, 'Error unreserving FW with fw_id {}'.format(fw.fw_id))

            return False

    else:
        l_logger.info('No jobs exist in the LaunchPad for submission to queue!')
        return None  # note: this is a hack (rather than False) to indicate a soft failure to rapidfire()


def rapidfire(launchpad, fworker, qadapter, launch_dir='.', nlaunches=0, njobs_queue=0,
              njobs_block=500, sleep_time=None, reserve=False, strm_lvl='INFO', timeout=None,
              fill_mode=False):
    """
    Submit many jobs to the queue.

    Args:
        launchpad (LaunchPad)
        fworker (FWorker)
        qadapter (QueueAdapterBase)
        launch_dir (str): directory where we want to write the blocks
        nlaunches (int): total number of launches desired; "infinite" for loop, 0 for one round
        njobs_queue (int): stops submitting jobs when njobs_queue jobs are in the queue, 0 for no limit
        njobs_block (int): automatically write a new block when njobs_block jobs are in a single block
        sleep_time (int): secs to sleep between rapidfire loop iterations
        reserve (bool): Whether to queue in reservation mode
        strm_lvl (str): level at which to stream log messages
        timeout (int): # of seconds after which to stop the rapidfire process
        fill_mode (bool): whether to submit jobs even when there is nothing to run (only in
            non-reservation mode)
    """

    sleep_time = sleep_time if sleep_time else RAPIDFIRE_SLEEP_SECS
    launch_dir = os.path.abspath(launch_dir)
    nlaunches = -1 if nlaunches == 'infinite' else int(nlaunches)
    l_logger = get_fw_logger('queue.launcher', l_dir=launchpad.logdir, stream_level=strm_lvl)

    # make sure launch_dir exists:
    if not os.path.exists(launch_dir):
        raise ValueError('Desired launch directory {} does not exist!'.format(launch_dir))

    num_launched = 0
    start_time = datetime.now()

    try:
        l_logger.info('getting queue adapter')

        prev_blocks = sorted(glob.glob(os.path.join(launch_dir, 'block_*')), reverse=True)
        if prev_blocks and not ALWAYS_CREATE_NEW_BLOCK:
            block_dir = os.path.abspath(os.path.join(launch_dir, prev_blocks[0]))
            l_logger.info('Found previous block, using {}'.format(block_dir))
        else:
            block_dir = create_datestamp_dir(launch_dir, l_logger)

        while True:
            # get number of jobs in queue
            jobs_in_queue = _get_number_of_jobs_in_queue(qadapter, njobs_queue, l_logger)
            job_counter = 0  # this is for QSTAT_FREQUENCY option

            while (launchpad.run_exists(fworker) or
                   (fill_mode and not reserve)):

                if timeout and (datetime.now() - start_time).total_seconds() >= timeout:
                    l_logger.info("Timeout reached.")
                    break

                if njobs_queue and jobs_in_queue >= njobs_queue:
                    l_logger.info("Jobs in queue ({}) meets/exceeds "
                                  "maximum allowed ({})".format(jobs_in_queue,
                                                                njobs_queue))
                    break

                l_logger.info('Launching a rocket!')

                # switch to new block dir if it got too big
                if _njobs_in_dir(block_dir) >= njobs_block:
                    l_logger.info('Block got bigger than {} jobs.'.format(njobs_block))
                    block_dir = create_datestamp_dir(launch_dir, l_logger)

                # launch a single job
                return_code = launch_rocket_to_queue(launchpad, fworker, qadapter, block_dir, reserve,
                                              strm_lvl, True, fill_mode)
                if return_code is None:
                    l_logger.info('No READY jobs detected...')
                    break
                elif not return_code:
                    raise RuntimeError("Launch unsuccessful!")
                num_launched += 1
                if nlaunches > 0 and num_launched == nlaunches:
                    l_logger.info('Launched allowed number of '
                                  'jobs: {}'.format(num_launched))
                    break
                # wait for the queue system to update
                l_logger.info('Sleeping for {} seconds...zzz...'.format(QUEUE_UPDATE_INTERVAL))
                time.sleep(QUEUE_UPDATE_INTERVAL)
                jobs_in_queue += 1
                job_counter += 1
                if job_counter % QSTAT_FREQUENCY == 0:
                    job_counter = 0
                    jobs_in_queue = _get_number_of_jobs_in_queue(qadapter, njobs_queue, l_logger)

            if (nlaunches > 0 and num_launched == nlaunches) or \
                    (timeout and (datetime.now() - start_time).total_seconds()
                     >= timeout) or (nlaunches == 0 and not launchpad.future_run_exists(fworker)):
                break

            l_logger.info('Finished a round of launches, sleeping for {} secs'.format(sleep_time))
            time.sleep(sleep_time)
            l_logger.info('Checking for Rockets to run...')

    except:
        log_exception(l_logger, 'Error with queue launcher rapid fire!')


def _njobs_in_dir(block_dir):
    """
    Internal method to count the number of jobs inside a block

    Args:
        block_dir: (str) the block directory we want to count the jobs in

    Return:
        (int)
    """
    return len(glob.glob('%s/launcher_*' % os.path.abspath(block_dir)))


def _get_number_of_jobs_in_queue(qadapter, njobs_queue, l_logger):
    """
    Internal method to get the number of jobs in the queue using the given job params.
    In case of failure, automatically retries at certain intervals...

    Args:
        qadapter (QueueAdapter)
        njobs_queue (int): The desired maximum number of jobs in the queue
        l_logger (logger): A logger to put errors/info/warnings/etc.

    Return:
        (int)
    """
    RETRY_INTERVAL = 30  # initial retry in 30 sec upon failure

    for i in range(QUEUE_RETRY_ATTEMPTS):
        try:
            jobs_in_queue = qadapter.get_njobs_in_queue()
            if jobs_in_queue is not None:
                l_logger.info('{} jobs in queue. '
                              'Maximum allowed by user: {}'.format(jobs_in_queue, njobs_queue))
                return jobs_in_queue
        except:
            log_exception(l_logger, 'Could not get number of jobs in queue! '
                                    'Sleeping {} secs...zzz...'.format(RETRY_INTERVAL))
        time.sleep(RETRY_INTERVAL)
        RETRY_INTERVAL *= 2

    raise RuntimeError('Unable to determine number of jobs in queue, '
                       'check queue adapter and queue server status!')


def setup_offline_job(launchpad, fw, launch_id):
    # separate this function out for reuse in unit testing
    fw.to_file("FW.json")
    with open('FW_offline.json', 'w') as f:
        f.write('{"launch_id":%s}' % launch_id)
    launchpad.add_offline_run(launch_id, fw.fw_id, fw.name)
