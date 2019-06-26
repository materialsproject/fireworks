# coding: utf-8

from __future__ import unicode_literals

"""
A runnable script for launching rockets (a command-line interface to queue_launcher.py)
"""

from argparse import ArgumentParser
import os
import sys
import time

try:
    import fabric
    if int(fabric.__version__.split('.')[0]) < 2:
        raise ImportError
except ImportError:
    HAS_FABRIC = False
else:
    HAS_FABRIC = True

from fireworks.fw_config import QUEUEADAPTER_LOC, CONFIG_FILE_DIR, FWORKER_LOC, LAUNCHPAD_LOC
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.queue.queue_launcher import rapidfire, launch_rocket_to_queue
from fireworks.utilities.fw_serializers import load_object_from_file

__authors__ = "Anubhav Jain, Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Jan 14, 2013"


def do_launch(args):
    if not args.launchpad_file and os.path.exists(
            os.path.join(args.config_dir, 'my_launchpad.yaml')):
        args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')
    elif not args.launchpad_file:
        args.launchpad_file = LAUNCHPAD_LOC

    if not args.fworker_file and os.path.exists(
            os.path.join(args.config_dir, 'my_fworker.yaml')):
        args.fworker_file = os.path.join(args.config_dir, 'my_fworker.yaml')
    elif not args.fworker_file:
        args.fworker_file = FWORKER_LOC

    if not args.queueadapter_file and os.path.exists(
            os.path.join(args.config_dir, 'my_qadapter.yaml')):
        args.queueadapter_file = os.path.join(args.config_dir, 'my_qadapter.yaml')
    elif not args.queueadapter_file:
        args.queueadapter_file = QUEUEADAPTER_LOC

    launchpad = LaunchPad.from_file(
        args.launchpad_file) if args.launchpad_file else LaunchPad(
        strm_lvl=args.loglvl)
    fworker = FWorker.from_file(
        args.fworker_file) if args.fworker_file else FWorker()
    queueadapter = load_object_from_file(args.queueadapter_file)
    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    if args.command == 'rapidfire':
        rapidfire(launchpad, fworker=fworker, qadapter=queueadapter, launch_dir=args.launch_dir,
                  nlaunches=args.nlaunches, njobs_queue=args.maxjobs_queue,
                  njobs_block=args.maxjobs_block, sleep_time=args.sleep,
                  reserve=args.reserve, strm_lvl=args.loglvl, timeout=args.timeout, fill_mode=args.fill_mode)
    else:
        launch_rocket_to_queue(launchpad, fworker, queueadapter,
                               args.launch_dir, args.reserve, args.loglvl, False, args.fill_mode, args.fw_id)

def qlaunch():
    m_description = 'This program is used to submit jobs to a queueing system. ' \
                    'Details of the job and queue interaction are handled by the ' \
                    'mandatory queue adapter file parameter. The "rapidfire" option ' \
                    'can be used to maintain a certain number of jobs in the queue by ' \
                    'specifying the n_loops parameter to a large number. If n_loops is ' \
                    'set to 1 (default) the queue launcher will quit after submitting ' \
                    'the desired number of jobs. For more help on rapid fire options, ' \
                    'use qlauncher.py rapidfire -h'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')
    single_parser = subparsers.add_parser('singleshot', help='launch a single rocket to the queue')
    rapid_parser = subparsers.add_parser('rapidfire', help='launch multiple rockets to the queue')

    parser.add_argument("-rh", "--remote_host", nargs="*",
                        help="Remote host to exec qlaunch. Right now, "
                             "only supports running from a config dir.")
    parser.add_argument("-rc", "--remote_config_dir",
                        nargs="+",
                        help="Remote config dir location(s). Defaults to "
                             "~/.fireworks. You can specify multiple "
                             "locations if you have multiple configurations "
                             "on the same cluster e.g., multiple queues or FireWorkers. "
                             "Note that this may have to come before the -ru"
                             "argument (or other single arg) options as "
                             "argparse may not be able to find "
                             "the find command while it consumes args.",
                        default=["~/.fireworks"])
    parser.add_argument("-ru", "--remote_user",
                        help="Username to login to remote host.")
    parser.add_argument("-rp", "--remote_password",
                        help="Password for remote host (if necessary). For "
                             "best operation, it is recommended that you do "
                             "passwordless ssh.")
    parser.add_argument("-rsh", "--remote_shell",
                        help="Shell command to use on remote host for running submission.",
                        default='/bin/bash -l -c')

    parser.add_argument("-rkf", "--remote_keyfile",
                        help="SSH keyfile for connecting to remote hosts",
                        type=str, default=None)

    parser.add_argument("-rs", "--remote_setup",
                        help="Setup the remote config dir using files in "
                             "the directory specified by -c.",
                        action="store_true")
    parser.add_argument("-d", "--daemon",
                        help="Daemon mode. Command is repeated every x "
                             "seconds. Defaults to 0, which means non-daemon "
                             "mode.",
                        type=int,
                        default=0)
    parser.add_argument('--launch_dir', help='directory to launch the job / rapid-fire', default='.')
    parser.add_argument('--logdir', help='path to a directory for logging', default=None)
    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('-s', '--silencer', help='shortcut to mute log messages', action='store_true')
    parser.add_argument('-r', '--reserve', help='reserve a fw', action='store_true')
    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file')
    parser.add_argument('-w', '--fworker_file', help='path to fworker file')
    parser.add_argument('-q', '--queueadapter_file', help='path to queueadapter file')
    parser.add_argument('-c', '--config_dir',
                        help='path to a directory containing the config file (used if -l, -w, -q unspecified)',
                        default=CONFIG_FILE_DIR)
    parser.add_argument('-fm', '--fill_mode', help='launch queue submissions even when there is nothing to run',
                        action='store_true')

    rapid_parser.add_argument('-m', '--maxjobs_queue',
                              help='maximum jobs to keep in queue for this user', default=0,
                              type=int)
    rapid_parser.add_argument('-b', '--maxjobs_block',
                              help='maximum jobs to put in a block',
                              default=500, type=int)
    rapid_parser.add_argument('--nlaunches',
                              help='num_launches (int or "infinite"; default 0 is all jobs in DB)',
                              default=0)
    rapid_parser.add_argument('--timeout', help='timeout (secs) after which to quit (default None)',
                              default=None, type=int)
    rapid_parser.add_argument('--sleep', help='sleep time between loops', default=None, type=int)
    
    single_parser.add_argument('-f', '--fw_id', help='specific fw_id to run in reservation mode', 
                               default=None, type=int)

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
        # This supports bash autocompletion. To enable this, pip install
        # argcomplete, activate global completion, or add
        #      eval "$(register-python-argcomplete qlaunch)"
        # into your .bash_profile or .bashrc
    except ImportError:
        pass

    args = parser.parse_args()

    if args.remote_host and not HAS_FABRIC:
        print("Remote options require the Fabric package v2+ to be installed!")
        sys.exit(-1)

    if args.remote_setup and args.remote_host:
        for h in args.remote_host:
            conf = fabric.Configuration()
            conf.run.shell = args.remote_shell
            connect_kwargs = {'password': args.remote_password}
            if args.remote_keyfile:
                connect_kwargs["key_filename"] = args.remote_keyfile
            with fabric.Connection(
                    host=h,
                    user=args.remote_user,
                    config=fabric.Config({'run': {'shell': args.remote_shell}}),
                    connect_kwargs=connect_kwargs) as conn:
                for r in args.remote_config_dir:
                    r = os.path.expanduser(r)
                    conn.run("mkdir -p {}".format(r))
                    for f in os.listdir(args.config_dir):
                        if os.path.isfile(f):
                            conn.put(f, os.path.join(r, f))
    non_default = []
    for k in ["maxjobs_queue", "maxjobs_block", "nlaunches", "sleep"]:
        v = getattr(args, k, None)
        if v != rapid_parser.get_default(k):
            non_default.append("--{} {}".format(k, v))
    non_default = " ".join(non_default)

    pre_non_default = []
    for k in ["silencer", "reserve"]:
        v = getattr(args, k, None)
        if v:
            pre_non_default.append("--%s" % k)
    pre_non_default = " ".join(pre_non_default)

    interval = args.daemon
    while True:
        if args.remote_host:
            connect_kwargs = {'password': args.remote_password}
            if args.remote_keyfile:
                connect_kwargs["key_filename"] = args.remote_keyfile
            for h in args.remote_host:
                with fabric.Connection(
                        host=h,
                        user=args.remote_user,
                        config=fabric.Config({'run': {'shell': args.remote_shell}}),
                        connect_kwargs=connect_kwargs) as conn:
                    for r in args.remote_config_dir:
                        r = os.path.expanduser(r)
                        with conn.cd(r):
                            conn.run("qlaunch {} {} {}".format(
                                pre_non_default, args.command, non_default))
        else:
            do_launch(args)
        if interval > 0:
            print("Next run in {} seconds... Press Ctrl-C to exit at any "
                  "time.".format(interval))
            time.sleep(args.daemon)
        else:
            break


if __name__ == '__main__':
    qlaunch()
