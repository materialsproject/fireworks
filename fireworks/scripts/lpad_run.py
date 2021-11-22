"""
A runnable script for managing a FireWorks database (a command-line interface to launchpad.py)
"""

import ast
import copy
import datetime
import json
import os
import re
import time
import traceback
from argparse import ArgumentParser, ArgumentTypeError

import ruamel.yaml as yaml
from pymongo import ASCENDING, DESCENDING

from fireworks import FW_INSTALL_DIR
from fireworks import __version__ as FW_VERSION
from fireworks.core.firework import Firework, Workflow
from fireworks.core.fworker import FWorker
from fireworks.core.launchpad import LaunchPad, WFLock
from fireworks.features.fw_report import FWReport
from fireworks.features.introspect import Introspector
from fireworks.fw_config import (
    CONFIG_FILE_DIR,
    FWORKER_LOC,
    LAUNCHPAD_LOC,
    MAINTAIN_INTERVAL,
    PW_CHECK_NUM,
    RESERVATION_EXPIRATION_SECS,
    RUN_EXPIRATION_SECS,
    WEBSERVER_HOST,
    WEBSERVER_PORT,
)
from fireworks.user_objects.firetasks.script_task import ScriptTask
from fireworks.utilities.fw_serializers import DATETIME_HANDLER, recursive_dict

__author__ = "Anubhav Jain"
__credits__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 7, 2013"

DEFAULT_LPAD_YAML = "my_launchpad.yaml"


def pw_check(ids, args, skip_pw=False):
    if len(ids) > PW_CHECK_NUM and not skip_pw:
        m_password = datetime.datetime.now().strftime("%Y-%m-%d")
        if not args.password:
            if input(f"Are you sure? This will modify {len(ids)} entries. (Y/N)")[0].upper() == "Y":
                args.password = datetime.datetime.now().strftime("%Y-%m-%d")
            else:
                print("Operation aborted by user.")
        if args.password != m_password:
            raise ValueError(
                f"Modifying more than {PW_CHECK_NUM} entries requires setting the --password parameter! "
                "(Today's date, e.g. 2012-02-25)"
            )
    return ids


def parse_helper(lp, args, wf_mode=False, skip_pw=False):
    """
    Helper method to parse args that can take either id, name, state or query.

    Args:
        args
        wf_mode (bool)
        skip_pw (bool)

    Returns:
        list of ids
    """
    if args.fw_id and sum(bool(x) for x in [args.name, args.state, args.query]) >= 1:
        raise ValueError("Cannot specify both fw_id and name/state/query)")

    query = {}
    if args.fw_id:
        return pw_check(args.fw_id, args, skip_pw)
    if args.query:
        query = ast.literal_eval(args.query)
    if args.name and "launches_mode" in args and not args.launches_mode:
        query["name"] = args.name
    if args.state:
        query["state"] = args.state

    if hasattr(args, "sort") and args.sort:
        sort = [(args.sort, ASCENDING)]
    elif hasattr(args, "rsort") and args.rsort:
        sort = [(args.rsort, DESCENDING)]
    else:
        sort = None

    max = args.max if hasattr(args, "max") else 0

    if wf_mode:
        return pw_check(lp.get_wf_ids(query, sort=sort, limit=max), args, skip_pw)

    return pw_check(lp.get_fw_ids(query, sort=sort, limit=max, launches_mode=args.launches_mode), args, skip_pw)


def get_lp(args):
    try:
        if not args.launchpad_file:
            if os.path.exists(os.path.join(args.config_dir, DEFAULT_LPAD_YAML)):
                args.launchpad_file = os.path.join(args.config_dir, DEFAULT_LPAD_YAML)
            else:
                args.launchpad_file = LAUNCHPAD_LOC

        if args.launchpad_file:
            return LaunchPad.from_file(args.launchpad_file)
        else:
            args.loglvl = "CRITICAL" if args.silencer else args.loglvl
            return LaunchPad(logdir=args.logdir, strm_lvl=args.loglvl)
    except Exception:
        traceback.print_exc()
        err_message = (
            "FireWorks was not able to connect to MongoDB. Is the server running? "
            f"The database file specified was {args.launchpad_file}."
        )
        if not args.launchpad_file:
            err_message += (
                ' Type "lpad init" if you would like to set up a file that specifies '
                "location and credentials of your Mongo database (otherwise use default "
                "localhost configuration)."
            )
        raise ValueError(err_message)


def init_yaml(args):
    if args.uri_mode:
        fields = (
            ("host", None, "Example: mongodb+srv://USER:PASSWORD@CLUSTERNAME.mongodb.net/fireworks"),
            ("ssl_ca_file", None, "Path to any client certificate to be used for mongodb connection"),
            (
                "authsource",
                None,
                "Database used for authentication, if not connection db. e.g., for MongoDB Atlas this is sometimes "
                "'admin'.",
            ),
        )
    else:
        fields = (
            ("host", "localhost", "Example: 'localhost' or 'mongodb+srv://CLUSTERNAME.mongodb.net'"),
            ("port", 27017, ""),
            ("name", "fireworks", "Database under which to store the fireworks collections"),
            ("username", None, "Username for MongoDB authentication"),
            ("password", None, "Password for MongoDB authentication"),
            ("ssl_ca_file", None, "Path to any client certificate to be used for Mongodb connection"),
            (
                "authsource",
                None,
                "Database used for authentication, if not connection db. e.g., for MongoDB Atlas this is sometimes "
                "'admin'.",
            ),
        )

    doc = {}
    if args.uri_mode:
        print(
            "Note 1: You are in URI format mode. This means that all database parameters (username, password, host, "
            "port, database name, etc.) must be present in the URI. See: "
            "https://docs.mongodb.com/manual/reference/connection-string/ for details."
        )
        print("(Enter your connection URI in under the 'host' parameter)")
    print("Please supply the following configuration values")
    print("(press Enter if you want to accept the defaults)\n")
    for k, default, helptext in fields:
        val = input(f"Enter {k} parameter. (default: {default}). {helptext}: ")
        doc[k] = val if val else default
    if "port" in doc:
        doc["port"] = int(doc["port"])  # enforce the port as an int
    if args.uri_mode:
        doc["uri_mode"] = True

    lp = LaunchPad.from_dict(doc)
    lp.to_file(args.config_file)
    print(f"\nConfiguration written to {args.config_file}!")


def reset(args):
    lp = get_lp(args)
    if not args.password:
        if (
            input(f"Are you sure? This will RESET {lp.workflows.count_documents({})} workflows and all data. (Y/N)")[
                0
            ].upper()
            == "Y"
        ):
            args.password = datetime.datetime.now().strftime("%Y-%m-%d")
        else:
            raise ValueError("Operation aborted by user.")
    lp.reset(args.password)


def add_wf(args):
    lp = get_lp(args)
    if args.dir:
        files = []
        for f in args.wf_file:
            files.extend([os.path.join(f, i) for i in os.listdir(f)])
    else:
        files = args.wf_file
    for f in files:
        fwf = Workflow.from_file(f)
        if args.check:
            from fireworks.utilities.dagflow import DAGFlow

            DAGFlow.from_fireworks(fwf).check()
        lp.add_wf(fwf)


def append_wf(args):
    lp = get_lp(args)
    lp.append_wf(Workflow.from_file(args.wf_file), args.fw_id, detour=args.detour, pull_spec_mods=args.pull_spec_mods)


def dump_wf(args):
    lp = get_lp(args)
    lp.get_wf_by_fw_id(args.fw_id).to_file(args.wf_file)


def check_wf(args):
    from fireworks.utilities.dagflow import DAGFlow

    lp = get_lp(args)
    DAGFlow.from_fireworks(lp.get_wf_by_fw_id(args.fw_id)).check()


def add_wf_dir(args):
    lp = get_lp(args)
    for filename in os.listdir(args.wf_dir):
        fwf = Workflow.from_file(filename)
        lp.add_wf(fwf)


def print_fws(ids, lp, args):
    """Prints results of some FireWorks query to stdout."""
    fws = []
    if args.display_format == "ids":
        fws = ids
    elif args.display_format == "count":
        fws = [ids]
    else:
        for id in ids:
            fw = lp.get_fw_by_id(id)
            d = fw.to_dict()
            d["state"] = d.get("state", "WAITING")
            if args.display_format == "more" or args.display_format == "less":
                if "archived_launches" in d:
                    del d["archived_launches"]
                del d["spec"]
            if args.display_format == "less":
                if "launches" in d:
                    del d["launches"]
            fws.append(d)
    if len(fws) == 1:
        fws = fws[0]

    print(args.output(fws))


def get_fw_ids_helper(lp, args, count_only=None):
    """Build fws query from command line options and submit.

    Parameters:
        lp (fireworks.core.firework.Launchpad)
        args (argparse.Namespace)
        count_only (bool): if None, then looked up in args.

    Returns:
        [int]: resulting fw_ids or count of fws in query.
    """
    if sum(bool(x) for x in [args.fw_id, args.name, args.state, args.query]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, state, query)")
    if sum(bool(x) for x in [args.fw_id, args.name, args.state, args.query]) == 0:
        args.query = "{}"
        args.display_format = args.display_format if args.display_format else "ids"
    if sum(bool(x) for x in [args.fw_id, args.name, args.qid]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, qid)")
    else:
        args.display_format = args.display_format if args.display_format else "more"

    if args.fw_id:
        query = {"fw_id": {"$in": args.fw_id}}
    elif args.name and not args.launches_mode:
        query = {"name": args.name}
    elif args.state:
        query = {"state": args.state}
    elif args.query:
        query = ast.literal_eval(args.query)
    else:
        query = None

    if args.sort:
        sort = [(args.sort, ASCENDING)]
    elif args.rsort:
        sort = [(args.rsort, DESCENDING)]
    else:
        sort = None

    if count_only is None:
        count_only = args.display_format == "count"
    if args.qid:
        ids = lp.get_fw_ids_from_reservation_id(args.qid)
        if query:
            query["fw_id"] = {"$in": ids}
            ids = lp.get_fw_ids(query, sort, args.max, launches_mode=args.launches_mode)

    else:
        ids = lp.get_fw_ids(query, sort, args.max, count_only=count_only, launches_mode=args.launches_mode)
    return ids


def get_fws_helper(lp, ids, args):
    """Get fws from ids in a representation according to args.display_format."""
    fws = []
    if args.display_format == "ids":
        fws = ids
    elif args.display_format == "count":
        fws = [ids]
    else:
        for id in ids:
            fw = lp.get_fw_by_id(id)
            d = fw.to_dict()
            d["state"] = d.get("state", "WAITING")
            if args.display_format == "more" or args.display_format == "less":
                if "archived_launches" in d:
                    del d["archived_launches"]
                del d["spec"]
            if args.display_format == "less":
                if "launches" in d:
                    del d["launches"]
            fws.append(d)
    if len(fws) == 1:
        fws = fws[0]
    return fws


def get_fws(args):
    lp = get_lp(args)
    ids = get_fw_ids_helper(lp, args)
    fws = get_fws_helper(lp, ids, args)
    print(args.output(fws))


def get_fws_in_wfs(args):
    # get_wfs
    lp = get_lp(args)
    if sum(bool(x) for x in [args.wf_fw_id, args.wf_name, args.wf_state, args.wf_query]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, state, query)")
    if sum(bool(x) for x in [args.wf_fw_id, args.wf_name, args.wf_state, args.wf_query]) == 0:
        args.wf_query = "{}"

    if args.wf_fw_id:
        wf_query = {"nodes": {"$in": args.wf_fw_id}}
    elif args.wf_name:
        wf_query = {"name": args.wf_name}
    elif args.wf_state:
        wf_query = {"state": args.wf_state}
    else:
        wf_query = ast.literal_eval(args.wf_query)

    # get_fws
    if sum(bool(x) for x in [args.fw_fw_id, args.fw_name, args.fw_state, args.fw_query]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, state, query)")
    if sum(bool(x) for x in [args.fw_fw_id, args.fw_name, args.fw_state, args.fw_query]) == 0:
        args.fw_query = "{}"
        args.display_format = args.display_format if args.display_format else "ids"
    if sum(bool(x) for x in [args.fw_fw_id, args.fw_name, args.qid]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, qid)")
    else:
        args.display_format = args.display_format if args.display_format else "more"

    if args.fw_fw_id:
        fw_query = {"fw_id": {"$in": args.fw_fw_id}}
    elif args.fw_name and not args.launches_mode:
        fw_query = {"name": args.fw_name}
    elif args.fw_state:
        fw_query = {"state": args.fw_state}
    elif args.fw_query:
        fw_query = ast.literal_eval(args.fw_query)
    else:
        fw_query = None

    if args.sort:
        sort = [(args.sort, ASCENDING)]
    elif args.rsort:
        sort = [(args.rsort, DESCENDING)]
    else:
        sort = None

    if args.qid:
        ids = lp.get_fw_ids_from_reservation_id(args.qid)
        if fw_query:
            fw_query["fw_id"] = {"$in": ids}
            ids = lp.get_fw_ids_in_wfs(
                wf_query=wf_query, fw_query=fw_query, sort=sort, limit=args.max, launches_mode=args.launches_mode
            )
    else:
        ids = lp.get_fw_ids_in_wfs(
            wf_query=wf_query,
            fw_query=fw_query,
            sort=sort,
            limit=args.max,
            count_only=args.display_format == "count",
            launches_mode=args.launches_mode,
        )

    print_fws(ids, lp, args)


def update_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    lp.update_spec(fw_ids, json.loads(args.update), args.mongo)


def get_wfs(args):
    lp = get_lp(args)
    if sum(bool(x) for x in [args.fw_id, args.name, args.state, args.query]) > 1:
        raise ValueError("Please specify exactly one of (fw_id, name, state, query)")
    if sum(bool(x) for x in [args.fw_id, args.name, args.state, args.query]) == 0:
        args.query = "{}"
        args.display_format = args.display_format if args.display_format else "ids"
    else:
        args.display_format = args.display_format if args.display_format else "more"

    if args.fw_id:
        query = {"nodes": {"$in": args.fw_id}}
    elif args.name:
        query = {"name": args.name}
    elif args.state:
        query = {"state": args.state}
    else:
        query = ast.literal_eval(args.query)

    if args.sort:
        sort = [(args.sort, ASCENDING)]
    elif args.rsort:
        sort = [(args.rsort, DESCENDING)]
    else:
        sort = None

    ids = lp.get_wf_ids(query, sort, args.max, count_only=args.display_format == "count")
    if args.display_format == "ids":
        wfs = ids
    elif args.display_format == "count":
        wfs = [ids]
    else:
        wfs = []
        for i in ids:
            d = lp.get_wf_summary_dict(i, args.display_format)
            d["name"] += "--%d" % i
            wfs.append(d)

    if args.table:
        if wfs:
            headers = list(wfs[0].keys())
            from prettytable import PrettyTable

            t = PrettyTable(headers)
            for d in wfs:
                t.add_row([d.get(k) for k in headers])
            print(t)
    else:
        if len(wfs) == 1:
            wfs = wfs[0]
        print(args.output(wfs))


def delete_wfs(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        lp.delete_wf(f, delete_launch_dirs=args.delete_launch_dirs)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished deleting {len(fw_ids)} WFs")


def get_children(links, start, max_depth):
    data = {}
    for l, c in links.items():
        if l == start:
            if len(c) > 0:
                data[l] = [get_children(links, i, max_depth) for i in c]
            else:
                data[l] = c
    return data


def detect_lostruns(args):
    lp = get_lp(args)
    query = ast.literal_eval(args.query) if args.query else None
    launch_query = ast.literal_eval(args.launch_query) if args.launch_query else None
    fl, ff, fi = lp.detect_lostruns(
        expiration_secs=args.time,
        fizzle=args.fizzle,
        rerun=args.rerun,
        max_runtime=args.max_runtime,
        min_runtime=args.min_runtime,
        refresh=args.refresh,
        query=query,
        launch_query=launch_query,
    )
    lp.m_logger.debug(f"Detected {len(fl)} lost launches: {fl}")
    lp.m_logger.info(f"Detected {len(ff)} lost FWs: {ff}")
    if args.display_format is not None and args.display_format != "none":
        print_fws(ff, lp, args)
    lp.m_logger.info(f"Detected {len(fi)} inconsistent FWs: {fi}")
    if args.display_format is not None and args.display_format != "none":
        print_fws(fi, lp, args)
    if len(ff) > 0 and not args.fizzle and not args.rerun:
        print("You can fix lost FWs using the --rerun or --fizzle arguments to the detect_lostruns command")
    if len(fi) > 0 and not args.refresh:
        print("You can fix inconsistent FWs using the --refresh argument to the detect_lostruns command")


def detect_unreserved(args):
    lp = get_lp(args)
    if args.display_format is not None and args.display_format != "none":
        unreserved = lp.detect_unreserved(expiration_secs=args.time, rerun=False)
        # very inefficient, replace by mongo aggregation
        fw_ids = []
        for launch_id in unreserved:
            launch = lp.get_launch_by_id(launch_id)
            fw_ids.append(launch.fw_id)
        print_fws(fw_ids, lp, args)
    print(lp.detect_unreserved(expiration_secs=args.time, rerun=args.rerun))


def tuneup(args):
    lp = get_lp(args)
    lp.tuneup(bkground=not args.full)


def defuse_wfs(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        lp.defuse_wf(f, defuse_all_states=args.defuse_all_states)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished defusing {len(fw_ids)} FWs.")
    if not args.defuse_all_states:
        lp.m_logger.info(
            "Note: FIZZLED and COMPLETED FWs were not defused. "
            "Use the --defuse_all_states option to force this (or rerun FIZZLED FWs first)."
        )


def pause_wfs(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        lp.pause_wf(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished defusing {len(fw_ids)} FWs.")


def archive(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        lp.archive_wf(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished archiving {len(fw_ids)} WFs")


def reignite_wfs(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        lp.reignite_wf(f)
        lp.m_logger.debug(f"Processed Workflow with fw_id: {f}")
    lp.m_logger.info(f"Finished reigniting {len(fw_ids)} Workflows")


def defuse_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    for f in fw_ids:
        lp.defuse_fw(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished defusing {len(fw_ids)} FWs")


def pause_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    for f in fw_ids:
        lp.pause_fw(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished pausing {len(fw_ids)} FWs")


def reignite_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    for f in fw_ids:
        lp.reignite_fw(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished reigniting {len(fw_ids)} FWs")


def resume_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    for f in fw_ids:
        lp.resume_fw(f)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished resuming {len(fw_ids)} FWs")


def rerun_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    if args.task_level:
        launch_ids = args.launch_id
        if launch_ids is None:
            launch_ids = ["last"] * len(fw_ids)
        elif len(launch_ids) != len(fw_ids):
            raise ValueError("Specify the same number of tasks and launches")
    else:
        launch_ids = [None] * len(fw_ids)
    for f, l in zip(fw_ids, launch_ids):
        lp.rerun_fw(int(f), recover_launch=l, recover_mode=args.recover_mode)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished setting {len(fw_ids)} FWs to rerun")


def refresh(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        wf = lp.get_wf_by_fw_id_lzyfw(f)
        for fw_id in wf.root_fw_ids:
            lp._refresh_wf(fw_id)
        lp.m_logger.debug(f"Processed Workflow with fw_id: {f}")
    lp.m_logger.info(f"Finished refreshing {len(fw_ids)} Workflows")


def unlock(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=True)
    for f in fw_ids:
        with WFLock(lp, f, expire_secs=0, kill=True):
            lp.m_logger.warning(f"FORCIBLY RELEASING LOCK DUE TO USER COMMAND, WF: {f}")
            lp.m_logger.debug(f"Processed Workflow with fw_id: {f}")
    lp.m_logger.info(f"Finished unlocking {len(fw_ids)} Workflows")


def get_qid(args):
    lp = get_lp(args)
    for f in args.fw_id:
        print(lp.get_reservation_id_from_fw_id(f))


def cancel_qid(args):
    lp = get_lp(args)
    lp.m_logger.warning(
        "WARNING: cancel_qid does not actually remove jobs from the queue "
        "(e.g., execute qdel), this must be done manually!"
    )
    lp.cancel_reservation_by_reservation_id(args.qid)


def set_priority(args):
    wf_mode = args.wf
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, wf_mode=wf_mode)
    if wf_mode:
        all_fw_ids = set()
        for fw_id in fw_ids:
            wf = lp.get_wf_by_fw_id_lzyfw(fw_id)
            all_fw_ids.update(wf.id_fw.keys())
        fw_ids = list(all_fw_ids)
    for f in fw_ids:
        lp.set_priority(f, args.priority)
        lp.m_logger.debug(f"Processed fw_id {f}")
    lp.m_logger.info(f"Finished setting priorities of {len(fw_ids)} FWs")


def _open_webbrowser(url):
    """Open a web browser after a delay to give the web server more startup time."""
    import webbrowser

    time.sleep(2)
    webbrowser.open(url)


def webgui(args):
    from fireworks.flask_site.app import app

    app.lp = get_lp(args)

    if any([args.webgui_username, args.webgui_password]) and not all([args.webgui_username, args.webgui_password]):
        raise ValueError("Must set BOTH a webgui_username and webgui_password!")

    app.config["WEBGUI_USERNAME"] = args.webgui_username
    app.config["WEBGUI_PASSWORD"] = args.webgui_password

    if args.wflowquery:
        app.BASE_Q_WF = json.loads(args.wflowquery)
    if args.fwquery:
        app.BASE_Q = json.loads(args.fwquery)
        if "state" in app.BASE_Q:
            app.BASE_Q_WF["state"] = app.BASE_Q["state"]

    if not args.server_mode:
        from threading import Thread

        url = f"http://{args.host}:{args.port}"
        p1 = Thread(target=_open_webbrowser, args=(url,))
        p1.start()
        app.run(host=args.host, port=args.port, debug=args.debug)
        p1.join()
    else:
        try:
            from fireworks.flask_site.gunicorn import StandaloneApplication
        except ImportError:
            import sys

            sys.exit("Gunicorn is required for server mode. Install using `pip install gunicorn`.")
        options = {
            "bind": f"{args.host}:{args.port}",
            "workers": args.nworkers,
        }
        StandaloneApplication(app, options).run()


def add_scripts(args):
    lp = get_lp(args)
    args.names = args.names if args.names else [None] * len(args.scripts)
    args.wf_name = args.wf_name if args.wf_name else args.names[0]
    fws = []
    links = {}
    for idx, s in enumerate(args.scripts):
        fws.append(Firework(ScriptTask({"script": s, "use_shell": True}), name=args.names[idx], fw_id=idx))
        if idx != 0:
            links[idx - 1] = idx

    lp.add_wf(Workflow(fws, links, args.wf_name))


def recover_offline(args):
    lp = get_lp(args)
    fworker_name = FWorker.from_file(args.fworker_file).name if args.fworker_file else None
    failed_fws = []
    recovered_fws = []

    for l in lp.offline_runs.find({"completed": False, "deprecated": False}, {"launch_id": 1, "fw_id": 1}):
        if fworker_name and lp.launches.count({"launch_id": l["launch_id"], "fworker.name": fworker_name}) == 0:
            continue
        fw = lp.recover_offline(l["launch_id"], args.ignore_errors, args.print_errors)
        if fw:
            failed_fws.append(l["fw_id"])
        else:
            recovered_fws.append(l["fw_id"])

    lp.m_logger.info(f"FINISHED recovering offline runs. {len(recovered_fws)} job(s) recovered: {recovered_fws}")
    if failed_fws:
        lp.m_logger.info(f"FAILED to recover offline fw_ids: {failed_fws}")


def forget_offline(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args)
    for f in fw_ids:
        lp.forget_offline(f, launch_mode=False)
        lp.m_logger.debug(f"Processed fw_id: {f}")
    lp.m_logger.info(f"Finished forget_offine, processed {len(fw_ids)} FWs")


def report(args):
    lp = get_lp(args)
    query = ast.literal_eval(args.query) if args.query else None
    fwr = FWReport(lp)
    stats = fwr.get_stats(
        coll=args.collection, interval=args.interval, num_intervals=args.num_intervals, additional_query=query
    )
    title_str = f"Stats on {args.collection}"
    title_dec = "-" * len(title_str)
    print(title_dec)
    print(title_str)
    print(title_dec)
    print(fwr.get_stats_str(stats))


def introspect(args):
    print("NOTE: This feature is in beta mode...")
    lp = get_lp(args)
    isp = Introspector(lp)
    for coll in ["launches", "tasks", "fireworks", "workflows"]:
        print(f"generating report for {coll}...please wait...")
        print("")
        table = isp.introspect_fizzled(coll=coll, threshold=args.threshold, limit=args.max)
        isp.print_report(table, coll)
        print("")


def get_launchdir(args):
    lp = get_lp(args)
    ld = lp.get_launchdir(args.fw_id, args.launch_idx)
    print(ld)


def track_fws(args):
    lp = get_lp(args)
    fw_ids = parse_helper(lp, args, skip_pw=True)
    include = args.include
    exclude = args.exclude
    first_print = True  # used to control newline
    for f in fw_ids:
        data = lp.get_tracker_data(f)
        output = []
        for d in data:
            for t in d["trackers"]:
                if (not include or t.filename in include) and (not exclude or t.filename not in exclude):
                    output.append(f"## Launch id: {d['launch_id']}")
                    output.append(str(t))
        if output:
            name = lp.fireworks.find_one({"fw_id": f}, {"name": 1})["name"]
            output.insert(0, f"# FW id: {f}, FW name: {name}")
            if first_print:
                first_print = False
            else:
                output.insert(0, ">------<")
            print("\n".join(output))


def version(args):
    print("FireWorks version:", FW_VERSION)
    print("located in:", FW_INSTALL_DIR)


def maintain(args):
    lp = get_lp(args)
    lp.maintain(args.infinite, args.maintain_interval)


def orphaned(args):
    # get_fws
    lp = get_lp(args)
    fw_ids = get_fw_ids_helper(lp, args, count_only=False)

    # get_wfs
    orphaned_fw_ids = []
    for fw_id in fw_ids:
        query = {"nodes": fw_id}
        wf_ids = lp.get_wf_ids(query)
        if len(wf_ids) == 0:
            orphaned_fw_ids.append(fw_id)

    fws = get_fws_helper(lp, orphaned_fw_ids, args)
    if args.remove:
        lp.m_logger.info(f"Found {len(orphaned_fw_ids)} orphaned fw_ids: {orphaned_fw_ids}")
        lp.delete_fws(orphaned_fw_ids, delete_launch_dirs=args.delete_launch_dirs)
    else:
        print(args.output(fws))


def get_output_func(format):
    if format == "json":
        return lambda x: json.dumps(x, default=DATETIME_HANDLER, indent=4)
    else:
        return lambda x: yaml.safe_dump(recursive_dict(x, preserve_unicode=False), default_flow_style=False)


def arg_positive_int(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise ArgumentTypeError(f"int(value) conversion failed for {value}")

    if ivalue < 1:
        raise ValueError(f"{value} is not a positive integer")
    return ivalue


def lpad():
    m_description = (
        "A command line interface to FireWorks. For more help on a specific command, type 'lpad <command> -h'."
    )

    parser = ArgumentParser(description=m_description)
    parent_parser = ArgumentParser(add_help=False)
    parser.add_argument(
        "-o",
        "--output",
        choices=["json", "yaml"],
        default="json",
        type=lambda s: s.lower(),
        help="Set output display format to either json or YAML. "
        "YAML is easier to read for long documents. JSON is the default.",
    )

    subparsers = parser.add_subparsers(help="command", dest="command")

    # This makes common argument options easier to maintain. E.g., what if
    # there is a new state or disp option?
    # NOTE: Those sets of standard options are not used consistently below (jotelha)
    fw_id_args = ["-i", "--fw_id"]
    fw_id_kwargs = {"type": str, "help": "fw_id"}

    state_args = ["-s", "--state"]
    state_kwargs = {
        "type": lambda s: s.upper(),
        "help": "Select by state.",
        "choices": Firework.STATE_RANKS,
    }
    disp_args = ["-d", "--display_format"]
    disp_kwargs = {
        "type": lambda s: s.lower(),
        "help": "Display format.",
        "default": "less",
        "choices": ["all", "more", "less", "ids", "count", "reservations"],
    }

    # enhanced display options allow for value 'none' or None (default) for no output
    enh_disp_args = copy.deepcopy(disp_args)
    enh_disp_kwargs = copy.deepcopy(disp_kwargs)
    enh_disp_kwargs["choices"].append("none")
    enh_disp_kwargs["default"] = None

    query_args = ["-q", "--query"]
    query_kwargs = {"help": "Query (enclose pymongo-style dict in " 'single-quotes, e.g. \'{"state":"COMPLETED"}\')'}

    launches_mode_args = ["-lm", "--launches_mode"]
    launches_mode_kwargs = {
        "action": "store_true",
        "help": "Query the launches collection (enclose pymongo-style "
        "dict in single-quotes, e.g. '{\"launch_id\": 1}')",
    }

    qid_args = ["--qid"]
    qid_kwargs = {"help": "Query by reservation id of job in queue"}

    # for using fw- and wf-specific options on one command line, distinguish by prefix fw and wf
    # prefix short one-dash options with 'wf', i.e. '-i' -> '-wfi'
    # prefix long two-dash options with 'wf_', i.e. '--fw_id' -> '--wf_fw_id'
    wf_prefixed_fw_id_args = [re.sub("^-([^-].*)$", "-wf\\1", s) for s in fw_id_args]
    wf_prefixed_fw_id_args = [re.sub("^--(.*)$", "--wf_\\1", s) for s in wf_prefixed_fw_id_args]

    wf_prefixed_state_args = [re.sub("^-([^-].*)$", "-wf\\1", s) for s in state_args]
    wf_prefixed_state_args = [re.sub("^--(.*)$", "--wf_\\1", s) for s in wf_prefixed_state_args]

    wf_prefixed_query_args = [re.sub("^-([^-].*)$", "-wf\\1", s) for s in query_args]
    wf_prefixed_query_args = [re.sub("^--(.*)$", "--wf_\\1", s) for s in wf_prefixed_query_args]

    # prefix short one-dash options with 'fw', i.e. '-i' -> '-fwi'
    # prefix long two-dash options with 'fw_', i.e. '--fw_id' -> '--fw_fw_id'
    fw_prefixed_fw_id_args = [re.sub("^-([^-].*)$", "-fw\\1", s) for s in fw_id_args]
    fw_prefixed_fw_id_args = [re.sub("^--(.*)$", "--fw_\\1", s) for s in fw_prefixed_fw_id_args]

    fw_prefixed_state_args = [re.sub("^-([^-].*)$", "-fw\\1", s) for s in state_args]
    fw_prefixed_state_args = [re.sub("^--(.*)$", "--fw_\\1", s) for s in fw_prefixed_state_args]

    fw_prefixed_query_args = [re.sub("^-([^-].*)$", "-fw\\1", s) for s in query_args]
    fw_prefixed_query_args = [re.sub("^--(.*)$", "--fw_\\1", s) for s in fw_prefixed_query_args]

    # filter all long options, i.e. '--fw_id' and strip off preceding '--'
    fw_id_options = [
        re.sub("^--(.*)$", "\\1", opt)
        for opt in [*fw_id_args, *wf_prefixed_fw_id_args, *fw_prefixed_fw_id_args]
        if re.match("^--.*$", opt)
    ]

    version_parser = subparsers.add_parser("version", help="Print the version and location of FireWorks")
    version_parser.set_defaults(func=version)

    init_parser = subparsers.add_parser("init", help="Initialize a Fireworks launchpad YAML file.")
    init_parser.add_argument(
        "-u",
        "--uri_mode",
        action="store_true",
        help="Connect via a URI, see: https://docs.mongodb.com/manual/reference/connection-string/",
    )
    init_parser.add_argument("--config-file", default=DEFAULT_LPAD_YAML, type=str, help="Filename to write to.")
    init_parser.set_defaults(func=init_yaml)

    reset_parser = subparsers.add_parser("reset", help="reset and re-initialize the FireWorks database")
    reset_parser.add_argument(
        "--password",
        help="Today's date,  e.g. 2012-02-25. "
        "Password or positive response to input prompt "
        "required to protect against accidental reset.",
    )
    reset_parser.set_defaults(func=reset)

    addwf_parser = subparsers.add_parser("add", help="insert a Workflow from file")
    addwf_parser.add_argument(
        "-d", "--dir", action="store_true", help="Directory mode. Finds all files in the paths given by wf_file."
    )
    addwf_parser.add_argument("wf_file", nargs="+", help="Path to a Firework or Workflow file")
    addwf_parser.add_argument(
        "-c", "--check", help="check the workflow before adding", dest="check", action="store_true"
    )
    addwf_parser.set_defaults(func=add_wf, check=False)

    check_wf_parser = subparsers.add_parser("check_wflow", help="check a workflow from launchpad")
    check_wf_parser.add_argument("-i", "--fw_id", type=int, help="the id of a firework from the workflow")
    check_wf_parser.set_defaults(func=check_wf)

    get_launchdir_parser = subparsers.add_parser(
        "get_launchdir",
        help="get the directory of the most recent launch of the given fw_id. A common usage is "
        "'cd `get_launchdir <FW_ID>`' to change the working directory to that of the FW launch",
    )
    get_launchdir_parser.add_argument("fw_id", type=int, help="fw_id to chdir to")
    get_launchdir_parser.add_argument(
        "--launch_idx",
        type=int,
        help="the index of the launch to get (default of -1 is most recent launch)",
        default=-1,
    )
    get_launchdir_parser.set_defaults(func=get_launchdir)

    append_wf_parser = subparsers.add_parser(
        "append_wflow", help="append a workflow from file to a workflow on launchpad"
    )
    append_wf_parser.add_argument(*fw_id_args, type=fw_id_kwargs["type"], help="parent firework ids")
    append_wf_parser.add_argument("-f", "--wf_file", help="path to a firework or workflow file")
    append_wf_parser.add_argument(
        "-d", "--detour", help="append workflow as a detour", dest="detour", action="store_true"
    )
    append_wf_parser.add_argument(
        "--no_pull_spec_mods", help="do not to pull spec mods from parent", dest="pull_spec_mods", action="store_false"
    )
    append_wf_parser.set_defaults(func=append_wf, detour=False, pull_spec_mods=True)

    dump_wf_parser = subparsers.add_parser("dump_wflow", help="dump a workflow from launchpad to a file")
    dump_wf_parser.add_argument("-i", "--fw_id", type=int, help="the id of a firework from the workflow")
    dump_wf_parser.add_argument("-f", "--wf_file", help="path to a local file to store the workflow")
    dump_wf_parser.set_defaults(func=dump_wf)

    addscript_parser = subparsers.add_parser(
        "add_scripts", help="quickly add a script (or several scripts) to run in sequence"
    )
    addscript_parser.add_argument("scripts", help="Script to run, or space-separated names", nargs="*")
    addscript_parser.add_argument("-n", "--names", help="Firework name, or space-separated names", nargs="*")
    addscript_parser.add_argument("-w", "--wf_name", help="Workflow name")
    addscript_parser.add_argument("-d", "--delimiter", help="delimiter for separating scripts", default=",")
    addscript_parser.set_defaults(func=add_scripts)

    get_fw_parser = subparsers.add_parser("get_fws", help="get information about FireWorks")
    get_fw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    get_fw_parser.add_argument("-n", "--name", help="get FWs with this name")
    get_fw_parser.add_argument(*state_args, **state_kwargs)
    get_fw_parser.add_argument(*query_args, **query_kwargs)
    get_fw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    get_fw_parser.add_argument(*qid_args, **qid_kwargs)
    get_fw_parser.add_argument(*disp_args, **disp_kwargs)
    get_fw_parser.add_argument("-m", "--max", help="limit results", default=0, type=int)
    get_fw_parser.add_argument("--sort", help="Sort results", choices=["created_on", "updated_on"])
    get_fw_parser.add_argument("--rsort", help="Reverse sort results", choices=["created_on", "updated_on"])
    get_fw_parser.set_defaults(func=get_fws)

    get_fw_in_wf_parser = subparsers.add_parser(
        "get_fws_in_wflows", help="get information about FireWorks in Workflows"
    )

    get_fw_in_wf_parser.add_argument(*wf_prefixed_fw_id_args, **fw_id_kwargs)
    get_fw_in_wf_parser.add_argument("-wfn", "--wf_name", help="get WFs with this name")
    get_fw_in_wf_parser.add_argument(*wf_prefixed_state_args, **state_kwargs)
    get_fw_in_wf_parser.add_argument(*wf_prefixed_query_args, **query_kwargs)

    get_fw_in_wf_parser.add_argument(*fw_prefixed_fw_id_args, **fw_id_kwargs)
    get_fw_in_wf_parser.add_argument("-fwn", "--fw_name", help="get FWs with this name")
    get_fw_in_wf_parser.add_argument(*fw_prefixed_state_args, **state_kwargs)
    get_fw_in_wf_parser.add_argument(*fw_prefixed_query_args, **query_kwargs)
    get_fw_in_wf_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    get_fw_in_wf_parser.add_argument(*qid_args, **qid_kwargs)
    get_fw_in_wf_parser.add_argument(*disp_args, **disp_kwargs)
    get_fw_in_wf_parser.add_argument("-m", "--max", help="limit results", default=0, type=int)
    get_fw_in_wf_parser.add_argument("--sort", help="Sort results", choices=["created_on", "updated_on"])
    get_fw_in_wf_parser.add_argument("--rsort", help="Reverse sort results", choices=["created_on", "updated_on"])
    get_fw_in_wf_parser.set_defaults(func=get_fws_in_wfs)

    trackfw_parser = subparsers.add_parser("track_fws", help="Track FireWorks")
    trackfw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    trackfw_parser.add_argument("-n", "--name", help="name")
    trackfw_parser.add_argument(*state_args, **state_kwargs)
    trackfw_parser.add_argument(*query_args, **query_kwargs)
    trackfw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    trackfw_parser.add_argument("-c", "--include", nargs="+", help="only include these files in the report")
    trackfw_parser.add_argument("-x", "--exclude", nargs="+", help="exclude these files from the report")
    trackfw_parser.add_argument("-m", "--max", help="limit results", default=0, type=int)
    trackfw_parser.set_defaults(func=track_fws)

    rerun_fws_parser = subparsers.add_parser("rerun_fws", help="re-run Firework(s)")
    rerun_fws_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    rerun_fws_parser.add_argument("-n", "--name", help="name")
    rerun_fws_parser.add_argument(*state_args, **state_kwargs)
    rerun_fws_parser.add_argument(*query_args, **query_kwargs)
    rerun_fws_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    rerun_fws_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    rerun_fws_parser.add_argument("--task-level", action="store_true", help="Enable task level recovery")
    rerun_fws_parser.add_argument(
        "-lid", "--launch_id", nargs="+", help="Recover launch id. --task-level must be given", default=None, type=int
    )
    recover_mode_group = rerun_fws_parser.add_mutually_exclusive_group()
    recover_mode_group.add_argument(
        "-cp",
        "--copy-data",
        action="store_const",
        const="cp",
        dest="recover_mode",
        help="Copy data from previous run. --task-level must be given",
    )
    recover_mode_group.add_argument(
        "-pd",
        "--previous-dir",
        action="store_const",
        const="prev_dir",
        dest="recover_mode",
        help="Reruns in the previous folder. --task-level must be given",
    )
    rerun_fws_parser.set_defaults(func=rerun_fws)

    defuse_fw_parser = subparsers.add_parser("defuse_fws", help="cancel (de-fuse) a single Firework")
    defuse_fw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    defuse_fw_parser.add_argument("-n", "--name", help="name")
    defuse_fw_parser.add_argument(*state_args, **state_kwargs)
    defuse_fw_parser.add_argument(*query_args, **query_kwargs)
    defuse_fw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    defuse_fw_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    defuse_fw_parser.set_defaults(func=defuse_fws)

    pause_fw_parser = subparsers.add_parser("pause_fws", help="pause a single Firework")
    pause_fw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    pause_fw_parser.add_argument("-n", "--name", help="name")
    pause_fw_parser.add_argument(*state_args, **state_kwargs)
    pause_fw_parser.add_argument(*query_args, **query_kwargs)
    pause_fw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    pause_fw_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    pause_fw_parser.set_defaults(func=pause_fws)

    reignite_fw_parser = subparsers.add_parser("reignite_fws", help="reignite (un-cancel) a set of Fireworks")
    reignite_fw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    reignite_fw_parser.add_argument("-n", "--name", help="name")
    reignite_fw_parser.add_argument(*state_args, **state_kwargs)
    reignite_fw_parser.add_argument(*query_args, **query_kwargs)
    reignite_fw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    reignite_fw_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    reignite_fw_parser.set_defaults(func=reignite_fws)

    resume_fw_parser = subparsers.add_parser("resume_fws", help="resume (un-pause) a set of Fireworks")
    resume_fw_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    resume_fw_parser.add_argument("-n", "--name", help="name")
    resume_fw_parser.add_argument(*state_args, **state_kwargs)
    resume_fw_parser.add_argument(*query_args, **query_kwargs)
    resume_fw_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    resume_fw_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    resume_fw_parser.set_defaults(func=resume_fws)

    update_fws_parser = subparsers.add_parser("update_fws", help="Update a Firework spec.")
    update_fws_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    update_fws_parser.add_argument("-n", "--name", help="get FWs with this name")
    update_fws_parser.add_argument(*state_args, **state_kwargs)
    update_fws_parser.add_argument(*query_args, **query_kwargs)
    update_fws_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    update_fws_parser.add_argument(
        "-u",
        "--update",
        type=str,
        help="Doc update (enclose pymongo-style dict in single-quotes, e.g. '{" '"_tasks.1.hello": "world"}\')',
    )
    update_fws_parser.add_argument(
        "--mongo",
        default=False,
        action="store_true",
        help="Use full pymongo style dict to modify spec. Be very careful as you can break your spec",
    )
    update_fws_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    update_fws_parser.set_defaults(func=update_fws)

    get_wf_parser = subparsers.add_parser("get_wflows", help="get information about Workflows")
    get_wf_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    get_wf_parser.add_argument("-n", "--name", help="get WFs with this name")
    get_wf_parser.add_argument(*state_args, **state_kwargs)
    get_wf_parser.add_argument(*query_args, **query_kwargs)
    get_wf_parser.add_argument(*disp_args, **disp_kwargs)
    get_wf_parser.add_argument("-m", "--max", help="limit results", default=0, type=int)
    get_wf_parser.add_argument("--sort", help="Sort results", choices=["created_on", "updated_on"])
    get_wf_parser.add_argument("--rsort", help="Reverse sort results", choices=["created_on", "updated_on"])
    get_wf_parser.add_argument(
        "-t",
        "--table",
        help="Print results in table form instead of json. Needs prettytable. Works best " 'with "-d less"',
        action="store_true",
    )
    get_wf_parser.set_defaults(func=get_wfs)

    defuse_wf_parser = subparsers.add_parser("defuse_wflows", help="cancel (de-fuse) an entire Workflow")
    defuse_wf_parser.add_argument(
        "--defuse_all_states", help="also defuse COMPLETED and FIZZLED workflows", action="store_true"
    )
    defuse_wf_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    defuse_wf_parser.add_argument("-n", "--name", help="name")
    defuse_wf_parser.add_argument(*state_args, **state_kwargs)
    defuse_wf_parser.add_argument(*query_args, **query_kwargs)
    defuse_wf_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    defuse_wf_parser.set_defaults(func=pause_wfs)

    pause_wf_parser = subparsers.add_parser("pause_wflows", help="pause an entire Workflow")
    pause_wf_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    pause_wf_parser.add_argument("-n", "--name", help="name")
    pause_wf_parser.add_argument(*state_args, **state_kwargs)
    pause_wf_parser.add_argument(*query_args, **query_kwargs)
    pause_wf_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    pause_wf_parser.set_defaults(func=pause_wfs)

    reignite_wfs_parser = subparsers.add_parser("reignite_wflows", help="reignite (un-cancel) an entire Workflow")
    reignite_wfs_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    reignite_wfs_parser.add_argument("-n", "--name", help="name")
    reignite_wfs_parser.add_argument(*state_args, **state_kwargs)
    reignite_wfs_parser.add_argument(*query_args, **query_kwargs)
    reignite_wfs_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    reignite_wfs_parser.set_defaults(func=reignite_wfs)

    archive_parser = subparsers.add_parser("archive_wflows", help="archive an entire Workflow (irreversible)")
    archive_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    archive_parser.add_argument("-n", "--name", help="name")
    archive_parser.add_argument(*state_args, **state_kwargs)
    archive_parser.add_argument(*query_args, **query_kwargs)
    archive_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    archive_parser.set_defaults(func=archive)

    delete_wfs_parser = subparsers.add_parser(
        "delete_wflows",
        help='Delete workflows (permanently). Use "archive_wflows" instead if ' 'you want to "soft-remove"',
    )
    delete_wfs_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    delete_wfs_parser.add_argument("-n", "--name", help="name")
    delete_wfs_parser.add_argument(*state_args, **state_kwargs)
    delete_wfs_parser.add_argument(*query_args, **query_kwargs)
    delete_wfs_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    delete_wfs_parser.add_argument(
        "--ldirs",
        help="the launch directories associated with the WF will be deleted as well, if possible",
        dest="delete_launch_dirs",
        action="store_true",
    )
    delete_wfs_parser.set_defaults(func=delete_wfs, delete_launch_dirs=False)

    get_qid_parser = subparsers.add_parser("get_qids", help="get the queue id of a Firework")
    get_qid_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    get_qid_parser.set_defaults(func=get_qid)

    cancel_qid_parser = subparsers.add_parser("cancel_qid", help="cancel a reservation")
    cancel_qid_parser.add_argument(*qid_args, **qid_kwargs)
    cancel_qid_parser.set_defaults(func=cancel_qid)

    reservation_parser = subparsers.add_parser("detect_unreserved", help="Find launches with stale reservations")
    reservation_parser.add_argument(
        "--time", help="expiration time (seconds)", default=RESERVATION_EXPIRATION_SECS, type=int
    )
    reservation_parser.add_argument("--rerun", help="cancel and rerun expired reservations", action="store_true")
    reservation_parser.add_argument(*enh_disp_args, **enh_disp_kwargs)
    reservation_parser.set_defaults(func=detect_unreserved)

    fizzled_parser = subparsers.add_parser("detect_lostruns", help="Find launches that have FIZZLED")
    fizzled_parser.add_argument("--time", help="expiration time (seconds)", default=RUN_EXPIRATION_SECS, type=int)
    fizzled_parser.add_argument("--fizzle", help="mark lost runs as fizzled", action="store_true")
    fizzled_parser.add_argument("--rerun", help="rerun lost runs", action="store_true")
    fizzled_parser.add_argument("--refresh", help="refresh the detected inconsistent fireworks", action="store_true")
    fizzled_parser.add_argument(
        "--max_runtime", help="max runtime, matching failures ran no longer than this (seconds)", type=int
    )
    fizzled_parser.add_argument(
        "--min_runtime", help="min runtime, matching failures must have run at least this long (seconds)", type=int
    )
    fizzled_parser.add_argument("-q", "--query", help="restrict search to only FWs matching this query")
    fizzled_parser.add_argument("-lq", "--launch_query", help="restrict search to only launches matching this query")
    fizzled_parser.add_argument(*enh_disp_args, **enh_disp_kwargs)
    fizzled_parser.set_defaults(func=detect_lostruns)

    priority_parser = subparsers.add_parser("set_priority", help="modify the priority of one or more FireWorks")
    priority_parser.add_argument("priority", help="get FW with this fw_id", default=None, type=int)
    priority_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    priority_parser.add_argument("-n", "--name", help="name")
    priority_parser.add_argument(*state_args, **state_kwargs)
    priority_parser.add_argument(*query_args, **query_kwargs)
    priority_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    priority_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    priority_parser.add_argument(
        "-wf", action="store_true", help="the priority will be set for all the fireworks of the matching workflows"
    )
    priority_parser.set_defaults(func=set_priority)

    parser.add_argument(
        "-l", "--launchpad_file", help="path to LaunchPad file containing central DB connection info", default=None
    )
    parser.add_argument(
        "-c",
        "--config_dir",
        help="path to a directory containing the LaunchPad file (used if -l unspecified)",
        default=CONFIG_FILE_DIR,
    )
    parser.add_argument("--logdir", help="path to a directory for logging")
    parser.add_argument("--loglvl", help="level to print log messages", default="INFO")
    parser.add_argument("-s", "--silencer", help="shortcut to mute log messages", action="store_true")

    webgui_parser = subparsers.add_parser("webgui", help="launch the web GUI")
    webgui_parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=WEBSERVER_PORT,
        help="Port to run the web server on (default: 5000 or WEBSERVER_PORT arg in FW_config.yaml)",
    )
    webgui_parser.add_argument(
        "--host",
        dest="host",
        type=str,
        default=WEBSERVER_HOST,
        help="Host to run the web server on (default: 127.0.0.1 or WEBSERVER_HOST arg in FW_config.yaml)",
    )
    webgui_parser.add_argument("--debug", help="print debug messages", action="store_true")
    webgui_parser.add_argument(
        "-s", "--server_mode", help="run in server mode (skip opening the browser)", action="store_true"
    )
    webgui_parser.add_argument(
        "--nworkers", type=arg_positive_int, help="Number of worker processes for server mode", default=1
    )
    webgui_parser.add_argument("--fwquery", help="additional query filter for FireWorks as JSON string")
    webgui_parser.add_argument("--wflowquery", help="additional query filter for Workflows as JSON string")
    webgui_parser.add_argument(
        "--webgui_username", help="Optional username needed to access webgui", type=str, default=None
    )
    webgui_parser.add_argument(
        "--webgui_password", help="Optional password needed to access webgui", type=str, default=None
    )
    webgui_parser.set_defaults(func=webgui)

    recover_parser = subparsers.add_parser("recover_offline", help="recover offline workflows")
    recover_parser.add_argument("-i", "--ignore_errors", help="ignore errors", action="store_true")
    recover_parser.add_argument(
        "-w",
        "--fworker_file",
        help="path to fworker file. An empty string will match all the workers",
        default=FWORKER_LOC,
    )
    recover_parser.add_argument("-pe", "--print-errors", help="print errors", action="store_true")
    recover_parser.set_defaults(func=recover_offline)

    forget_parser = subparsers.add_parser("forget_offline", help="forget offline workflows")
    forget_parser.add_argument("-n", "--name", help="name")
    forget_parser.add_argument(*state_args, **state_kwargs)
    forget_parser.add_argument(*query_args, **query_kwargs)
    forget_parser.set_defaults(func=forget_offline)

    # admin commands
    admin_parser = subparsers.add_parser(
        "admin", help="Various db admin commands, " 'type "lpad admin -h" for more.', parents=[parent_parser]
    )
    admin_subparser = admin_parser.add_subparsers(title="action", dest="action_command")

    maintain_parser = admin_subparser.add_parser("maintain", help="Run database maintenance")
    maintain_parser.add_argument("--infinite", help="loop infinitely", action="store_true")
    maintain_parser.add_argument(
        "--maintain_interval",
        help="sleep time between maintenance loops (infinite mode)",
        default=MAINTAIN_INTERVAL,
        type=int,
    )
    maintain_parser.set_defaults(func=maintain)

    orphaned_parser = admin_subparser.add_parser("orphaned", help="Find orphaned FireWorks")
    orphaned_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    orphaned_parser.add_argument("-n", "--name", help="get FWs with this name")
    orphaned_parser.add_argument(*state_args, **state_kwargs)
    orphaned_parser.add_argument(*query_args, **query_kwargs)
    orphaned_parser.add_argument(*launches_mode_args, **launches_mode_kwargs)
    orphaned_parser.add_argument(*qid_args, **qid_kwargs)
    orphaned_parser.add_argument(*disp_args, **disp_kwargs)
    orphaned_parser.add_argument("-m", "--max", help="limit results", default=0, type=int)
    orphaned_parser.add_argument("--sort", help="Sort results", choices=["created_on", "updated_on"])
    orphaned_parser.add_argument("--rsort", help="Reverse sort results", choices=["created_on", "updated_on"])
    orphaned_parser.add_argument("--remove", help="delete orphaned", action="store_true")
    orphaned_parser.add_argument(
        "--ldirs",
        help="the launch directories associated with the orphaned Fireworks will be deleted as well, if possible",
        dest="delete_launch_dirs",
        action="store_true",
    )
    orphaned_parser.set_defaults(func=orphaned)

    tuneup_parser = admin_subparser.add_parser(
        "tuneup", help="Tune-up the database (should be performed during scheduled downtime)"
    )
    tuneup_parser.add_argument(
        "--full", help="Run full tuneup and compaction (should be run during DB downtime only)", action="store_true"
    )
    tuneup_parser.set_defaults(func=tuneup)

    refresh_parser = admin_subparser.add_parser(
        "refresh", help="manually force a workflow refresh (not usually needed)"
    )
    refresh_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    refresh_parser.add_argument("-n", "--name", help="name")
    refresh_parser.add_argument(*state_args, **state_kwargs)
    refresh_parser.add_argument(*query_args, **query_kwargs)
    refresh_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    refresh_parser.set_defaults(func=refresh)

    unlock_parser = admin_subparser.add_parser(
        "unlock", help="manually unlock a workflow that is locked (only if you know what you are doing!)"
    )
    unlock_parser.add_argument(*fw_id_args, **fw_id_kwargs)
    unlock_parser.add_argument("-n", "--name", help="name")
    unlock_parser.add_argument(*state_args, **state_kwargs)
    unlock_parser.add_argument(*query_args, **query_kwargs)
    unlock_parser.add_argument(
        "--password",
        help="Today's date, e.g. 2012-02-25. Password or positive response to "
        f"input prompt required when modifying more than {PW_CHECK_NUM} entries.",
    )
    unlock_parser.set_defaults(func=unlock)

    report_parser = subparsers.add_parser(
        "report", help="Compile a report of runtime stats, " 'type "lpad report -h" for more options.'
    )
    report_parser.add_argument(
        "-c",
        "--collection",
        help="The collection to report on; choose from 'fws' (default), 'wflows', or 'launches'.",
        default="fws",
    )
    report_parser.add_argument(
        "-i",
        "--interval",
        help="Interval on which to split the report. "
        "Choose from 'minutes', 'hours', "
        "'days' (default), 'months', or 'years'.",
        default="days",
    )
    report_parser.add_argument(
        "-n", "--num_intervals", help="The number of intervals on which to report (default=5)", type=int, default=5
    )
    report_parser.add_argument("-q", "--query", help="Additional Pymongo queries to filter entries before processing.")
    report_parser.set_defaults(func=report)

    introspect_parser = subparsers.add_parser("introspect", help="Introspect recent runs to pin down errors")
    introspect_parser.add_argument("-m", "--max", help="examine past <max> results", default=100, type=int)
    introspect_parser.add_argument(
        "-t",
        "--threshold",
        help="controls signal to noise ratio, e.g., 10 means "
        "difference of at least 10 runs between fizzled/completed count",
        default=10,
        type=int,
    )
    introspect_parser.set_defaults(func=introspect)

    try:
        import argcomplete

        argcomplete.autocomplete(parser)
        # This supports bash autocompletion. To enable this, pip install
        # argcomplete, activate global completion, or add
        #      eval "$(register-python-argcomplete lpad)"
        # into your .bash_profile or .bashrc
    except ImportError:
        pass

    args = parser.parse_args()

    args.output = get_output_func(args.output)

    if args.command is None:
        # if no command supplied, print help
        parser.print_help()
    else:
        for opt in fw_id_options:
            if hasattr(args, opt) and getattr(args, opt) is not None and isinstance(getattr(args, opt), str):
                if "," in getattr(args, opt):
                    setattr(args, opt, [int(x) for x in getattr(args, opt).split(",")])
                else:
                    setattr(args, opt, [int(getattr(args, opt))])

        args.func(args)


if __name__ == "__main__":
    lpad()
