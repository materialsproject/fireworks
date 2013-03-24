#!/usr/bin/env python

"""
The LaunchPad manages the FireWorks database.
"""
import datetime
from fireworks.core.fw_config import FWConfig
from fireworks.core.workflow import Workflow
from fireworks.utilities.fw_serializers import FWSerializable, load_object
from pymongo.mongo_client import MongoClient
from fireworks.core.firework import FireWork, Launch
from pymongo import DESCENDING
from fireworks.utilities.fw_utilities import get_fw_logger

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Jan 30, 2013'


# TODO: be able to terminate / un-terminate a FW
# TODO: can actions like complete_launch() be done as a transaction? e.g. refresh_wf() might have error...I guess at
# least set the state to FIZZLED or ERROR and add traceback...

class LaunchPad(FWSerializable):
    """
    The LaunchPad manages the FireWorks database.
    """

    def __init__(self, host='localhost', port=27017, name='fireworks', username=None, password=None,
                 logdir=None, strm_lvl=None):
        """
        
        :param host:
        :param port:
        :param name:
        :param username:
        :param password:
        :param logdir:
        :param strm_lvl:
        """
        self.host = host
        self.port = port
        self.name = name
        self.username = username
        self.password = password

        # set up logger
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.m_logger = get_fw_logger('launchpad', l_dir=self.logdir, stream_level=self.strm_lvl)

        self.connection = MongoClient(host, port, j=False)
        self.database = self.connection[name]
        if username:
            self.database.authenticate(username, password)

        self.fireworks = self.database.fireworks
        self.launches = self.database.launches
        self.fw_id_assigner = self.database.fw_id_assigner
        self.workflows = self.database.workflows

    def to_dict(self):
        """
        Note: usernames/passwords are exported as unencrypted Strings!
        """
        d = {'host': self.host, 'port': self.port, 'name': self.name, 'username': self.username,
             'password': self.password, 'logdir': self.logdir, 'strm_lvl': self.strm_lvl}
        return d

    @classmethod
    def from_dict(cls, d):
        logdir = d.get('logdir', None)
        strm_lvl = d.get('strm_lvl', None)
        return LaunchPad(d['host'], d['port'], d['name'], d['username'], d['password'], logdir, strm_lvl)

    def reset(self, password, require_password=True):
        """
        Create a new FireWorks database. This will overwrite the existing FireWorks database! \
        To safeguard against accidentally erasing an existing database, a password must \
        be entered.

        :param password: A String representing today's date, e.g. '2012-12-31'
        :param require_password: Whether a password is required to reset the DB. Highly \
        recommended to leave this set to True, otherwise you are inviting disaster!
        """
        m_password = datetime.datetime.now().strftime('%Y-%m-%d')

        if password == m_password or not require_password:
            self.fireworks.remove()
            self.launches.remove()
            self.workflows.remove()
            self._restart_ids(1, 1)
            self._update_indices()
            self.m_logger.info('LaunchPad was RESET.')
        else:
            raise ValueError("Invalid password! Password is today's date: {}".format(m_password))

    def maintain(self):
        # TODO: compact the database / collections
        # TODO: track down launches that have not pinged the server in awhile...
        # TODO: update FIZZLED and long RESERVED states...

        self.m_logger.info('Performing maintenance on Launchpad, please wait....')
        self._update_indices()
        self.m_logger.info('LaunchPad was MAINTAINED.')

    def add_wf(self, wf):
        """

        :param wf: a Workflow object.
        """

        if isinstance(wf, FireWork):
            wf = Workflow.from_FireWork(wf)

        # insert the FireWorks and get back mapping of old to new ids
        old_new = self._upsert_fws(wf.id_fw.values())

        # TODO: refresh_workflow probably takes care of this now
        # redo the Workflow based on new mappings
        wf._reassign_ids(old_new)

        # insert the WFLinks
        self.workflows.insert(wf.to_db_dict())

        # refresh WF states, starting from all roots
        for fw_id in wf.root_fw_ids:
            self._refresh_wf(wf, fw_id)

        self.m_logger.info('Added a workflow. id_map: {}'.format(old_new))
        return old_new

    def get_launch_by_id(self, launch_id):
        """
        Given a Launch id, return details of the Launch

        :param launch_id: launch id
        :return: Launch object
        """
        m_launch = self.launches.find_one({'launch_id': launch_id})
        if m_launch:
            return Launch.from_dict(m_launch)
        raise ValueError('No Launch exists with launch_id: {}'.format(launch_id))

    def get_fw_by_id(self, fw_id):
        """
        Given a FireWork id, give back a FireWork object

        :param fw_id: FireWork id (int)
        :return: FireWork object
        """
        fw_dict = self.fireworks.find_one({'fw_id': fw_id})

        if not fw_dict:
            raise ValueError('No FireWork exists with id: {}'.format(fw_id))
            # recreate launches from the launch collection
        launches = []
        for launch_id in fw_dict['launches']:
            launches.append(self.get_launch_by_id(launch_id).to_dict())
        fw_dict['launches'] = launches

        return FireWork.from_dict(fw_dict)

    def get_wf_by_fw_id(self, fw_id):

        """
        Given a FireWork id, give back the Workflow containing that FireWork
        :param fw_id:
        :return: A Workflow object
        """

        links_dict = self.workflows.find_one({'nodes': fw_id})
        fws = []
        for fw_id in links_dict['nodes']:
            fws.append(self.get_fw_by_id(fw_id))
        links = Workflow.Links.from_dict(links_dict['links']).to_dict()  # necessary because Mongo no like int keys

        return Workflow(fws, links, links_dict['metadata'])

    def get_fw_ids(self, query=None, sort=False):
        """
        Return all the fw ids that match a query,
        :param query: a dict representing a Mongo query
        """
        fw_ids = []
        criteria = query if query else {}
        sort = [("spec._priority", DESCENDING)] if sort else None
        for fw in self.fireworks.find(criteria, {"fw_id": True}, sort=sort):
            fw_ids.append(fw["fw_id"])

        return fw_ids

    def run_exists(self):
        """
        Checks to see if the database contains any FireWorks that are ready to run
        :return: (T/F)
        """
        return bool(self._get_a_fw_to_run(checkout=False))

    def _update_indices(self):
        self.fireworks.ensure_index('fw_id', unique=True)
        self.fireworks.ensure_index('state')

        self.launches.ensure_index('launch_id', unique=True)
        self.launches.ensure_index('state')
        self.launches.ensure_index('start')
        self.launches.ensure_index('end')
        self.launches.ensure_index('host')
        self.launches.ensure_index('ip')

    def _restart_ids(self, next_fw_id, next_launch_id):
        """
        (internal method) Used to reset id counters

        :param next_fw_id: id to give next FireWork (int)
        :param next_launch_id: id to give next Launch (int)
        """
        self.fw_id_assigner.remove()
        self.fw_id_assigner.insert({"next_fw_id": next_fw_id, "next_launch_id": next_launch_id})
        self.m_logger.debug('RESTARTED fw_id, launch_id to ({}, {})'.format(next_fw_id, next_launch_id))

    def _check_fw_for_uniqueness(self, m_fw):
        # check if there are duplicates
        if not self._steal_launches(m_fw):
            self.m_logger.debug('FW with id: {} is unique!'.format(m_fw.fw_id))
            return True

        self._upsert_fws([m_fw])  # update the DB with the new launches
        self._refresh_wf(self.get_wf_by_fw_id(m_fw.fw_id),
                         m_fw.fw_id)  # since we updated a state, we need to refresh the WF again

        return False

    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        m_query = dict(query) if query else {}  # make a defensive copy
        m_query['state'] = 'READY'

        # Override query if fw_id defined
        # Note for the fw_id option: We want to return None if this specific FW doesn't exist anymore
        # This is because our queue params might have been tailored to this FW
        if fw_id:
            m_query = {"fw_id": fw_id, "state": {'$in': ['READY', 'RESERVED']}}

        while True:
            # check out the matching firework, depending on the query set by the FWorker
            if checkout:
                m_fw = self.fireworks.find_and_modify(query=m_query, update={'$set': {'state': 'RESERVED'}},
                                                  sort=[("spec._priority", DESCENDING)])
            else:
                m_fw = self.fireworks.find_one(m_query, {'fw_id': 1}, sort=[("spec._priority", DESCENDING)])

            if not m_fw:
                return None
            m_fw = self.get_fw_by_id(m_fw['fw_id'])

            if self._check_fw_for_uniqueness(m_fw):
                return m_fw

    def _reserve_fw(self, fworker, launch_dir, host=None, ip=None):
        m_fw = self._get_a_fw_to_run(fworker.query)
        if not m_fw:
            return None, None
        # create a launch
        # TODO: this code is duplicated with checkout_fw with minimal mods, should refactor this!!
        launch_id = self.get_new_launch_id()
        m_launch = Launch('RESERVED', launch_dir, fworker, host, ip, launch_id=launch_id, fw_id=m_fw.fw_id)
        self.launches.insert(m_launch.to_db_dict())

        # add launch to FW
        m_fw.launches.append(m_launch)
        m_fw.state = 'RESERVED'
        self._upsert_fws([m_fw])
        self.m_logger.debug('Reserved FW with id: {}'.format(m_fw.fw_id))

        return m_fw, launch_id

    def unreserve(self, launch_id):
        self.launches.update({'launch_id': launch_id}, {'$set': {'state': 'READY'}})
        self.fireworks.update({'launches': launch_id, 'state': 'RESERVED'}, {'$set': {'state': 'READY'}}, multi=True)
        # self.connection.fsync()

    def detect_unreserved(self, expiration_secs=FWConfig().RESERVATION_EXPIRATION_SECS, fix=False):
        bad_launch_ids = []
        now_time = datetime.datetime.utcnow()
        cutoff_timestr = (now_time - datetime.timedelta(seconds=expiration_secs)).isoformat()
        bad_launch_data = self.launches.find({'state': 'RESERVED', 'state_history': {
        '$elemMatch': {'state': 'RESERVED', 'updated_on': {'$lte': cutoff_timestr}}}}, {'launch_id': 1})
        for ld in bad_launch_data:
            bad_launch_ids.append(ld['launch_id'])
        if fix:
            for lid in bad_launch_ids:
                self.unreserve(lid)
        return bad_launch_ids

    def mark_fizzled(self, launch_id):
        self.launches.update({'launch_id': launch_id}, {'$set': {'state': 'FIZZLED'}})
        for fw_data in self.fireworks.find({'launches': launch_id}, {'fw_id': 1}):
            fw_id = fw_data['fw_id']
            wf = self.get_wf_by_fw_id(fw_id)
            self._refresh_wf(wf, fw_id)

    def detect_fizzled(self, expiration_secs=FWConfig().RUN_EXPIRATION_SECS, fix=False):
        bad_launch_ids = []
        now_time = datetime.datetime.utcnow()
        cutoff_timestr = (now_time - datetime.timedelta(seconds=expiration_secs)).isoformat()
        bad_launch_data = self.launches.find({'state': 'RUNNING', 'state_history': {
        '$elemMatch': {'state': 'RUNNING', 'updated_on': {'$lte': cutoff_timestr}}}}, {'launch_id': 1})
        for ld in bad_launch_data:
            bad_launch_ids.append(ld['launch_id'])
        if fix:
            for lid in bad_launch_ids:
                self.mark_fizzled(lid)
        return bad_launch_ids

    def _set_reservation_id(self, launch_id, reservation_id):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.set_reservation_id(reservation_id)
        self.launches.update({'launch_id': launch_id}, m_launch.to_db_dict())
        # self.connection.fsync()

    def _checkout_fw(self, fworker, launch_dir, fw_id=None, host=None, ip=None):
        """
        (internal method) Finds a FireWork that's ready to be run, marks it as running,
        and returns it to the caller. The caller is responsible for running the FireWork.
        
        :param fworker: A FWorker instance
        :param host: the host making the request (for creating a Launch object)
        :param ip: the ip making the request (for creating a Launch object)
        :param launch_dir: the dir the FW will be run in (for creating a Launch object)
        :return: a FireWork, launch_id tuple
        """

        # TODO: this method is confusing, says AJ of Xmas past

        # TODO: state history is not preserved when going from RESERVED --> RUNNING! The RUNNING launch just
        # overwrites the RESERVED launch completely!!

        # TODO: Duplicate FWS are not updated when going from RESERVED --> RUNNING!

        m_fw = self._get_a_fw_to_run(fworker.query, fw_id)
        if not m_fw:
            return None, None

        # create or update a launch
        # Was this FireWork previously reserved? If so, update that launch instead of creating a new one
        prev_reservations = [l for l in m_fw.launches if l.state == 'RESERVED']
        prev_launch_id = None if len(prev_reservations) == 0 else prev_reservations[0].launch_id

        l_id = prev_launch_id if prev_launch_id else self.get_new_launch_id()
        m_launch = Launch('RUNNING', launch_dir, fworker, host, ip, launch_id=l_id, fw_id=m_fw.fw_id)
        self.launches.update({'launch_id': l_id}, m_launch.to_db_dict(), upsert=True)
        self.m_logger.debug('Created/updated Launch with launch_id: {}'.format(l_id))

        if not prev_launch_id:
            # we're appending a new FireWork
            m_fw.launches.append(m_launch)
        else:
            # we're updating an existing launch
            m_fw.launches = [m_launch if l.launch_id == m_launch.launch_id else l for l in m_fw.launches]

        m_fw.state = 'RUNNING'
        self._upsert_fws([m_fw])
        self.m_logger.debug('Checked out FW with id: {}'.format(m_fw.fw_id))
        # self.connection.fsync()

        return m_fw, l_id

    def _complete_launch(self, launch_id, action, state='COMPLETED'):
        """
        (internal method) used to mark a FireWork's Launch as completed.
        :param launch_id:
        :param action: the FWAction of what to do next
        """
        # update the launch data to COMPLETED, set end time, etc
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.state = state
        m_launch.action = action
        self.launches.update({'launch_id': launch_id}, m_launch.to_db_dict())

        # find all the fws that have this launch
        for fw in self.fireworks.find({'launches': launch_id}, {'fw_id': 1}):
            fw_id = fw['fw_id']
            self._refresh_wf(self.get_wf_by_fw_id(fw_id), fw_id)

    def _ping_launch(self, launch_id):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.touch_history()
        self.launches.update({'launch_id': launch_id}, m_launch.to_db_dict())

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

    def _upsert_fws(self, fws):
        old_new = {} # mapping between old and new FireWork ids
        for fw in fws:
            if fw.fw_id < 0:
                new_id = self.get_new_fw_id()
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id
            self.fireworks.update({'fw_id': fw.fw_id}, fw.to_db_dict(), upsert=True)

        return old_new

    def _refresh_wf(self, wf, fw_id):

        """
        Update the FW state of all jobs in workflow
        :param wf: a Workflow object
        :param fw_id: the parent fw_id - children will be refreshed
        """
        # TODO: time how long it took to refresh the WF!
        # TODO: need a try-except here, high probability of failure if incorrect action supplied

        updated_ids = wf.refresh(fw_id)
        updated_fws = [wf.id_fw[fid] for fid in updated_ids]
        old_new = self._upsert_fws(updated_fws)
        wf._reassign_ids(old_new)
        # redo the links
        self.workflows.update({'nodes': fw_id}, wf.to_db_dict())
        # self.connection.fsync()  # fsync the changes

    def _steal_launches(self, thief_fw):
        stolen = False
        if thief_fw.state in ['READY', 'RESERVED'] and '_dupefinder' in thief_fw.spec:
            m_dupefinder = thief_fw.spec['_dupefinder']
            # get the query that will limit the number of results to check as duplicates
            m_query = m_dupefinder.query(thief_fw.spec)
            m_query['launches'] = {'$ne': []}
            # iterate through all potential duplicates in the DB
            self.m_logger.debug('Querying for duplicates, fw_id: {}'.format(thief_fw.fw_id))
            for potential_match in self.fireworks.find(m_query):
                self.m_logger.debug('Verifying for duplicates, fw_ids: {}, {}'.format(thief_fw.fw_id, potential_match['fw_id']))
                spec1 = dict(thief_fw.to_dict()['spec'])  # defensive copy
                spec2 = dict(potential_match['spec'])  # defensive copy
                if m_dupefinder.verify(spec1, spec2):  # verify the match
                    # steal the launches
                    victim_fw = self.get_fw_by_id(potential_match['fw_id'])
                    thief_launches = [l.launch_id for l in thief_fw.launches]
                    valuable_launches = [l for l in victim_fw.launches if l.launch_id not in thief_launches]
                    for launch in valuable_launches:
                        thief_fw.launches.append(launch)
                        stolen = True
                        self.m_logger.info('Duplicate found! fwids {} and {}'.format(thief_fw.fw_id, potential_match['fw_id']))

        return stolen
