import os

__author__ = 'Morgan Hargrove'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Morgan Hargrove'
__email__ = 'mhargrove@lbl.gov'
__date__ = 'Jun 13, 2013'

import json
import datetime
import logging
from pymongo import DESCENDING
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.shortcuts import render_to_response
from fireworks.core.launchpad import LaunchPad
from fireworks.utilities.fw_serializers import DATETIME_HANDLER


lp = LaunchPad.from_dict(json.loads(os.environ['FWDB_CONFIG']))

_log = logging.getLogger("fwdash")
hndlr = logging.StreamHandler()
fmtr = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
hndlr.setFormatter(fmtr)
_log.addHandler(hndlr)
_log.setLevel(logging.DEBUG)
_dbg = _log.debug

DEFAULT_PAGELEN = 10

def home(request):
    shown = 20
    comp_fws = lp.get_fw_ids(query={'state': 'COMPLETED'}, count_only=True)

    # Newest Fireworks table data
    _dbg("fireworks.begin")
    fws_shown = lp.fireworks.find({}, limit=shown, sort=[('created_on', DESCENDING)])
    fw_info = []
    for item in fws_shown:
        fw_info.append((item['fw_id'], item['name'], item['state']))
    _dbg("fireworks.end")

    # Current Database Status table data
    _dbg("status.begin")
    states = ['ARCHIVED', 'DEFUSED', 'WAITING', 'READY', 'RESERVED',
        'FIZZLED', 'RUNNING', 'COMPLETED']
    fw_nums = []
    wf_nums = []
    for state in states:
        fw_nums.append(lp.get_fw_ids(query={'state': state}, count_only=True))
        if state == 'WAITING' or state == 'RESERVED':
            wf_nums.append('')
        else:
            wf_nums.append(lp.get_wf_ids(query={'state': state}, count_only=True))
    tot_fws   = lp.get_fw_ids(count_only=True)
    tot_wfs   = lp.get_wf_ids(count_only=True)
    info = zip(states, fw_nums, wf_nums)
    _dbg("status.end")

    # Newest Workflows table data
    _dbg("workflows.begin")
    wfs_shown = lp.workflows.find({}, limit=shown, sort=[('updated_on', DESCENDING)])
    wf_info = []
    for item in wfs_shown:
        wf_info.append((item['nodes'][0], item['name'],item['state']))
    _dbg("workflows.end")

    return render_to_response('home.html', {'fw_info': fw_info, 'info': info,
        'comp_fws': comp_fws, 'tot_fws': tot_fws, 'tot_wfs': tot_wfs, 'wf_info': wf_info})

class QueryResult(object):
    def __init__(self, db, qry, size, sort=None):
        self._db, self._q, self._srt = db, qry, sort
        self._len = size

    def __len__(self):
        return self._len

    def __getslice__(self,  a, b):
        skip, limit = a, b - a 
        _dbg("QueryResult a={} b={}".format(a,b))
        cursor = self._db.find(self._q)
        cursor.skip(skip)
        cursor.sort(*self._srt)
        cursor.limit(limit)
        return [(x['fw_id'], x['name'], x['state']) for x in cursor]

class WFQueryResult(QueryResult):
    def __getslice__(self,  a, b):
        skip, limit = a, b - a 
        _dbg("QueryResult a={} b={}".format(a,b))
        cursor = self._db.find(self._q)
        cursor.skip(skip)
        cursor.sort(*self._srt)
        cursor.limit(limit)
        return [(x['nodes'][0], x['name'], x['state']) for x in cursor]
        
class WFStateQueryResult(QueryResult):
    def __getslice__(self,  a, b):
        skip, limit = a, b - a 
        _dbg("QueryResult a={} b={}".format(a,b))
        cursor = self._db.find(self._q)
        cursor.skip(skip)
        cursor.sort(*self._srt)
        cursor.limit(limit)
        return [(x['nodes'][0], x['name']) for x in cursor]

def fw(request):
    pagelen = DEFAULT_PAGELEN
    db = lp.fireworks
    qry = {}
    fw_count = lp.get_fw_ids(count_only=True)
    rows = QueryResult(lp.fireworks, {}, fw_count, sort=('created_on', -1))

    # pagination
    paginator = Paginator(rows, pagelen)
    page = request.GET.get('page')
    try:
        display = paginator.page(page)
    except PageNotAnInteger:
        display = paginator.page(1)
    except EmptyPage:
        display = paginator.page(paginator.num_pages)

    return render_to_response('fw.html', {'fws': fw_count, 'display': display})

def fw_state(request, state):
    pagelen = DEFAULT_PAGELEN
    db = lp.fireworks
    try:
        state = state.upper()
    except ValueError:
        raise Http404()
    qry = {'state': state}
    fw_count = lp.get_fw_ids(query=qry, count_only=True)
    rows = QueryResult(lp.fireworks, qry, fw_count, sort=('created_on', -1))

    # pagination
    paginator = Paginator(rows, pagelen)
    page = request.GET.get('page')
    try:
        display = paginator.page(page)
    except PageNotAnInteger:
        display = paginator.page(1)
    except EmptyPage:
        display = paginator.page(paginator.num_pages)

    return render_to_response('fw_state.html', {'fws': fw_count, 'state': state, 'display': display})

def fw_id(request, id): # same as fw_id_more
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    fw = lp.get_fw_by_id(id)
    fw_dict = fw.to_dict()
    if 'archived_launches' in fw_dict:
        del fw_dict['archived_launches']
    del fw_dict['spec']
    fw_data = json.dumps(fw_dict, default=DATETIME_HANDLER, indent=4)
    return render_to_response('fw_id.html', {'fw_id': id, 'fw_data': fw_data})

def fw_id_all(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    fw = lp.get_fw_by_id(id)
    fw_data = json.dumps(fw.to_dict(), default=DATETIME_HANDLER, indent=4)
    return render_to_response('fw_id.html', {'fw_id': id, 'fw_data': fw_data})

def fw_id_less(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    fw = lp.get_fw_by_id(id)
    fw_dict = fw.to_dict()
    if 'archived_launches' in fw_dict:
        del fw_dict['archived_launches']
    del fw_dict['spec']
    if 'launches' in fw_dict:
        del fw_dict['launches']
    fw_data = json.dumps(fw_dict, default=DATETIME_HANDLER, indent=4)
    return render_to_response('fw_id.html', {'fw_id': id, 'fw_data': fw_data})

def wf(request):
    pagelen = DEFAULT_PAGELEN
    db = lp.workflows
    qry = {}
    wf_count = lp.get_wf_ids(query=qry, count_only=True)
    rows = WFQueryResult(db, qry, wf_count, sort=('updated_on', -1))

    # pagination
    paginator = Paginator(rows, pagelen)
    page = request.GET.get('page')
    try:
        display = paginator.page(page)
    except PageNotAnInteger:
        display = paginator.page(1)
    except EmptyPage:
        display = paginator.page(paginator.num_pages)

    return render_to_response('wf.html', {'wfs': wf_count, 'display': display})

def wf_state(request, state):
    try:
        state = state.upper()
    except ValueError:
        raise Http404()
    pagelen = DEFAULT_PAGELEN
    db = lp.workflows
    qry = {'state': state}
    wf_count = lp.get_wf_ids(query=qry, count_only=True)
    rows = WFStateQueryResult(db, qry, wf_count, sort=('created_on', -1))

    # pagination
    paginator = Paginator(rows, pagelen)
    page = request.GET.get('page')
    try:
        display = paginator.page(page)
    except PageNotAnInteger:
        display = paginator.page(1)
    except EmptyPage:
        display = paginator.page(paginator.num_pages)

    return render_to_response('wf_state.html', {'wfs': wf_count, 'state': state, 'display': display})

def wf_id(request, id): # same as wf_id_more
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    wf = lp.get_wf_by_fw_id(id)
    wf_dict = wf.to_display_dict()
    del wf_dict['name']
    del wf_dict['parent_links']
    del wf_dict['nodes']
    del wf_dict['links']
    del wf_dict['metadata']
    del wf_dict['states_list']
    wf_data = json.dumps(wf_dict, default=DATETIME_HANDLER, indent=4)
    return render_to_response('wf_id.html', {'wf_id': id, 'wf_data': wf_data})

def wf_id_all(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    wf = lp.get_wf_by_fw_id(id)
    wf_dict = wf.to_display_dict()
    del wf_dict['states_list']
    wf_data = json.dumps(wf_dict, default=DATETIME_HANDLER, indent=4)
    return render_to_response('wf_id.html', {'wf_id': id, 'wf_data': wf_data})

def wf_id_less(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404()
    wf = lp.get_wf_by_fw_id(id)
    wf_dict = wf.to_display_dict()
    del wf_dict['name']
    del wf_dict['parent_links']
    del wf_dict['nodes']
    del wf_dict['links']
    del wf_dict['metadata']
    del wf_dict['states']
    del wf_dict['launch_dirs']
    del wf_dict['updated_on']
    wf_data = json.dumps(wf_dict, default=DATETIME_HANDLER, indent=4)
    return render_to_response('wf_id.html', {'wf_id': id, 'wf_data': wf_data})

def testing(request):
    return render_to_response('testing.html')

def data(request):
    # get list of all dates
    start = datetime.datetime(2013, 05, 15)
    current = datetime.datetime.now()
    dates = []
    query_dates = []
    for i in range((current - start).days + 1):
        new_date = start+datetime.timedelta(days = i)
        dates.append(new_date.strftime('%Y,%m,%d'))
        query_dates.append(new_date.strftime('%Y-%m-%d'))
    # query for fws based on date
    data = []
    for day in query_dates:
        query = day
        data.append(lp.fireworks.find({'created_on': {'$lte': query}}).count())
    info = zip(dates, data)
    return render_to_response('data.html', {'info': info})
