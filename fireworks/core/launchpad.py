#!/usr/bin/env python

"""
The LaunchPad manages the FireWorks database.
"""
import datetime
from core.firework import WFConnections
from fireworks.core.fw_constants import LAUNCH_RANKS
from fireworks.core.fworker import FWorker
from fireworks.core.rocket import Rocket
from fireworks.utilities.fw_serializers import FWSerializable
from pymongo.mongo_client import MongoClient
from fireworks.core.firework import FireWork, Launch, FWorkflow
from pymongo import DESCENDING

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'

# TODO: add logging throughout
# TODO: probably lots of cleanup is possible
# TODO: be able to "freeze" and "thaw" a FireWork

class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """

    def __init__(self, host='localhost', port=27017, name='fireworks', id_prefix=None, username=None, password=None):
        """
        
        :param host:
        :param port:
        :param name:
        :param id_prefix:
        :param username:
        :param password:
        """
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password

        connection = MongoClient(host, port)
        self.database = connection[name]
        if username:
            self.database.authenticate(username, password)

        self.fireworks = self.database.fireworks
        self.fw_id_assigner = self.database.fw_id_assigner
        self.wfconnections = self.database.wfconnections

    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        d = {}
        d['host'] = self.host
        d['port'] = self.port
        d['name'] = self.name
        d['username'] = self.username
        d['password'] = self.password
        return d

    @classmethod
    def from_dict(cls, d):
        return LaunchPad(d['host'], d['port'], d['name'], d['username'], d['password'])

    def initialize(self, password, require_password=True):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! \
        To safeguard against accidentally erasing an existing database, a password must \
        be entered.
        :param password: A String representing today's date, e.g. '2012-12-31'
        :param require_password: Whether a password is required to initialize the DB. Highly \
        recommended to leave this set to True, otherwise you are inviting dangerous behavior!
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')

        if password == m_password or not require_password:
            self.fireworks.remove()
            self.wfconnections.remove()
            self._restart_ids(1, 1)
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))

    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        (internal method) Used to reset id counters
        :param next_fw_id: id to give next FireWork (int)
        :param next_launch_id: id to give next Launch (int)
        """

        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id, "next_launch_id": next_launch_id})

    def _checkout_fw(self, fworker, host, ip, launch_dir):
        """
        (internal method) Finds a FireWork that's ready to be run, marks it as running, and returns it to the caller. \
        The caller should run this FireWork.
        
        :param fworker: A FWorker instance
        """
        m_query = dict(fworker.query)  # make a copy of the query
        m_query['state'] = {'$in': ['READY', 'FIZZLED']}

        # check out the matching firework, depending on the query set by the FWorker
        m_fw = self.fireworks.find_and_modify(query=m_query, fields={"fw_id": 1}, update={'$set': {'state': 'RUNNING'}},
                                              sort=[("spec._priority", DESCENDING)])

        if not m_fw:
            return (None, None)

        # create a launch
        launch_id = self.get_new_launch_id()
        m_launch = Launch(fworker, host, ip, launch_dir, state='RUNNING', launch_id=launch_id)

        # add launch to FW
        m_fw_dict = self.fireworks.find_and_modify(query={'fw_id': m_fw['fw_id']},
                                                   update={'$push': {'launch_data': m_launch.to_db_dict()}}, new=True)

        # return FW
        return (FireWork.from_dict(m_fw_dict), launch_id)

    def _complete_launch(self, m_fw, launch_id, fw_decision=None):
        """
        (internal method) used to mark a FireWork's Launch as completed.
        :param m_fw:
        :param launch_id:
        :param fw_decision: the decision of what to do next
        """
        # TODO: what happens when multiple FireWorks share the same launch? Technically _complete_launch should only
        # depend on the launch_id.
        # You could implement this using a "launches_to_watch" key in FireWorks, and updating all FireWorks where the
        #  launch_id matches.

        for launch in m_fw.launch_data:
            if launch.launch_id == launch_id:
                launch.state = "COMPLETED"
                launch.end = datetime.datetime.utcnow()
                launch.stored_data = fw_decision.stored_data
                break

        # get the wf_dict
        wfc = WFConnections.from_dict(self.wfconnections.find_one({'nodes': m_fw.fw_id}))
        # get all the children
        child_fw_ids = wfc.children_links[m_fw.fw_id]

        # depending on the decision, you might have to do additional actions
        if fw_decision.action == 'CONTINUE':
            pass
        elif fw_decision.action == 'TERMINATE':
            # mark all children as terminated
            for cfid in child_fw_ids:
                self. _update_fw_state(self, cfid, 'TERMINATED')

        elif fw_decision.action == 'MODIFY':
            for cfid in child_fw_ids:
                self. _update_fw_spec(self, cfid, fw_decision.mod_spec['modifications'])

        elif fw_decision.action == 'DETOUR':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'ADD':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'ADDIFY':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'PHOENIX':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))

        self.fireworks.update({"fw_id": m_fw.fw_id}, m_fw.to_db_dict())
        self._refresh_wf(m_fw.fw_id)

    def get_new_fw_id(self):
        """
        Checkout the next FireWork id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_fw_id': 1}})['next_fw_id']

    def get_new_launch_id(self):
        """
        Checkout the next Launch id
        """
        return self.fw_id_assigner.find_and_modify(query={}, update={'$inc': {'next_launch_id': 1}})['next_launch_id']

    '''
    def upsert_fw(self, fw):
        """
        Given a FireWork, either insert it into the database or update the FireWork with the same id.
        
        :param fw: A FireWork instance
        """
        # TODO: make sure no child fws
        # TODO: make this also apply to sub-fireworks
        # TODO: make this to be INsert FW, not UPsert. Much safer that way unless you really need upsert.
        # TODO: add logging
        if not fw.fw_id or fw.fw_id < 0:
            fw.fw_id = self.get_new_fw_id()
        
        # TODO: make this also apply to sub-fireworks, add children and parent keys
        self.fireworks.update({"fw_id": fw.fw_id}, fw.to_db_dict(), upsert=True)
    '''

    def insert_wf(self, fwf):
        """

        :param fwf: an FWorkflow object.
        """

        if isinstance(fwf, FireWork):
            fwf = FWorkflow.from_FireWork(fwf)

        # mapping between old and new FireWork ids
        old_new = {}

        # insert the FireWorks
        for fw in fwf.id_fw.itervalues():
            if not fw.fw_id or fw.fw_id < 0:
                new_id = self.get_new_fw_id()
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id

            self.fireworks.insert(fw.to_db_dict())

        # redo the FWorkflow based on new mappings
        fwf._reassign_ids(old_new)
        self.wfconnections.insert(fwf.to_db_dict())
        self._refresh_wf(fwf.nodes[0])  # fwf.nodes[0] is any fw_id in this workflow

    def _refresh_wf(self, fw_id):

        """
        Update the FW state of all affected FWs
        :param fw_id:
        """

        # get the workflow containing this fw_id
        wf_dict = self.wfconnections.find_one({'nodes': fw_id})

        updated_nodes = set()

        while len(updated_nodes) != len(wf_dict['nodes']):
            for fw_id in wf_dict['nodes']:
                if str(fw_id) not in wf_dict['parent_links']:
                    self._refresh_fw(fw_id, [])
                    updated_nodes.add(fw_id)
                else:
                    # if all parents are updated, update it
                    if all(parent in updated_nodes for parent in wf_dict['parent_links'][str(fw_id)]):
                        self._refresh_fw(fw_id, wf_dict['parent_links'][str(fw_id)])
                        updated_nodes.add(fw_id)


    def _get_fw_state(self, fw_id):
        return self.fireworks.find_one({"fw_id": fw_id}, {"state": True})['state']

    def _update_fw_state(self, fw_id, m_state):
        return self.fireworks.update({"fw_id": fw_id}, {"$set": {"state": m_state}})

    def _update_fw_spec(self, fw_id, modder_dict):

        raise NotImplementedError('')
        #return self.fireworks.update({"fw_id": fw_id}, {"$set": {"state": m_state}})

    def _refresh_fw(self, fw_id, parent_ids):
        # if we are terminated, just skip this whole thing
        if self._get_fw_state(fw_id) == 'TERMINATED':
            return

        m_state = None

        # what are the parent states?
        parent_states = [self._get_fw_state(p) for p in parent_ids]

        if len(parent_ids) != 0 and not all([s == 'COMPLETED' for s in parent_states]):
            m_state = 'WAITING'

        elif any([s == 'CANCELED' for s in parent_states]):
            m_state = 'CANCELED'

        else:
            # my state depends on launch
            launch_data = self.get_launches(fw_id)
            max_score = 0
            m_state = 'READY'

            for l in launch_data:
                if LAUNCH_RANKS[l.state] > max_score:
                    max_score = LAUNCH_RANKS[l.state]
                    m_state = l.state

        self._update_fw_state(fw_id, m_state)

    def get_fw_by_id(self, fw_id):
        """
        Given a FireWork id, give back a FireWork object
        :param fw_id: FireWork id (int)
        """
        fw_dict = self.fireworks.find_one({'fw_id': fw_id})
        return FireWork.from_dict(fw_dict)

    def get_launches(self, fw_id):
        """
        Given a FireWork id, give back a FireWork object
        :param fw_id: FireWork id (int)
        """
        launch_data = self.fireworks.find_one({'fw_id': fw_id}, {'launch_data': 1})['launch_data']
        return [Launch.from_dict(l) for l in launch_data]

    def get_fw_ids(self, query=None):
        """
        Return all the fw ids that match a query
        :param query: a dict representing a Mongo query
        """
        fw_ids = []
        criteria = query if query else {}

        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=[("spec._priority", DESCENDING)]):
            fw_ids.append(fw["fw_id"])

        return fw_ids


if __name__ == "__main__":
    lp = LaunchPad()
    lp.initialize('2013-02-19')
    fwf = FWorkflow.from_tarfile('../../fw_tutorials/workflow/hello.tar')
    lp.insert_wf(fwf)
    fworker = FWorker()
    rocket = Rocket(lp, fworker)
    rocket.run()
