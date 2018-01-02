# coding: utf-8

from __future__ import unicode_literals

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
    A special PBS adapter that works via the NEWT interface (https://newt.nersc.gov)
    Only intended for job submission via the RESTful NEWT web interface.
    """
    _fw_name = 'PBSAdapter (NEWT)'
    template_file = os.path.join(os.path.dirname(__file__), 'PBS_template.txt')
    submit_cmd = ''
    q_name = 'pbs_newt'
    defaults = {}
    resource = 'carver'  # 'carver' or 'hopper'
    _session = None

    def submit_to_queue(self, script_file):
        self._init_auth_session()
        jobfile = os.path.join(os.getcwd(), script_file)
        r = PBSAdapterNEWT._session.post("https://newt.nersc.gov/newt/queue/{}/".format(self.resource), {"jobfile": jobfile})
        return int(r.json()['jobid'].split('.')[0])

    def get_njobs_in_queue(self, username=None):
        if username is None:
            username = getpass.getuser()
        from requests import Session  # hide import in case optional library not installed
        r = Session().get("https://newt.nersc.gov/newt/queue/{}/?user={}".format(self.resource, username))
        return len(r.json())

    @staticmethod
    def _init_auth_session(max_pw_requests=3):
        """
        Initialize the _session class var with an authorized session. Asks for a /
        password in new sessions, skips PW check for previously authenticated sessions
        """
        from requests import Session  # hide import in case optional library not installed
        username = getpass.getuser()
        if not PBSAdapterNEWT._session:
            PBSAdapterNEWT._session = Session()  # create new session
        else:
            # are we already authenticated?
            r = PBSAdapterNEWT._session.get("https://newt.nersc.gov/newt/auth")
            if r.json()['auth'] and r.json()['username'] == username:
                return
        # assert: not already authenticated, ask for a PW and authenticate
        pw_iterations = 0
        while pw_iterations < max_pw_requests:
            password = getpass.getpass()
            r = PBSAdapterNEWT._session.post("https://newt.nersc.gov/newt/auth", {"username": username, "password": password})
            if r.json()['auth'] and r.json()['username'] == username:
                return
            pw_iterations += 1
        raise ValueError('Could not get authorized connection to NEWT!')
