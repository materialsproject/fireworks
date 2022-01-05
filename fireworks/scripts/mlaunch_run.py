"""
A runnable script to launch Job Packing (Multiple) Rockets
"""

import os
from argparse import ArgumentParser

from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.features.multi_launcher import launch_multiprocess
from fireworks.fw_config import CONFIG_FILE_DIR, FWORKER_LOC, LAUNCHPAD_LOC

__author__ = "Xiaohui Qu, Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project & Electrolyte Genome Project"
__version__ = "0.1"
__maintainer__ = "Xiaohui Qu"
__email__ = "xqu@lbl.gov"
__date__ = "Aug 19, 2013"


def mlaunch():

    m_description = "This program launches multiple Rockets simultaneously"

    parser = ArgumentParser(description=m_description)

    parser.add_argument("num_jobs", help="the number of jobs to run in parallel", type=int)
    parser.add_argument(
        "--nlaunches",
        help="number of FireWorks to run in series per parallel job "
        '(int or "infinite"; default 0 is all jobs in DB)',
        default=0,
    )
    parser.add_argument(
        "--sleep", help="sleep time between loops in infinite launch mode (secs)", default=None, type=int
    )
    parser.add_argument("--timeout", help="timeout (secs) after which to quit (default None)", default=None, type=int)

    parser.add_argument("-l", "--launchpad_file", help="path to launchpad file", default=LAUNCHPAD_LOC)
    parser.add_argument("-w", "--fworker_file", help="path to fworker file", default=FWORKER_LOC)
    parser.add_argument(
        "-c",
        "--config_dir",
        help="path to a directory containing the config file (used if -l, -w unspecified)",
        default=CONFIG_FILE_DIR,
    )

    parser.add_argument("--loglvl", help="level to print log messages", default="INFO")
    parser.add_argument("-s", "--silencer", help="shortcut to mute log messages", action="store_true")

    parser.add_argument(
        "--nodefile",
        help="nodefile name or environment variable name containing the node file name (for populating FWData only)",
        default=None,
        type=str,
    )
    parser.add_argument("--ppn", help="processors per node (for populating FWData only)", default=1, type=int)
    parser.add_argument(
        "--exclude_current_node", help="Don't use the script launching node as compute node", action="store_true"
    )

    try:
        import argcomplete

        argcomplete.autocomplete(parser)
        # This supports bash autocompletion. To enable this, pip install
        # argcomplete, activate global completion, or add
        #      eval "$(register-python-argcomplete mlaunch)"
        # into your .bash_profile or .bashrc
    except ImportError:
        pass

    args = parser.parse_args()

    if (
        not args.launchpad_file
        and args.config_dir
        and os.path.exists(os.path.join(args.config_dir, "my_launchpad.yaml"))
    ):
        args.launchpad_file = os.path.join(args.config_dir, "my_launchpad.yaml")

    if not args.fworker_file and args.config_dir and os.path.exists(os.path.join(args.config_dir, "my_fworker.yaml")):
        args.fworker_file = os.path.join(args.config_dir, "my_fworker.yaml")

    args.loglvl = "CRITICAL" if args.silencer else args.loglvl

    launchpad = LaunchPad.from_file(args.launchpad_file) if args.launchpad_file else LaunchPad(strm_lvl=args.loglvl)

    if args.fworker_file:
        fworker = FWorker.from_file(args.fworker_file)
    else:
        fworker = FWorker()

    total_node_list = None
    if args.nodefile:
        if args.nodefile in os.environ:
            args.nodefile = os.environ[args.nodefile]
        with open(args.nodefile) as f:
            total_node_list = [line.strip() for line in f.readlines()]

    launch_multiprocess(
        launchpad,
        fworker,
        args.loglvl,
        args.nlaunches,
        args.num_jobs,
        args.sleep,
        total_node_list,
        args.ppn,
        timeout=args.timeout,
        exclude_current_node=args.exclude_current_node,
    )


if __name__ == "__main__":
    mlaunch()
