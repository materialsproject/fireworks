import json
from django.shortcuts import render_to_response
from fireworks.core.launchpad import LaunchPad
from fireworks.utilities.fw_serializers import DATETIME_HANDLER

lp = LaunchPad() #LaunchPad.auto_load()

def home(request):
    arc_fws = lp.fireworks.find({'state':'READY'}).count()
    # arc_fws = len(lp.fireworks.find({'state':'ARCHIVED'}))
    # arc_fws = lp.fireworks.count({'state':'ARCHIVED'})
    print arc_fws
    '''
    arc_fws   = len(lp.get_fw_ids(query={'state':"ARCHIVED"}))
    arc_wfs   = len(lp.get_wf_ids(query={'state':"ARCHIVED"}))
    def_fws   = len(lp.get_fw_ids(query={'state':"DEFUSED"}))
    def_wfs   = len(lp.get_wf_ids(query={'state':"DEFUSED"}))
    wait_fws  = len(lp.get_fw_ids(query={'state':"WAITING"}))
    wait_wfs  = len(lp.get_wf_ids(query={'state':"WAITING"}))
    ready_fws = len(lp.get_fw_ids(query={'state':"READY"}))
    ready_wfs = len(lp.get_wf_ids(query={'state':"READY"}))
    res_fws   = len(lp.get_fw_ids(query={'state':"RESERVED"}))
    res_wfs   = len(lp.get_wf_ids(query={'state':"RESERVED"}))
    fizz_fws  = len(lp.get_fw_ids(query={'state':"FIZZLED"}))
    fizz_wfs  = len(lp.get_wf_ids(query={'state':"FIZZLED"}))
    run_fws   = len(lp.get_fw_ids(query={'state':"RUNNING"}))
    run_wfs   = len(lp.get_wf_ids(query={'state':"RUNNING"}))
    comp_fws  = len(lp.get_fw_ids(query={'state':"COMPLETED"}))
    comp_wfs  = len(lp.get_wf_ids(query={'state':"COMPLETED"}))
    tot_fws   = len(lp.get_fw_ids())
    tot_wfs   = len(lp.get_wf_ids())
    '''
    url = request.get_full_path()
    return render_to_response('home.html', {'arc_fws': arc_fws, ''''arc_wfs': arc_wfs,
        'def_fws': def_fws, 'def_wfs': def_wfs, 'wait_fws': wait_fws, 'wait_wfs': wait_wfs,
        'ready_fws': ready_fws, 'ready_wfs': ready_wfs, 'res_fws': res_fws, 'res_wfs': res_wfs,
        'fizz_fws': fizz_fws, 'fizz_wfs': fizz_wfs, 'run_fws': run_fws, 'run_wfs': run_wfs,
        'comp_fws': comp_fws, 'comp_wfs': comp_wfs, 'tot_fws': tot_fws, 'tot_wfs': tot_wfs,'''
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
