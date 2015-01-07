from flask import Flask, url_for, render_template, request
from fireworks.utilities.fw_serializers import DATETIME_HANDLER
from pymongo import DESCENDING
import os, json
from fireworks.core.launchpad import LaunchPad
from helpers import get_totals
from flask.ext.paginate import Pagination

app = Flask(__name__)
app.debug = True
app.use_reloader=True
hello = __name__
lp = LaunchPad.from_dict(json.loads(os.environ["FWDB_CONFIG"]))
PER_PAGE = 20
STATES = "archived defused waiting ready reserved fizzled running completed".upper().split(" ")

@app.template_filter('datetime')
def datetime(value):
  import datetime as dt
  date = dt.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
  return date.strftime('%m/%d/%Y')

@app.template_filter('pluralize')
def pluralize(number, singular = '', plural = 's'):
    if number == 1:
        return singular
    else:
        return plural

@app.route("/")
def home():
    comp_fws = lp.get_fw_ids(query={'state': 'COMPLETED'}, count_only=True)
    # Newest Fireworks table data
    fws_shown = lp.fireworks.find({}, limit=PER_PAGE, sort=[('created_on', DESCENDING)])
    fw_info = []
    for item in fws_shown:
        fw_info.append((item['fw_id'], item['name'], item['state']))

    # Current Database Status table data
    tot_fws   = lp.get_fw_ids(count_only=True)
    tot_wfs   = lp.get_wf_ids(count_only=True)
    fw_nums = []
    wf_nums = []
    for state in STATES:
        fw_nums.append(lp.get_fw_ids(query={'state': state}, count_only=True))
        if state == 'WAITING' or state == 'RESERVED':
            wf_nums.append('')
        else:
            wf_nums.append(lp.get_wf_ids(query={'state': state}, count_only=True))
    info = zip(STATES, fw_nums, wf_nums)
    # Newest Workflows table data
    wfs_shown = lp.workflows.find({}, limit=PER_PAGE, sort=[('updated_on', DESCENDING)])
    wf_info = []
    for item in wfs_shown:
        wf_info.append( {
            "id": item['nodes'][0], 
            "name": item['name'],
            "state": item['state'],
            "fireworks": list(lp.fireworks.find({"fw_id": { "$in": item["nodes"]} }, 
                limit=PER_PAGE, sort=[('created_on', DESCENDING)], 
                fields=["state", "name", "fw_id"] ))
        })
    return render_template('home.html', **locals())


@app.route('/fw/<int:fw_id>')
def show_fw(fw_id):
    try:
        int(fw_id)
    except:
        raise ValueError("Invalid fw_id: {}".format(fw_id))
    fw = lp.get_fw_by_id(fw_id)
    fw = fw.to_dict()
    if 'archived_launches' in fw:
        del fw['archived_launches']
    del fw['spec']
    fw_data = json.dumps(fw, default=DATETIME_HANDLER, indent=4)
    return render_template('fw_details.html', **locals())

@app.route('/wf/<int:wf_id>')
def show_workflow(wf_id):
    try:
        int(wf_id)
    except ValueError:
        raise ValueError("Invalid fw_id: {}".format(wf_id))
    wf = lp.get_wf_by_fw_id(wf_id)
    wf_dict = wf.to_display_dict()
    del wf_dict['name']
    del wf_dict['parent_links']
    del wf_dict['nodes']
    del wf_dict['links']
    del wf_dict['metadata']
    del wf_dict['states_list']
    wf_data = json.dumps(wf_dict, default=DATETIME_HANDLER, indent=4)
    return render_template('wf_details.html', **locals())

@app.route('/fw/', defaults={"state": "total"})
@app.route("/fw/<state>/")
def fw_states(state):
  db = lp.fireworks
  if state is "total":
    query = {}    
  else: 
    query = {'state': state.upper()}
  fw_count = lp.get_fw_ids(query=query, count_only=True)
  fw_stats = get_totals(STATES, lp)["fw_stats"]
  all_states = map(lambda s: s + ": " + str(fw_stats[s]), 
    STATES)
  all_states = zip(STATES, all_states)
  try:
      page = int(request.args.get('page', 1))
  except ValueError:
      page = 1  
  rows = list(db.find(query, fields=["fw_id", "name", "created_on"])
    .skip(page-1).sort([("created_on", DESCENDING)]).limit(PER_PAGE))
  pagination = Pagination(page=page, total=fw_count,  
    record_name='fireworks', per_page=PER_PAGE)
  return render_template('fw_state.html', **locals())

@app.route('/wf/', defaults={"state": "total"})
@app.route("/wf/<state>/")
def wf_states(state):
  db = lp.workflows
  if state is "total":
    query = {}    
  else: 
    query = {'state': state.upper()}
  wf_count = lp.get_fw_ids(query=query, count_only=True)
  wf_stats = get_totals(STATES, lp)["wf_stats"]
  all_states = map(lambda s: s + ": " + str(wf_stats[s]), 
    STATES)
  all_states = zip(STATES, all_states)
  try:
      page = int(request.args.get('page', 1))
  except ValueError:
      page = 1  
  rows = list(db.find(query).skip(page-1)
    .sort([('created_on', DESCENDING)])
    .limit(PER_PAGE))
  for r in rows:
    r["fw_id"] = r["nodes"][0]
  pagination = Pagination(page=page, total=wf_count,  
    record_name='workflows', per_page=PER_PAGE)
  return render_template('wf_state.html', **locals())

     
if __name__ == "__main__":
    app.run()

