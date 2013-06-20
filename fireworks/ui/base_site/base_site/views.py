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
    # len(lp.get_fw_ids(query={'state':"ARCHIVED"}))
    arc_fws   = lp.fireworks.find({'state':'ARCHIVED'}).count()
    arc_wfs   = lp.workflows.find({'state':'ARCHIVED'}).count()
    def_fws   = lp.fireworks.find({'state':'DEFUSED'}).count()
    def_wfs   = lp.workflows.find({'state':'DEFUSED'}).count()
    wait_fws  = lp.fireworks.find({'state':'WAITING'}).count()
    wait_wfs  = lp.workflows.find({'state':'WAITING'}).count()
    ready_fws = lp.fireworks.find({'state':'READY'}).count()
    ready_wfs = lp.workflows.find({'state':'READY'}).count()
    res_fws   = lp.fireworks.find({'state':'RESERVED'}).count()
    res_wfs   = lp.workflows.find({'state':'RESERVED'}).count()
    fizz_fws  = lp.fireworks.find({'state':'FIZZLED'}).count()
    fizz_wfs  = lp.workflows.find({'state':'FIZZLED'}).count()
    run_fws   = lp.fireworks.find({'state':'RUNNING'}).count()
    run_wfs   = lp.workflows.find({'state':'RUNNING'}).count()
    comp_fws  = lp.fireworks.find({'state':'COMPLETED'}).count()
    comp_wfs  = lp.workflows.find({'state':'COMPLETED'}).count()
    tot_fws   = lp.fireworks.count()
    tot_wfs   = lp.workflows.count()
    url = request.get_full_path()
    return render_to_response('home.html', {'arc_fws': arc_fws, 'arc_wfs': arc_wfs,
        'def_fws': def_fws, 'def_wfs': def_wfs, 'wait_fws': wait_fws, 'wait_wfs': wait_wfs,
        'ready_fws': ready_fws, 'ready_wfs': ready_wfs, 'res_fws': res_fws, 'res_wfs': res_wfs,
        'fizz_fws': fizz_fws, 'fizz_wfs': fizz_wfs, 'run_fws': run_fws, 'run_wfs': run_wfs,
        'comp_fws': comp_fws, 'comp_wfs': comp_wfs, 'tot_fws': tot_fws, 'tot_wfs': tot_wfs,
        'url': url})

def fw(request):
    fws = lp.get_fw_ids()
    url = request.get_full_path()
    return render_to_response('fw.html', {'fw_ids': fws, 'url': url})

def fw_id(request, id):
    fw = lp.get_fw_by_id(int(id))
    str_to_print = json.dumps(fw.to_dict(), default=DATETIME_HANDLER, indent=4)
    return render_to_response('fw_id.html', {'fw_id': id, 'fw_data': str_to_print})

def wf(request):
    wfs = lp.get_wf_ids()
    url = request.get_full_path()
    return render_to_response('wf.html', {'wf_ids': wfs, 'url': url})

def wf_id(request, id):
    wf = lp.get_wf_by_fw_id(int(id))
    str_to_print = json.dumps(wf.to_dict(), default=DATETIME_HANDLER, indent=4)
    return render_to_response('wf_id.html', {'wf_id': id, 'wf_data': str_to_print})
