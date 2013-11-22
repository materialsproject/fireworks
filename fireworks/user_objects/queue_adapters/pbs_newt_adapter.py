import os
from requests import Session
from fireworks.queue.queue_adapter import QueueAdapterBase
import getpass

__author__ = 'Shreyas Cholia, Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Nov 21, 2013'


class PBSAdapterNEWT(QueueAdapterBase):
    """
    A PBS adapter that works via the NEWT interface (https://newt.nersc.gov)
    """
    _fw_name = 'PBSAdapter (NEWT)'
    template_file = os.path.join(os.path.dirname(__file__), 'PBS_template.txt')
    submit_cmd = ''
    q_name = 'pbs_newt'
    defaults = {}

    def submit_to_queue(self, script_file):
        s = Session()
        r = s.get("https://newt.nersc.gov/newt")
        print r.content
        r = s.get("https://newt.nersc.gov/newt/auth")
        print r.content
        username = getpass.getuser()
        password = getpass.getpass()
        r = s.post("https://newt.nersc.gov/newt/auth", {"username": username, "password": password})
        print r.status_code
        print r.content
        jobfile = os.path.join(os.getcwd(), script_file)
        r = s.post("https://newt.nersc.gov/newt/queue/carver/", {"jobfile": jobfile})
        return int(r.json()['jobid'].split('.')[0])


    def get_njobs_in_queue(self, username=None):
        if username is None:
            username = getpass.getuser()
        s = Session()
        r = s.get("https://newt.nersc.gov/newt/queue/carver/?user={}".format(username))
        j = r.json()
        print len(j)
        return len(j)