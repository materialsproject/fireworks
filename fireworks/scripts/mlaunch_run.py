from argparse import ArgumentParser
from fireworks.core.fw_config import FWConfig
import os
from fireworks.core.fworker import FWorker
from fireworks.core.job_packing import run_manager_server, split_node_lists, launch_rapidfire_processes


"""
A runnable script to launch Job Packing Rockets (a command-line interface to rocket_launcher.py)
"""
__author__ = 'Xiaohui'
__copyright__ = 'Copyright 2013, The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Aug 19, 2013'



def mlaunch():
    m_description = 'This program launches Job Packing Rockets. A Rocket grabs a job from the central database and ' \
                    'runs it.'

    parser = ArgumentParser(description=m_description)

    parser.add_argument('--nlaunches', help='num_launches (int or "infinite")', default=0)
    parser.add_argument('--sleep', help='sleep time between loops (secs)', default=None, type=int)

    parser.add_argument('-l', '--launchpad_file', help='path to launchpad file', default=FWConfig().LAUNCHPAD_LOC)
    parser.add_argument('-w', '--fworker_file', help='path to fworker file', default=FWConfig().FWORKER_LOC)
    parser.add_argument('-c', '--config_dir', help='path to a directory containing the config file (used if -l, -w unspecified)',
                        default=FWConfig().CONFIG_FILE_DIR)

    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('-s', '--silencer', help='shortcut to mute log messages', action='store_true')

    parser.add_argument('--port', help='shared object service internet port number', default=27015, type=int)
    parser.add_argument('--password', help='shared object service password', default='123')
    parser.add_argument('--num_rockets', help='the numbers of sub jobs to split into', default=2, type=int)

    args = parser.parse_args()

    if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
        args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

    if not args.fworker_file and os.path.exists(os.path.join(args.config_dir, 'my_fworker.yaml')):
        args.fworker_file = os.path.join(args.config_dir, 'my_fworker.yaml')

    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    m = run_manager_server(args.launchpad_file, args.loglvl, args.port, args.password)

    if args.fworker_file:
        fworker = FWorker.from_file(args.fworker_file)
    else:
        fworker = FWorker()

    node_lists = split_node_lists(args.num_rockets)

    processes = launch_rapidfire_processes(fworker, args.nlaunches, args.sleep, args.loglvl,
                                           args.port, args.password, node_lists)

    for p in processes:
        p.join()

    m.shutdown()


if __name__ == "__main__":
    mlaunch()