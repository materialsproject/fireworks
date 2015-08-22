from flask import Flask, render_template, request
from fireworks import Firework
from fireworks.utilities.fw_serializers import DATETIME_HANDLER
from pymongo import DESCENDING
import os, json
from fireworks.core.launchpad import LaunchPad
from flask.ext.paginate import Pagination

app = Flask(__name__)
app.use_reloader=True
hello = __name__
lp = LaunchPad.from_dict(json.loads(os.environ["FWDB_CONFIG"]))
PER_PAGE = 20
STATES = Firework.STATE_RANKS.keys()


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
def home():
    fw_nums = []
    wf_nums = []
    for state in STATES:
        fw_nums.append(lp.get_fw_ids(query={'state': state}, count_only=True))
        wf_nums.append(lp.get_wf_ids(query={'state': state}, count_only=True))
    state_nums = zip(STATES, fw_nums, wf_nums)

    tot_fws = sum(fw_nums)
    tot_wfs = sum(wf_nums)

    # Newest Workflows table data
    wfs_shown = lp.workflows.find({}, limit=PER_PAGE, sort=[('_id', DESCENDING)])
    wf_info = []
    for item in wfs_shown:
        wf_info.append({
            "id": item['nodes'][0],
            "name": item['name'],
            "state": item['state'],
            "fireworks": list(lp.fireworks.find({"fw_id": {"$in": item["nodes"]}},
                                                limit=PER_PAGE, sort=[('fw_id', DESCENDING)],
                                                projection=["state", "name", "fw_id"]))
        })
    return render_template('home.html', **locals())


@app.route('/fw/<int:fw_id>')
def show_fw(fw_id):
    try:
        int(fw_id)
    except:
        raise ValueError("Invalid fw_id: {}".format(fw_id))
    fw = lp.get_fw_dict_by_id(fw_id)
    fw = json.loads(json.dumps(fw, default=DATETIME_HANDLER))  # formats ObjectIds
    return render_template('fw_details.html', **locals())


@app.route('/wf/<int:wf_id>')
def show_workflow(wf_id):
    try:
        int(wf_id)
    except ValueError:
        raise ValueError("Invalid fw_id: {}".format(wf_id))
    wf = lp.get_wf_summary_dict(wf_id)
    wf = json.loads(json.dumps(wf, default=DATETIME_HANDLER))  # formats ObjectIds
    return render_template('wf_details.html', **locals())


@app.route('/fw/', defaults={"state": "total"})
@app.route("/fw/<state>/")
def fw_states(state):
    db = lp.fireworks
    q = {} if state == "total" else {"state": state}
    fw_count = lp.get_fw_ids(query=q, count_only=True)
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    rows = list(db.find(q, projection=["fw_id", "name", "created_on"]).sort([('_id', DESCENDING)]).skip(page - 1).limit(
        PER_PAGE))
    pagination = Pagination(page=page, total=fw_count, record_name='fireworks', per_page=PER_PAGE)
    all_states = STATES
    return render_template('fw_state.html', **locals())


@app.route('/wf/', defaults={"state": "total"})
@app.route("/wf/<state>/")
def wf_states(state):
    db = lp.workflows
    q = {} if state == "total" else {"state": state}
    wf_count = lp.get_fw_ids(query=q, count_only=True)
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    rows = list(db.find(q).sort([('_id', DESCENDING)]).skip(page - 1).limit(PER_PAGE))
    for r in rows:
        r["fw_id"] = r["nodes"][0]
    pagination = Pagination(page=page, total=wf_count, record_name='workflows', per_page=PER_PAGE)
    all_states = STATES
    return render_template('wf_state.html', **locals())


if __name__ == "__main__":
    app.run(debug=True, port=8080)
