"""A runnable script to launch Job Packing (Multiple) Rockets."""

from __future__ import annotations

import os
from argparse import ArgumentParser
from importlib import metadata
from typing import Sequence

from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.features.multi_launcher import launch_multiprocess
from fireworks.fw_config import CONFIG_FILE_DIR, FWORKER_LOC, LAUNCHPAD_LOC

from ._helpers import _validate_config_file_paths

__author__ = "Xiaohui Qu, Anubhav Jain"
__copyright__ = "Copyright 2013, The Materials Project & Electrolyte Genome Project"
__maintainer__ = "Xiaohui Qu"
__email__ = "xqu@lbl.gov"
__date__ = "Aug 19, 2013"


def mlaunch(argv: Sequence[str] | None = None) -> int:
    m_description = "This program launches multiple Rockets simultaneously"

    parser = ArgumentParser("mlaunch", description=m_description)

    fw_version = metadata.version("fireworks")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s v{fw_version}")

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

    args = parser.parse_args(argv)

    cfg_files_to_check = [
        ("launchpad", "-l", False, LAUNCHPAD_LOC),
        ("fworker", "-w", False, FWORKER_LOC),
    ]
    _validate_config_file_paths(args, cfg_files_to_check)

    args.loglvl = "CRITICAL" if args.silencer else args.loglvl

    launchpad = LaunchPad.from_file(args.launchpad_file) if args.launchpad_file else LaunchPad(strm_lvl=args.loglvl)

    fworker = FWorker.from_file(args.fworker_file) if args.fworker_file else FWorker()

    total_node_list = None
    if args.nodefile:
        if args.nodefile in os.environ:
            args.nodefile = os.environ[args.nodefile]
        with open(args.nodefile) as f:
            total_node_list = [line.strip() for line in f]

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

    return 0


if __name__ == "__main__":
    raise SystemExit(mlaunch())
