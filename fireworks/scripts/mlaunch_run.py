from argparse import ArgumentParser
from multiprocessing.managers import BaseManager
from multiprocessing import Process
from fireworks.core.fw_config import FWConfig
import os
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import rapidfire


"""
A runnable script to launch Job Packing Rockets (a command-line interface to rocket_launcher.py)
"""
__author__ = 'Xiaohui'
__copyright__ = 'Copyright 2013, The Electrolyte Genome Project'
__version__ = '0.1'
__maintainer__ = 'Xiaohui Qu'
__email__ = 'xqu@lbl.gov'
__date__ = 'Aug 19, 2013'


class PackingManager(BaseManager):
    pass

def create_launchpad(launchpad_file):
    if launchpad_file:
        launchpad = LaunchPad.from_file(args.launchpad_file)
    else:
        launchpad = LaunchPad(strm_lvl=args.loglvl)
    return launchpad

def manager_initializer():
    fw_conf = FWConfig()
    fw_conf.MULTIPROCESSING = None # don't confuse the server process

def run_manager_server(lauchpad_file, port, password):
    PackingManager.register('LaunchPad', callable=lambda: create_launchpad(lauchpad_file))
    m = PackingManager(address=('127.0.0.1', port), authkey=password)
    m.start(initializer=manager_initializer)
    return m

def rapidfire_process(fworker, nlaunches, sleep, loglvl, port, password, node_list):
    fw_conf = FWConfig()
    fw_conf.MULTIPROCESSING = True
    fw_conf.PACKING_MANAGER_PORT = port
    fw_conf.PACKING_MANAGER_PASSWORD = password
    m = PackingManager()
    m.connect()
    launchpad = m.LaunchPad()
    rapidfire(launchpad, fworker, None, nlaunches, -1, sleep, loglvl)

def launch_rapidfire_processes(fworker, nlaunches, sleep, loglvl, port, password, node_lists):
    processes = [Process(target=rapidfire_process, args=(fworker, nlaunches, sleep, loglvl, port, password, nl))
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
    parser._add_action('--num_rockets', help='the numbers of sub jobs to split into', default=2, type=int)

    args = parser.parse_args()

    if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
        args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

    if not args.fworker_file and os.path.exists(os.path.join(args.config_dir, 'my_fworker.yaml')):
        args.fworker_file = os.path.join(args.config_dir, 'my_fworker.yaml')

    args.loglvl = 'CRITICAL' if args.silencer else args.loglvl

    m = run_manager_server(args.launchpad_file, args.port, args.password)

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
    print '?'*20