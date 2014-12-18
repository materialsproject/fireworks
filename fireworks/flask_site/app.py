from flask import Flask, url_for, render_template
from fireworks.utilities.fw_serializers import DATETIME_HANDLER
from pymongo import DESCENDING
import os, json
from fireworks.core.launchpad import LaunchPad
DEFAULT_LPAD_YAML = "my_launchpad.yaml"
from helpers import get_lp

app = Flask(__name__)
app.debug = True
app.use_reloader=True

lp = LaunchPad.from_dict(get_lp())

@app.route("/")
def home():
    shown = 20
    comp_fws = lp.get_fw_ids(query={'state': 'COMPLETED'}, count_only=True)

    # Newest Fireworks table data
    fws_shown = lp.fireworks.find({}, limit=shown, sort=[('created_on', DESCENDING)])
    fw_info = []
    for item in fws_shown:
        fw_info.append((item['fw_id'], item['name'], item['state']))

    # Current Database Status table data
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

    # Newest Workflows table data
    wfs_shown = lp.workflows.find({}, limit=shown, sort=[('updated_on', DESCENDING)])
    wf_info = []
    for item in wfs_shown:
        wf_info.append( {
            "id": item['nodes'][0], 
            "name": item['name'],
            "state": item['state'],
            "fireworks": list(lp.fireworks.find({"fw_id": { "$in": item["nodes"]} }, 
                limit=shown, sort=[('created_on', DESCENDING)], 
                fields=["state", "name", "fw_id"] ))
        })
    return render_template('home.html', **locals())





if __name__ == "__main__":
    app.run()