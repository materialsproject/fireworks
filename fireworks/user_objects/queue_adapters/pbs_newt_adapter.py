import os
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
    _auth_session = None

    def submit_to_queue(self, script_file):
        self._init_auth_session()
        jobfile = os.path.join(os.getcwd(), script_file)
        r = self._auth_session.post("https://newt.nersc.gov/newt/queue/carver/", {"jobfile": jobfile})
        return int(r.json()['jobid'].split('.')[0])


    def get_njobs_in_queue(self, username=None):
        if username is None:
            username = getpass.getuser()
        from requests import Session  # hide import in case requests library not installed
        s = Session()
        r = s.get("https://newt.nersc.gov/newt/queue/carver/?user={}".format(username))
        return len(r.json())

    def _init_auth_session(self):
        from requests import Session  # hide import in case requests library not installed
        max_iterations = 3
        username = getpass.getuser()
        if not self._auth_session:
            self._auth_session = Session()  # create new session
        else:
            # check if we are already authenticated
            r = self._auth_session.get("https://newt.nersc.gov/newt/auth")
            if r.json()['auth'] and r.json()['username'] == username:
                return
        pw_iterations = 0
        while pw_iterations < max_iterations:
            password = getpass.getpass()
            r = self._auth_session.post("https://newt.nersc.gov/newt/auth", {"username": username, "password": password})
            pw_iterations+=1
            if r.json()['auth'] and r.json()['username'] == username:
                return
        raise ValueError('Could not get authorized connection to NEWT!')