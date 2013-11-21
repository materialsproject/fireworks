#!/usr/bin/env python

"""
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
"""

from argparse import ArgumentParser
import os
import webbrowser
from pymongo import DESCENDING, ASCENDING
import time
from fireworks.core.fw_config import FWConfig
from fireworks.core.launchpad import LaunchPad
from fireworks.core.firework import Workflow, FireWork
import ast
import json
import datetime
from fireworks import __version__ as FW_VERSION
from fireworks import FW_INSTALL_DIR
from fireworks.user_objects.firetasks.script_task import ScriptTask
from fireworks.utilities.fw_serializers import DATETIME_HANDLER

__author__ = 'Anubhav Jain'
__credits__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 7, 2013'


def pw_check(ids, args):
    if len(ids) > FWConfig().PW_CHECK_NUM:
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')
        if not args.password:
            if raw_input('Are you sure? This will modify {} entries. (Y/N)'.format(len(ids)))[0].upper() == 'Y':
                args.password=datetime.datetime.now().strftime('%Y-%m-%d')
            else:
                raise ValueError('Operation aborted by user.')
        if args.password != m_password:
            raise ValueError("Modifying more than {} entries requires setting the --password parameter! (Today's date, e.g. 2012-02-25)".format(FWConfig().PW_CHECK_NUM))

    return ids


def parse_helper(lp, args, wf_mode=False):
    """
    Helper method to parse args that can take either id, name, state or query
    :param args:
    :return:
    """

    if args.fw_id and sum([bool(x) for x in [args.name, args.state, args.query]]) >= 1:
        raise ValueError('Cannot specify both fw_id and name/state/query)')

    query = {}
    if args.fw_id:
        return pw_check([int(x) for x in args.fw_id.split(',')], args)
    if args.query:
        query = ast.literal_eval(args.query)
    if args.name:
        query['name'] = args.name
    if args.state:
        query['state'] = args.state

    if wf_mode:
        return pw_check(lp.get_wf_ids(query), args)

    return pw_check(lp.get_fw_ids(query), args)

def lpad():
    m_description = 'This script is used for creating and managing a FireWorks database (LaunchPad). For a list of ' \
                    'available commands, type "lpad -h". For more help on a specific command, ' \
                    'type "lpad <command> -h".'

    parser = ArgumentParser(description=m_description)
    subparsers = parser.add_subparsers(help='command', dest='command')

    reset_parser = subparsers.add_parser('reset', help='reset and re-initialize the FireWorks database')
    reset_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required to protect against accidental reset.")

    addwf_parser = subparsers.add_parser('add', help='insert a Workflow from file')
    addwf_parser.add_argument('wf_file', help="path to a FireWork or Workflow file")

    adddir_parser = subparsers.add_parser('add_dir', help='insert all FWs/Workflows in a directory')
    adddir_parser.add_argument('wf_dir', help="path to a directory containing only FireWorks or Workflow files")

    get_fw_parser = subparsers.add_parser('get_fws', help='get information about FireWorks')
    get_fw_parser.add_argument('-i', '--fw_id', help='get FW with this fw_id', default=None, type=int)
    get_fw_parser.add_argument('-n', '--name', help='get FWs with this name', default=None)
    get_fw_parser.add_argument('-s', '--state', help='get FWs with this state ("ARCHIVED", "DEFUSED", "WAITING", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    get_fw_parser.add_argument('-q', '--query', help='get FWs matching this query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    get_fw_parser.add_argument('-d', '--display_format', help='display_format ("all","more", "less","ids", "count")', default=None)
    get_fw_parser.add_argument('-m', '--max', help='limit results', default=0, type=int)
    get_fw_parser.add_argument('--sort', help='sort results ("created_on")', default=None)
    get_fw_parser.add_argument('--rsort', help='reverse sort results ("created_on")', default=None)

    get_wf_parser = subparsers.add_parser('get_wfs', help='get information about Workflows')
    get_wf_parser.add_argument('-i', '--fw_id', help='get WF with this fw_id', default=None, type=int)
    get_wf_parser.add_argument('-n', '--name', help='get WFs with this name', default=None)
    get_wf_parser.add_argument('-s', '--state', help='get WFs with this state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    get_wf_parser.add_argument('-q', '--query', help='get WFs matching this query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    get_wf_parser.add_argument('-d', '--display_format', help='display_format ("all","more", "less","ids", "count")', default=None)
    get_wf_parser.add_argument('-m', '--max', help='limit results', default=0, type=int)
    get_wf_parser.add_argument('--sort', help='sort results ("created_on", "updated_on")', default=None)
    get_wf_parser.add_argument('--rsort', help='reverse sort results ("created_on", "updated_on")', default=None)

    rerun_fws_parser = subparsers.add_parser('rerun_fws', help='re-run FireWork(s)')
    rerun_fws_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    rerun_fws_parser.add_argument('-n', '--name', help='name', default=None)
    rerun_fws_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    rerun_fws_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    rerun_fws_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    reservation_parser = subparsers.add_parser('detect_unreserved', help='Find launches with stale reservations')
    reservation_parser.add_argument('--time', help='expiration time (seconds)',
                                    default=FWConfig().RESERVATION_EXPIRATION_SECS, type=int)
    reservation_parser.add_argument('--mark', help='cancel bad reservations', action='store_true')

    fizzled_parser = subparsers.add_parser('detect_fizzled', help='Find launches that have FIZZLED')
    fizzled_parser.add_argument('--time', help='expiration time (seconds)', default=FWConfig().RUN_EXPIRATION_SECS,
                                type=int)
    fizzled_parser.add_argument('--mark', help='mark fizzled', action='store_true')

    defuse_parser = subparsers.add_parser('defuse', help='cancel (de-fuse) an entire Workflow')
    defuse_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    defuse_parser.add_argument('-n', '--name', help='name', default=None)
    defuse_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    defuse_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    defuse_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    archive_parser = subparsers.add_parser('archive', help='archive an entire Workflow (irreversible)')
    archive_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    archive_parser.add_argument('-n', '--name', help='name', default=None)
    archive_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    archive_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    archive_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    reignite_parser = subparsers.add_parser('reignite', help='reignite (un-cancel) an entire Workflow')
    reignite_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    reignite_parser.add_argument('-n', '--name', help='name', default=None)
    reignite_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    reignite_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    reignite_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    defuse_fw_parser = subparsers.add_parser('defuse_fws', help='cancel (de-fuse) a single FireWork')
    defuse_fw_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    defuse_fw_parser.add_argument('-n', '--name', help='name', default=None)
    defuse_fw_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    defuse_fw_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    defuse_fw_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    reignite_fw_parser = subparsers.add_parser('reignite_fws', help='reignite (un-cancel) a single FireWork')
    reignite_fw_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    reignite_fw_parser.add_argument('-n', '--name', help='name', default=None)
    reignite_fw_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    reignite_fw_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    reignite_fw_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    maintain_parser = subparsers.add_parser('maintain', help='Run database maintenance')
    maintain_parser.add_argument('--infinite', help='loop infinitely', action='store_true')
    maintain_parser.add_argument('--maintain_interval', help='sleep time between maintenance loops (infinite mode)',
                                 default=FWConfig().MAINTAIN_INTERVAL, type=int)

    tuneup_parser = subparsers.add_parser('tuneup',
                                          help='Tune-up the database (should be performed during scheduled downtime)')

    refresh_parser = subparsers.add_parser('refresh', help='manually force a workflow refresh (not usually needed)')
    refresh_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    refresh_parser.add_argument('-n', '--name', help='name', default=None)
    refresh_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    refresh_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    refresh_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    priority_parser = subparsers.add_parser('set_priority', help='modify the priority of one or more FireWorks')
    priority_parser.add_argument('priority', help='get FW with this fw_id', default=None, type=int)
    priority_parser.add_argument('-i', '--fw_id', help='fw id or comma separated list of fw ids', default=None)
    priority_parser.add_argument('-n', '--name', help='name', default=None)
    priority_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    priority_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)
    priority_parser.add_argument('--password', help="Today's date, e.g. 2012-02-25. Password or positive response to input prompt required when modifying more than {} entries.".format(FWConfig().PW_CHECK_NUM))

    subparsers.add_parser('version', help='Print the version and location of FireWorks installation')

    parser.add_argument('-l', '--launchpad_file', help='path to LaunchPad file containing central DB connection info',
                        default=FWConfig().LAUNCHPAD_LOC)
    parser.add_argument('-c', '--config_dir',
                        help='path to a directory containing the LaunchPad file (used if -l unspecified)',
                        default=FWConfig().CONFIG_FILE_DIR)
    parser.add_argument('--logdir', help='path to a directory for logging', default=None)
    parser.add_argument('--loglvl', help='level to print log messages', default='INFO')
    parser.add_argument('-s', '--silencer', help='shortcut to mute log messages', action='store_true')

    webgui_parser = subparsers.add_parser('webgui', help='launch the web GUI')
    webgui_parser.add_argument("--port", dest="port", type=int, default=8000,
                        help="Port to run the server on (default: 8000)")

    webgui_parser.add_argument("--host", dest="host", type=str, default="127.0.0.1",
                        help="Host to run the server on (default: 127.0.0.1)")
    webgui_parser.add_argument('-b', '--browser', help='launch browser', action='store_true')

    addscript_parser = subparsers.add_parser('add_scripts', help='quickly add a script (or several scripts) to run in sequence')
    addscript_parser.add_argument('scripts', help="Script to run, or delimiter-separated scripts (default comma-separated)")
    addscript_parser.add_argument('-n', '--names', help='FireWork name, or delimiter-separated names (default comma-separated)', default=None)
    addscript_parser.add_argument('-w', '--wf_name', help='Workflow name', default=None)
    addscript_parser.add_argument('-d', '--delimiter', help='delimiter for separating scripts', default=',')

    recover_parser = subparsers.add_parser('recover_offline', help='recover offline workflows')
    recover_parser.add_argument('-i', '--ignore_errors', help='ignore errors', action='store_true')

    forget_parser = subparsers.add_parser('forget_offline', help='forget offline workflows')
    forget_parser.add_argument('-n', '--name', help='name', default=None)
    forget_parser.add_argument('-s', '--state', help='state ("ARCHIVED", "DEFUSED", "READY", "RESERVED", "FIZZLED", "RUNNING", "COMPLETED")', default=None)
    forget_parser.add_argument('-q', '--query', help='query (enclose pymongo-style dict in single-quotes, e.g. \'{"state":"COMPLETED"}\')', default=None)

    args = parser.parse_args()

    if args.command == 'version':
        print 'FireWorks version:', FW_VERSION
        print 'located in:', FW_INSTALL_DIR

    else:
        if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, 'my_launchpad.yaml')):
            args.launchpad_file = os.path.join(args.config_dir, 'my_launchpad.yaml')

        if args.launchpad_file:
            lp = LaunchPad.from_file(args.launchpad_file)
        else:
            args.loglvl = 'CRITICAL' if args.silencer else args.loglvl
            lp = LaunchPad(logdir=args.logdir, strm_lvl=args.loglvl)

        if args.command == 'reset':
            if not args.password:
                if raw_input('Are you sure? This will RESET {} FWs and all data. (Y/N)'.format(lp.fireworks.count()))[0].upper() == 'Y': args.password=datetime.datetime.now().strftime('%Y-%m-%d')
                else:
                    raise ValueError('Operation aborted by user.')
            lp.reset(args.password)

        elif args.command == 'detect_fizzled':
            print lp.detect_fizzled(args.time, args.mark)

        elif args.command == 'detect_unreserved':
            print lp.detect_unreserved(args.time, args.mark)

        elif args.command == 'add':
            fwf = Workflow.from_file(args.wf_file)
            lp.add_wf(fwf)

        elif args.command == 'add_dir':
            for filename in os.listdir(args.wf_dir):
                fwf = Workflow.from_file(filename)
                lp.add_wf(fwf)

        elif args.command == 'tuneup':
            lp.tuneup()

        elif args.command == 'get_wfs':
            if sum([bool(x) for x in [args.fw_id, args.name, args.state, args.query]]) > 1:
                raise ValueError('Please specify exactly one of (fw_id, name, state, query)')
            if sum([bool(x) for x in [args.fw_id, args.name, args.state, args.query]]) == 0:
                args.query = '{}'
                args.display_format = args.display_format if args.display_format else 'ids'
            else:
                args.display_format = args.display_format if args.display_format else 'more'

            if args.fw_id:
                query = {'nodes': args.fw_id}
            elif args.name:
                query = {'name': args.name}
            elif args.state:
                query = {'state': args.state}
            else:
                query = ast.literal_eval(args.query)

            if args.sort:
                sort = [(args.sort, ASCENDING)]
            elif args.rsort:
                sort = [(args.rsort, DESCENDING)]
            else:
                sort = None

            ids = lp.get_wf_ids(query, sort, args.max, count_only=args.display_format == 'count')
            wfs = []
            if args.display_format == 'ids':
                wfs = ids
            elif args.display_format == 'count':
                wfs = [ids]
            else:
                for id in ids:
                    wf = lp.get_wf_by_fw_id(id)
                    d = wf.to_display_dict()
                    if args.display_format == 'more' or args.display_format == 'less':
                        del d['name']
                        del d['parent_links']
                        del d['nodes']
                        del d['links']
                        del d['metadata']
                    if args.display_format == 'less':
                        del d['states']
                        del d['launch_dirs']
                        del d['updated_on']
                    if args.display_format == 'more' or args.display_format == 'all':
                        del d['states_list']
                    wfs.append(d)
            if len(wfs) == 1:
                wfs = wfs[0]

            print json.dumps(wfs, default=DATETIME_HANDLER, indent=4)

        elif args.command == 'get_fws':
            if sum([bool(x) for x in [args.fw_id, args.name, args.state, args.query]]) > 1:
                raise ValueError('Pleases specify exactly one of (fw_id, name, state, query)')
            if sum([bool(x) for x in [args.fw_id, args.name, args.state, args.query]]) == 0:
                args.query = '{}'
                args.display_format = args.display_format if args.display_format else 'ids'
            else:
                args.display_format = args.display_format if args.display_format else 'more'

            if args.fw_id:
                query = {'fw_id': args.fw_id}
            elif args.name:
                query = {'name': args.name}
            elif args.state:
                query = {'state': args.state}
            else:
                query = ast.literal_eval(args.query)

            if args.sort:
                sort = [(args.sort, ASCENDING)]
            elif args.rsort:
                sort = [(args.rsort, DESCENDING)]
            else:
                sort = None

            ids = lp.get_fw_ids(query, sort, args.max, count_only=args.display_format == 'count')
            fws = []
            if args.display_format == 'ids':
                fws = ids
            elif args.display_format == 'count':
                fws = [ids]
            else:
                for id in ids:
                    fw = lp.get_fw_by_id(id)
                    d = fw.to_dict()
                    if args.display_format == 'more' or args.display_format == 'less':
                        if 'archived_launches' in d:
                            del d['archived_launches']
                        del d['spec']
                    if args.display_format == 'less':
                        if 'launches' in d:
                            del d['launches']


                    fws.append(d)
            if len(fws) == 1:
                fws = fws[0]

            print json.dumps(fws, default=DATETIME_HANDLER, indent=4)

        elif args.command == 'defuse':
            fw_ids = parse_helper(lp, args, wf_mode=True)
            for f in fw_ids:
                lp.defuse_wf(f)
                lp.m_logger.debug('Processed fw_id: {}'.format(f))
            lp.m_logger.info('Finished defusing {} FWs'.format(len(fw_ids)))

        elif args.command == 'archive':
            fw_ids = parse_helper(lp, args, wf_mode=True)
            for f in fw_ids:
                lp.archive_wf(f)
                lp.m_logger.debug('Processed fw_id: {}'.format(f))
            lp.m_logger.info('Finished archiving {} FWs'.format(len(fw_ids)))

        elif args.command == 'reignite':
            fw_ids = parse_helper(lp, args, wf_mode=True)
            for f in fw_ids:
                lp.reignite_wf(f)
                lp.m_logger.debug('Processed Workflow with fw_id: {}'.format(f))
            lp.m_logger.info('Finished reigniting {} Workflows'.format(len(fw_ids)))

        elif args.command == 'defuse_fws':
            fw_ids = parse_helper(lp, args)
            for f in fw_ids:
                lp.defuse_fw(f)
                lp.m_logger.debug('Processed fw_id: {}'.format(f))
            lp.m_logger.info('Finished defusing {} FWs'.format(len(fw_ids)))

        elif args.command == 'reignite_fws':
            fw_ids = parse_helper(lp, args)
            for f in fw_ids:
                lp.reignite_fw(f)
                lp.m_logger.debug('Processed fw_id: {}'.format(f))
            lp.m_logger.info('Finished reigniting {} FWs'.format(len(fw_ids)))

        elif args.command == 'rerun_fws':
            fw_ids = parse_helper(lp, args)
            for f in fw_ids:
                lp.rerun_fw(int(f))
                lp.m_logger.debug('Processed fw_id: {}'.format(f))
            lp.m_logger.info('Finished rerunning {} FWs'.format(len(fw_ids)))

        elif args.command == 'refresh':
            fw_ids = parse_helper(lp, args, wf_mode=True)
            for f in fw_ids:
                wf = lp.get_wf_by_fw_id(f)
                lp._refresh_wf(wf, f)
                lp.m_logger.debug('Processed Workflow with fw_id: {}'.format(f))
            lp.m_logger.info('Finished refreshing {} Workflows'.format(len(fw_ids)))

        elif args.command == 'set_priority':
            fw_ids = parse_helper(lp, args, wf_mode=True)
            for f in fw_ids:
                lp.set_priority(f, args.priority)
                lp.m_logger.debug("Processed fw_id {}".format(f))
            lp.m_logger.info("Finished setting priorities of {} FWs".format(len(fw_ids)))

        elif args.command == 'webgui':
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fireworks.base_site.settings")
            os.environ["FWDB_CONFIG"] = json.dumps(lp.to_dict())
            from django.core.management import call_command
            from multiprocessing import Process
            p1 = Process(target=call_command,
                         args=("runserver",  "{}:{}".format(args.host, args.port)))
            p1.start()
            if args.browser:
                time.sleep(2)
                webbrowser.open("http://{}:{}".format(args.host, args.port))
            p1.join()

        elif args.command == 'add_scripts':
            scripts = args.scripts.split(args.delimiter)
            names = args.names.split(args.delimiter) if args.names else [None] * len(scripts)
            wf_name = args.wf_name if args.wf_name else names[0]
            fws = []
            links = {}
            for idx, s in enumerate(scripts):
                fws.append(FireWork(ScriptTask({'script': s, 'use_shell': True}), name=names[idx], fw_id=idx))
                if idx != 0:
                    links[idx-1] = idx

            lp.add_wf(Workflow(fws, links, wf_name))

        elif args.command == 'recover_offline':
            failed_fws = []
            for l in lp.offline_runs.find({"completed": False, "deprecated": False}, {"launch_id": 1}):
                fw = lp.recover_offline(l['launch_id'], args.ignore_errors)
                if fw:
                    failed_fws.append(fw)

            lp.m_logger.info("FINISHED recovering offline runs.")
            if failed_fws:
                lp.m_logger.info("FAILED to recover offline fw_ids: {}".format(failed_fws))

        elif args.command == 'forget_offline':
            fw_ids = parse_helper(lp, args)
            for f in fw_ids:
                lp.forget_offline(f)
                lp.m_logger.debug('Processed fw_id: {}'.format(f))

            lp.m_logger.info('Finished forget_offine, processed {} FWs'.format(len(fw_ids)))


if __name__ == '__main__':
    lpad()