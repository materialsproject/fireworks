__author__ = 'Morgan Hargrove'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Morgan Hargrove'
__email__ = 'mhargrove@lbl.gov'
__date__ = 'Jun 13, 2013'

import json
from pymongo import DESCENDING
from django.shortcuts import render_to_response
from fireworks.core.launchpad import LaunchPad
from fireworks.utilities.fw_serializers import DATETIME_HANDLER

lp = LaunchPad() # LaunchPad.auto_load()

def home(request):
    arc_fws   = lp.get_fw_ids(query={'state':'ARCHIVED'}, count_only=True)
    arc_wfs   = lp.get_wf_ids(query={'state':'ARCHIVED'}, count_only=True)
    def_fws   = lp.get_fw_ids(query={'state':'DEFUSED'}, count_only=True)
    def_wfs   = lp.get_wf_ids(query={'state':'DEFUSED'}, count_only=True)
    wait_fws  = lp.get_fw_ids(query={'state':'WAITING'}, count_only=True)
    wait_wfs  = lp.get_wf_ids(query={'state':'WAITING'}, count_only=True)
    ready_fws = lp.get_fw_ids(query={'state':'READY'}, count_only=True)
    ready_wfs = lp.get_wf_ids(query={'state':'READY'}, count_only=True)
    res_fws   = lp.get_fw_ids(query={'state':'RESERVED'}, count_only=True)
    res_wfs   = lp.get_wf_ids(query={'state':'RESERVED'}, count_only=True)
    fizz_fws  = lp.get_fw_ids(query={'state':'FIZZLED'}, count_only=True)
    fizz_wfs  = lp.get_wf_ids(query={'state':'FIZZLED'}, count_only=True)
    run_fws   = lp.get_fw_ids(query={'state':'RUNNING'}, count_only=True)
    run_wfs   = lp.get_wf_ids(query={'state':'RUNNING'}, count_only=True)
    # run_wfs   = lp.workflows.find({'state':'RUNNING'}).count()
    comp_fws  = lp.get_fw_ids(query={'state':'COMPLETED'}, count_only=True)
    comp_wfs  = lp.get_wf_ids(query={'state':'COMPLETED'}, count_only=True)
    tot_fws   = lp.get_fw_ids(count_only=True)
    tot_wfs   = lp.get_wf_ids(count_only=True)
    return render_to_response('home.html', {'arc_fws': arc_fws, 'arc_wfs': arc_wfs,
        'def_fws': def_fws, 'def_wfs': def_wfs, 'wait_fws': wait_fws, 'wait_wfs': wait_wfs,
        'ready_fws': ready_fws, 'ready_wfs': ready_wfs, 'res_fws': res_fws, 'res_wfs': res_wfs,
        'fizz_fws': fizz_fws, 'fizz_wfs': fizz_wfs, 'run_fws': run_fws, 'run_wfs': run_wfs,
        'comp_fws': comp_fws, 'comp_wfs': comp_wfs, 'tot_fws': tot_fws, 'tot_wfs': tot_wfs})

def fw(request):
    fws = lp.get_fw_ids(count_only=True)
    ids_shown = 20
    fws_shown = lp.get_fw_ids(limit=ids_shown, sort=[('created_on', DESCENDING)])
    return render_to_response('fw.html', {'fws': fws, 'fws_shown': fws_shown})

def fw_id(request, id):
    fw = lp.get_fw_by_id(int(id))
    str_to_print = json.dumps(fw.to_dict(), default=DATETIME_HANDLER, indent=4)
    return render_to_response('fw_id.html', {'fw_id': id, 'fw_data': str_to_print})

def wf(request):
    wfs = lp.get_wf_ids(count_only=True)
    ids_shown = 20
    wfs_shown = lp.get_wf_ids(limit=ids_shown, sort=[('updated_on', DESCENDING)])
    return render_to_response('wf.html', {'wfs': wfs, 'wfs_shown': wfs_shown})

def wf_id(request, id):
    wf = lp.get_wf_by_fw_id(int(id))
    str_to_print = json.dumps(wf.to_dict(), default=DATETIME_HANDLER, indent=4)
    return render_to_response('wf_id.html', {'wf_id': id, 'wf_data': str_to_print})

def testing(request):
    shown = 5
    fws = lp.get_fw_ids(limit=shown, sort=[('created_on', DESCENDING)])
    fw_names = []
    for fw in fws:
        fw_names.append(lp.get_fw_by_id(fw).name)

    arc_fws   = lp.get_fw_ids(query={'state':'ARCHIVED'}, count_only=True)
    arc_wfs   = lp.get_wf_ids(query={'state':'ARCHIVED'}, count_only=True)
    def_fws   = lp.get_fw_ids(query={'state':'DEFUSED'}, count_only=True)
    def_wfs   = lp.get_wf_ids(query={'state':'DEFUSED'}, count_only=True)
    wait_fws  = lp.get_fw_ids(query={'state':'WAITING'}, count_only=True)
    wait_wfs  = lp.get_wf_ids(query={'state':'WAITING'}, count_only=True)
    ready_fws = lp.get_fw_ids(query={'state':'READY'}, count_only=True)
    ready_wfs = lp.get_wf_ids(query={'state':'READY'}, count_only=True)
    res_fws   = lp.get_fw_ids(query={'state':'RESERVED'}, count_only=True)
    res_wfs   = lp.get_wf_ids(query={'state':'RESERVED'}, count_only=True)
    fizz_fws  = lp.get_fw_ids(query={'state':'FIZZLED'}, count_only=True)
    fizz_wfs  = lp.get_wf_ids(query={'state':'FIZZLED'}, count_only=True)
    run_fws   = lp.get_fw_ids(query={'state':'RUNNING'}, count_only=True)
    run_wfs   = lp.get_wf_ids(query={'state':'RUNNING'}, count_only=True)
    # run_wfs   = lp.workflows.find({'state':'RUNNING'}).count()
    comp_fws  = lp.get_fw_ids(query={'state':'COMPLETED'}, count_only=True)
    comp_wfs  = lp.get_wf_ids(query={'state':'COMPLETED'}, count_only=True)
    tot_fws   = lp.get_fw_ids(count_only=True)
    tot_wfs   = lp.get_wf_ids(count_only=True)

    return render_to_response('testing.html', {'fws': fws, 'fw_names': fw_names, 'arc_fws': arc_fws, 'arc_wfs': arc_wfs,
        'def_fws': def_fws, 'def_wfs': def_wfs, 'wait_fws': wait_fws, 'wait_wfs': wait_wfs,
        'ready_fws': ready_fws, 'ready_wfs': ready_wfs, 'res_fws': res_fws, 'res_wfs': res_wfs,
        'fizz_fws': fizz_fws, 'fizz_wfs': fizz_wfs, 'run_fws': run_fws, 'run_wfs': run_wfs,
        'comp_fws': comp_fws, 'comp_wfs': comp_wfs, 'tot_fws': tot_fws, 'tot_wfs': tot_wfs})