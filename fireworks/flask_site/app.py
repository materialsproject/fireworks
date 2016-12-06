from flask import Flask, render_template, request, jsonify, Response
from flask import redirect, url_for, abort
from fireworks import Firework
from fireworks.features.fw_report import FWReport
from fireworks.utilities.fw_serializers import DATETIME_HANDLER
from pymongo import DESCENDING
import os, json
from fireworks.core.launchpad import LaunchPad
from flask_paginate import Pagination
from functools import wraps

app = Flask(__name__)
app.use_reloader = True
hello = __name__
lp = LaunchPad.from_dict(json.loads(os.environ["FWDB_CONFIG"]))
app.BASE_Q = {}
app.BASE_Q_WF = {}

PER_PAGE = 20
STATES = Firework.STATE_RANKS.keys()

AUTH_USER = os.environ.get("FWAPP_AUTH_USERNAME", None)
AUTH_PASSWD = os.environ.get("FWAPP_AUTH_PASSWORD", None)


def check_auth(username, password):
    """
    This function is called to check if a username /
    password combination is valid.
    """
    if (AUTH_USER is None) or (AUTH_PASSWD is None):
        return True
    return username == AUTH_USER and password == AUTH_PASSWD


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL. You have to login '
        'with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if (AUTH_USER is not None) and (not auth or not check_auth(
                auth.username, auth.password)):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def _addq(base, q):
    return {"$and": [q, base]} if base else q


@app.template_filter('datetime')
def datetime(value):
    import datetime as dt

    date = dt.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
    return date.strftime('%m/%d/%Y')


@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    if number == 1:
        return singular
    else:
        return plural


@app.route("/")
@requires_auth
def home():
    fw_nums = []
    wf_nums = []
    for state in STATES:
        fw_nums.append(lp.get_fw_ids(query=_addq(app.BASE_Q, {'state': state}),
                                     count_only=True))
        wf_nums.append(
            lp.get_wf_ids(query=_addq(app.BASE_Q_WF, {'state': state}),
                          count_only=True))
    state_nums = zip(STATES, fw_nums, wf_nums)

    tot_fws = sum(fw_nums)
    tot_wfs = sum(wf_nums)

    # Newest Workflows table data
    wfs_shown = lp.workflows.find(app.BASE_Q_WF, limit=PER_PAGE,
                                  sort=[('_id', DESCENDING)])
    wf_info = []
    for item in wfs_shown:
        wf_info.append({
            "id": item['nodes'][0],
            "name": item['name'],
            "state": item['state'],
            "fireworks": list(
                lp.fireworks.find({"fw_id": {"$in": item["nodes"]}},
                                  limit=PER_PAGE, sort=[('fw_id', DESCENDING)],
                                  projection=["state", "name", "fw_id"]))
        })
    return render_template('home.html', **locals())


@app.route('/fw/<int:fw_id>/details')
@requires_auth
def get_fw_details(fw_id):
    # just fill out whatever attributse you want to see per step, then edit the handlebars template in
    # wf_details.html
    # to control their display
    fw = lp.get_fw_dict_by_id(fw_id)
    for launch in fw['launches']:
        del launch['_id']
    del fw['_id']
    return jsonify(fw)


@app.route('/fw/<int:fw_id>')
@requires_auth
def fw_details(fw_id):
    try:
        int(fw_id)
    except:
        raise ValueError("Invalid fw_id: {}".format(fw_id))
    fw = lp.get_fw_dict_by_id(fw_id)
    fw = json.loads(
        json.dumps(fw, default=DATETIME_HANDLER))  # formats ObjectIds
    return render_template('fw_details.html', **locals())


@app.route('/wf/<int:wf_id>/json')
@requires_auth
def workflow_json(wf_id):
    try:
        int(wf_id)
    except ValueError:
        raise ValueError("Invalid fw_id: {}".format(wf_id))

    # TODO: modify so this doesn't duplicate the .css file that contains the same colors
    state_to_color = {"RUNNING": "#F4B90B",
                      "WAITING": "#1F62A2",
                      "FIZZLED": "#DB0051",
                      "READY": "#2E92F2",
                      "COMPLETED": "#24C75A",
                      "RESERVED": "#BB8BC1",
                      "ARCHIVED": "#7F8287",
                      "DEFUSED": "#B7BCC3"
                      }

    wf = lp.workflows.find_one({'nodes': wf_id})
    fireworks = list(lp.fireworks.find({"fw_id": {"$in": wf["nodes"]}},
                                       projection=["name", "fw_id", "state"]))
    nodes_and_edges = {'nodes': list(), 'edges': list()}
    for fw in fireworks:
        fw_id = fw['fw_id']
        node_obj = dict()
        node_obj['id'] = fw_id
        node_obj['name'] = fw["name"]
        node_obj['state'] = state_to_color[fw["state"]]
        node_obj['width'] = len(node_obj['name']) * 10
        nodes_and_edges['nodes'].append({'data': node_obj})
        if str(fw_id) in wf['links']:
            for link in wf['links'][str(fw_id)]:
                link_object = dict()
                link_object['source'] = str(fw_id)
                link_object['target'] = str(link)
                nodes_and_edges['edges'].append({'data': link_object})
    return jsonify(nodes_and_edges)


@app.route('/wf/<int:wf_id>')
@requires_auth
def wf_details(wf_id):
    try:
        int(wf_id)
    except ValueError:
        raise ValueError("Invalid fw_id: {}".format(wf_id))
    wf = lp.get_wf_summary_dict(wf_id, mode="all")
    wf = json.loads(
        json.dumps(wf, default=DATETIME_HANDLER))  # formats ObjectIds
    all_states = list(set(wf["states"].values()))
    return render_template('wf_details.html', **locals())


@app.route('/fw/', defaults={"state": "total"})
@app.route("/fw/<state>/")
@requires_auth
def fw_state(state):
    db = lp.fireworks
    q = {} if state == "total" else {"state": state}
    q = _addq(app.BASE_Q, q)
    fw_count = lp.get_fw_ids(query=q, count_only=True)
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    rows = list(db.find(q, projection=["fw_id", "name", "created_on"]).sort(
        [('_id', DESCENDING)]).skip(
        (page - 1) * PER_PAGE).limit(PER_PAGE))
    pagination = Pagination(page=page, total=fw_count, record_name='fireworks',
                            per_page=PER_PAGE)
    return render_template('fw_state.html', **locals())


@app.route('/wf/', defaults={"state": "total"})
@app.route("/wf/<state>/")
@requires_auth
def wf_state(state):
    db = lp.workflows
    q = {} if state == "total" else {"state": state}
    q = _addq(app.BASE_Q_WF, q)
    wf_count = lp.get_wf_ids(query=q, count_only=True)
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    rows = list(db.find(q).sort([('_id', DESCENDING)]).skip(
        (page - 1) * PER_PAGE).limit(PER_PAGE))
    for r in rows:
        r["fw_id"] = r["nodes"][0]
    pagination = Pagination(page=page, total=wf_count, record_name='workflows',
                            per_page=PER_PAGE)
    return render_template('wf_state.html', **locals())


@app.route("/wf/metadata/<key>/<value>/", defaults={"state": "total"})
@app.route("/wf/metadata/<key>/<value>/<state>/")
@requires_auth
def wf_metadata_find(key, value, state):
    db = lp.workflows
    try:
        value = int(value)
    except ValueError:
        pass
    q = {'metadata.{}'.format(key): value}
    state_mixin = {} if state == "total" else {"state": state}
    q.update(state_mixin)
    q = _addq(app.BASE_Q_WF, q)
    wf_count = lp.get_wf_ids(query=q, count_only=True)
    if wf_count == 0:
        abort(404)
    elif wf_count == 1:
        doc = db.find_one(q, {'nodes': 1, '_id': 0})
        fw_id = doc['nodes'][0]
        return redirect(url_for('wf_details', wf_id=fw_id))
    else:
        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1
        rows = list(db.find(q).sort([('_id', DESCENDING)]). \
                    skip(page - 1).limit(PER_PAGE))
        for r in rows:
            r["fw_id"] = r["nodes"][0]
        pagination = Pagination(page=page, total=wf_count,
                                record_name='workflows', per_page=PER_PAGE)
        all_states = STATES
        return render_template('wf_metadata.html', **locals())


@app.route('/report/', defaults={"interval": "months", "num_intervals": 6})
@app.route('/report/<interval>/', defaults={"num_intervals": 6})
@app.route("/report/<interval>/<num_intervals>/")
@requires_auth
def report(interval, num_intervals):
    num_intervals = int(num_intervals)
    fwr = FWReport(lp)

    fw_report_data = fwr.get_stats(coll="fireworks", interval=interval,
                                   num_intervals=num_intervals,
                                   additional_query=app.BASE_Q)
    fw_report_text = fwr.get_stats_str(fw_report_data)

    wf_report_data = fwr.get_stats(coll="workflows", interval=interval,
                                   num_intervals=num_intervals,
                                   additional_query=app.BASE_Q_WF)
    wf_report_text = fwr.get_stats_str(wf_report_data)

    return render_template('report.html', **locals())


def bootstrap_app(*args, **kwargs):
    """Pass instead of `app` to a forking process.

    This is so a server process will re-initialize a MongoDB client
    connection after forking. This is useful to avoid deadlock when
    using pymongo with multiprocessing.
    """
    import fireworks.flask_site.app
    fireworks.flask_site.app.lp = LaunchPad.from_dict(
        json.loads(os.environ["FWDB_CONFIG"]))
    return app(*args, **kwargs)


if __name__ == "__main__":
    app.run(debug=True, port=8080)
