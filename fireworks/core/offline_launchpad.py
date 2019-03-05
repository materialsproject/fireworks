"""Internet? Where we're going we don't need internet

Stores everything in a sqlite database (instead of MongoDB)

Implementation notes:

Each mdb collection is roughly translated into a separate table in the db

The 'meta' table keeps counts of ids as they're handed out.

Fireworks are stored a row each.  Only the important information (which is
later queried upon) is pulled out into columns, everything else is stuffed
as a json representation into 'data' which represents anything/everything.

Workflows follow a similar strategy.  In order to get a unique 'key' for
these, they follow a similar strategy to Fireworks in requesting a unique
id upon insertion.

There is a table of firework to workflow id 'mapping'.  This allows searching
for the parent workflow of a given Firework.  (ie replicate $in in SQL).
To remove this table we'd have to store Workflow ID alongside Fireworks
(not impossible tbh, Fireworks are only inserted in the context of a WF).


"""
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
from bson import json_util as json
import datetime
import sqlite3

from .firework import Firework, Workflow, Launch


def _nq(n):
    # for IN statements
    # generates a (?,...,?) block with *n* values
    return '(' + ','.join(['?'] * n) + ')'


def firework_to_sqlite(firework):
    d = firework.to_db_dict()
    fw_id = d.pop('fw_id')
    state = d.pop('state', None)
    d = json.dumps(d)

    return fw_id, state, d

def sqlite_to_firework(firework):
    fw_id, state, data = firework
    d = json.loads(data)

    d['fw_id'] = fw_id
    if not state is None:
        d['state'] = state

    return d

def workflow_to_sqlite(workflow):
    return json.dumps(workflow.to_db_dict())

def sqlite_to_workflow(workflow):
    return json.loads(workflow)


def launch_to_sqlite(launch):
    dlaunch = launch.to_db_dict()

    fw_id = dlaunch.pop('fw_id')
    launch_id = dlaunch.pop('launch_id')

    return json.dumps(dlaunch)

def sqlite_to_launch(launch):
    launch_id, fw_id, dlaunch = launch

    dlaunch = json.loads(dlaunch)
    dlaunch['fw_id'] = fw_id
    dlaunch['launch_id'] = launch_id

    return dlaunch


class OfflineLaunchPad(object):
    def __init__(self, address, *args, logdir=None, **kwargs):
        self._address = address  # store how we got here
        self._db = sqlite3.connect(address)
        with self._db as c:
            c.execute('PRAGMA foreign_keys = ON')
        self.logdir = logdir

    def copy(self):
        # can only use one connection per thread
        # so this method creates a new connection for threads
        return self.__class__(self._address)

    def to_dict(self):
        raise NotImplementedError

    def update_specs(self, fw_ids, spec_document, mongo=False):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d):
        raise NotImplementedError

    @classmethod
    def auto_loc(cls):
        raise NotImplementedError

    def reset(self, *args, **kwargs):
        with self._db as c:
            # TODO: Can squish these commands into single call?
            # reset count of ids
            c.execute('DROP TABLE IF EXISTS meta')
            c.execute('CREATE TABLE meta(name TEXT, value INTEGER)')
            c.executemany('INSERT INTO meta VALUES(?, 1)',
                          (('next_fw_id',),
                           ('next_launch_id',),
                           ('next_workflow_id',)))
            c.execute('DROP TABLE IF EXISTS fireworks')
            c.execute('''CREATE TABLE fireworks(fw_id INTEGER UNIQUE,
                                                state TEXT,
                                                data TEXT)''')
            c.execute('DROP TABLE IF EXISTS workflows')
            c.execute('''CREATE TABLE workflows(wf_id INTEGER UNIQUE,
                                                data TEXT)''')
            c.execute('DROP TABLE IF EXISTS mapping')
            # TODO: Maybe store this inside the fireworks collection?
            # ie add row of workflow_id values to fireworks schema
            c.execute('CREATE TABLE mapping(firework_id INTEGER UNIQUE, '
                      'workflow_id INTEGER, '
                      # all entries must match a fw_id in fireworks
                      'FOREIGN KEY (firework_id) REFERENCES fireworks(fw_id) '
                      # ie when these rows are modified,
                      # also update this table
                      #'ON UPDATE CASCADE ON DELETE CASCADE, '
                      'FOREIGN KEY (workflow_id) REFERENCES workflows(wf_id) '
                      #'ON UPDATE CASCADE ON DELETE CASCADE)'
                      ')')
            c.execute('DROP TABLE IF EXISTS launches')
            c.execute('CREATE TABLE launches(launch_id INTEGER UNIQUE, '
                      'fw_id INTEGER, '
                      'data TEXT, '
                      # launches know what firework they're for
                      'FOREIGN KEY(fw_id) REFERENCES fireworks(fw_id) '
                      ')')

    def maintain(self, **kwargs):
        raise NotImplementedError

    def add_wf(self, wf, reassign_all=True):
        """Add WF to LaunchPad"""
        if isinstance(wf, Firework):
            wf = Workflow.from_Firework(wf)

        for fw_id in wf.root_fw_ids:
            wf.id_fw[fw_id].state = 'READY'
            wf.fw_states[fw_id] = 'READY'

        # "insert" and get new mapping of ids
        old_new = self._upsert_fws(list(wf.id_fw.values()),
                                   reassign_all=reassign_all)
        wf._reassign_ids(old_new)

        workflow_id = self._get_new_workflow_id()
        with self._db as c:
            c.execute('INSERT INTO workflows VALUES(?, ?)',
                      (workflow_id, workflow_to_sqlite(wf)))
            c.executemany('INSERT INTO mapping VALUES(?, ?)', (
                (fw_id, workflow_id) for fw_id in wf.id_fw
            ))
        return old_new

    def bulk_add_wfs(self, wfs):
        for wf in wfs:
            self.add_wf(wf)

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=True):
        raise NotImplementedError

    def get_launch_by_id(self, launch_id):
        with self._db as c:
            cur = c.execute('SELECT * FROM launches '
                            'WHERE launch_id = ?', (launch_id,))
            payload = cur.fetchone()
        m_launch = sqlite_to_launch(payload)

        return Launch.from_dict(m_launch)

    def get_fw_dict_by_id(self, fw_id):
        # TODO: Storage of launches/fireworks
        with self._db as c:
            val = c.execute('SELECT * FROM fireworks WHERE fw_id = ?',
                            (fw_id,)).fetchone()
            launches = c.execute('SELECT * FROM launches '
                                 'WHERE fw_id = ?', (fw_id,))
            firework = sqlite_to_firework(val)
            # these are converted into Launch objects by Firework.from_dict
            launches = [(sqlite_to_launch(l)) for l in launches]
        # TODO: Differentiate between archived and not
        #       Maybe extra boolean column in launches schema?
        firework['launches'] = launches

        return firework

    def get_fw_by_id(self, fw_id):
        return Firework.from_dict(self.get_fw_dict_by_id(fw_id))

    def get_wf_by_fw_id(self, fw_id):
        # search through all Workflows, looking for correct fw_id?
        # or could have some index file, but this could get stale
        with self._db as c:
            # TODO: Maybe this can be some fancy INNER JOIN
            wf_id = c.execute('SELECT workflow_id FROM mapping WHERE firework_id = ?',
                              (fw_id,)).fetchone()[0]

            workflow = c.execute('SELECT data FROM workflows WHERE wf_id = ?',
                                 (wf_id,)).fetchone()[0]

        workflow = sqlite_to_workflow(workflow)

        fireworks = [self.get_fw_by_id(i) for i in workflow['nodes']]

        return Workflow(fireworks, workflow['links'], workflow['name'],
                        workflow['metadata'], workflow['created_on'],
                        workflow['updated_on'])

    def get_wf_by_fw_id_lzyfw(self, fw_id):
        with self._db as c:
            wf_id = c.execute('SELECT workflow_id FROM mapping WHERE firework_id = ?',
                              (fw_id,)).fetchone()[0]

            workflow = c.execute('SELECT data FROM workflows WHERE wf_id = ?',
                                 (wf_id,)).fetchone()[0]

        workflow = sqlite_to_workflow(workflow)

        fws = [LazyFirework(fw_id, self)
               for fw_id in workflow['nodes']]

        if 'fw_states' in workflow:
            fw_states = dict([(int(k), v)
                              for (k, v) in workflow['fw_states'].items()])
        else:
            fw_states = None

        return Workflow(fws, workflow['links'], workflow['name'],
                        workflow['metadata'], workflow['created_on'],
                        workflow['updated_on'], fw_states)

    def delete_wf(self, fw_id, delete_launch_dirs=False):
        raise NotImplementedError

    def get_wf_summary_dict(self, fw_id, mode='more'):
        raise NotImplementedError

    def get_fw_ids(self, **kwargs):
        raise NotImplementedError

    def get_wf_ids(self, **kwargs):
        raise NotImplementedError

    def run_exists(self, fworker=None):
        if not fworker is None:
            raise NotImplementedError
        return bool(self._get_a_fw_to_run(query=None,
                                          checkout=False))

    def future_run_exists(self, fworker=None):
        if self.run_exists(fworker):
            return True
        if not fworker is None:
            raise NotImplementedError
        with self._db as c:
            # iterate over 'active' fireworks checking for waiting children
            for (fw_id,) in c.execute('SELECT fw_id FROM fireworks '
                                      'WHERE state in ("RUNNING", "RESERVED")'):
                # TODO: Could optimise here by grouping into workflows
                #       & fetch each unique workflow only once...
                # TODO: Make lazy again
                children = self.get_wf_by_fw_id(fw_id).links[fw_id]
                # If any children are "WAITING" then we've got future work
                if c.execute('SELECT state FROM fireworks '
                             'WHERE fw_id IN ' + _nq(len(children)) + ' '
                             'AND state = "WAITING"',
                             children):
                    return True
            else:
                # At end of loop, no future work remains
                return False

    def tuneup(self, bkground=True):
        # TODO: Just do sqlite VACUUM ?
        raise NotImplementedError

    def pause_fw(self, fw_id):
        raise NotImplementedError

    def defuse_fw(self, fw_id, rerun_duplicates=True):
        raise NotImplementedError

    def reignite_fw(self, fw_id):
        raise NotImplementedError

    def resume_fw(self, fw_id):
        raise NotImplementedError

    def defuse_wf(self, fw_id, defuse_all_states=True):
        raise NotImplementedError

    def pause_wf(self, fw_id):
        raise NotImplementedError

    def reignite_wf(self, fw_id):
        raise NotImplementedError

    def archive_wf(self, fw_id):
        raise NotImplementedError

    def _restart_ids(self, next_fw_id, next_launch_id):
        raise NotImplementedError

    def _check_fw_for_uniqueness(self, m_fw):
        raise NotImplementedError

    def _get_a_fw_to_run(self, query=None, fw_id=None, checkout=True):
        # TODO: FWorker query isn't implemented at all
        #       At minimum need category functionality
        #if query:
        #    # let's smoke out where/if this is ever used
        #    raise NotImplementedError

        with self._db as c:
            if fw_id:
                firework = c.execute('SELECT * FROM fireworks '
                                     'WHERE fw_id = ? AND '
                                     'state IN ("READY", "RESERVED")',
                                     (fw_id,)).fetchone()
            else:
                # TODO: Ordering expected here
                firework = c.execute('SELECT * FROM fireworks '
                                     'WHERE state = "READY"').fetchone()
            if not firework is None:
                firework = Firework.from_dict(sqlite_to_firework(firework))
                if checkout:
                    # TODO: Updated on field in fireworks schema
                    c.execute('UPDATE fireworks SET state = "RESERVED" '
                              'WHERE fw_id = ?',
                              (firework.fw_id,))

        # TODO: Check for uniqueness

        return firework

    def _get_active_launch_ids(self):
        raise NotImplementedError

    def reserve_fws(slef, *args, **kwargs):
        raise NotImplementedError

    def get_fw_ids_from_reservation_id(self, reservation_id):
        raise NotImplementedError

    def cancel_reservation_by_reservation_id(self, reservation_id):
        raise NotImplementedError

    def get_reservation_id_from_fw_id(self, fw_id):
        raise NotImplementedError

    def cancel_reservation(self, launch_id):
        raise NotImplementedError

    def detect_unreserved(self, **kwargs):
        raise NotImplementedError

    def mark_fizzled(self, launch_id):
        raise NotImplementedError

    def detect_lostruns(self, **kwargs):
        raise NotImplementedError

    def set_reservation_id(self, launch_id, reservation_id):
        raise NotImplementedError

    def checkout_fw(self, fworker, launch_dir, fw_id=None, host=None,
                    ip=None, state="RUNNING"):
        m_fw = self._get_a_fw_to_run(fworker.query, fw_id=fw_id)
        if not m_fw:
            return None, None

        # TODO: reserved launch stuff
        reserved_launch = False

        launch_id = (reserved_launch.launch_id if reserved_launch
                     else self.get_new_launch_id())
        # TODO: trackers
        trackers=None

        m_launch = Launch(state, launch_dir, fworker, host, ip,
                          trackers=trackers, state_history=None,
                          launch_id=launch_id, fw_id=m_fw.fw_id)
        with self._db as c:
            c.execute('INSERT INTO launches VALUES(?, ?, ?)',
                      (launch_id, m_fw.fw_id, launch_to_sqlite(m_launch)))

        if not reserved_launch:
            m_fw.launches.append(m_launch)
        else:
            raise NotImplementedError

        m_fw.state = state
        # TODO: Why upsert here?
        #       Why not just update the STATE field? - because of launches?
        self._upsert_fws([m_fw])
        self._refresh_wf(m_fw.fw_id)

        # TODO: Duplicate run stuff
        # if state == "RUNNING"

        # TODO: Backup fw_data?

        return m_fw, launch_id

    def change_launch_dir(self, launch_id, launch_dir):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.launch_dir = launch_dir
        with self._db as c:
            c.execute('UPDATE launches SET data = ? '
                      'WHERE launch_id = ?',
                      (launch_to_sqlite(m_launch), launch_id))

    def restore_backup_data(self, launch_id, fw_id):
        # called from Rocket.run() if everything falls apart completely
        raise NotImplementedError

    def complete_launch(self, launch_id, action=None, state='COMPLETED'):
        m_launch = self.get_launch_by_id(launch_id)
        m_launch.state = state
        if action:
            m_launch.action = action

        with self._db as c:
            c.execute('UPDATE launches SET data = ? '
                      'WHERE launch_id = ?',
                      (launch_to_sqlite(m_launch), launch_id))
            # find related fireworks
            for (fw_id,) in c.execute('SELECT fw_id FROM launches '
                                      'WHERE launch_id = ?', (launch_id,)):
                self._refresh_wf(fw_id)

        return m_launch.to_dict()

    def ping_launch(self, launch_id, ptime=None, checkpoint=None):
        m_launch = self.get_launch_by_id(launch_id)
        for tracker in m_launch.trackers:
            track_file(m_launch.launch_dir)
        m_launch.touch_history(ptime, checkpoint=checkpoint)

        with self._db as c:
            c.execute('UPDATE launches SET data = ? '
                      'WHERE launch_id = ?',
                      (launch_to_sqlite(m_launch), launch_id))

    def _get_new_and_increment(self, table, increment):
        with self._db as c:
            c2 = c.execute('SELECT value FROM meta WHERE name = ?',
                           (table,))
            next_id = c2.fetchone()[0]
            c.execute('UPDATE meta SET value = ? WHERE name = ?',
                      (next_id + increment, table))

        return next_id

    def _get_new_workflow_id(self, quantity=1):
        # not official API, a hack to make workflow->firework mapping work
        return self._get_new_and_increment('next_workflow_id', quantity)

    def get_new_fw_id(self, quantity=1):
        return self._get_new_and_increment('next_fw_id', quantity)

    def get_new_launch_id(self):
        return self._get_new_and_increment('next_launch_id', 1)

    def _upsert_fws(self, fws, reassign_all=False):
        """Insert into Fireworks 'collection'"""
        old_new = {}
        fws.sort(key=lambda x: x.fw_id)

        if reassign_all:
            used_ids = []
            first_new_id = self.get_new_fw_id(quantity=len(fws))

            for new_id, fw in enumerate(fws, start=first_new_id):
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id
                used_ids.append(new_id)

            with self._db as c:
                # delete rows that existed
                # TODO: How to use 'WHERE fw_id IN used_ids'?
                # WHERE fw_id IN (?,)*len(fws)
                # '(' + ','.join(['?'] * len(fws)) + ')'
                c.executemany('DELETE FROM fireworks WHERE fw_id = ?',
                              ((i,) for i in used_ids))
                # Use REPLACE to upsert
                c.executemany('REPLACE INTO fireworks VALUES(?,?,?)',
                              (firework_to_sqlite(fw) for fw in fws))
        else:
            for fw in fws:
                if fw.fw_id < 0:
                    new_id = self.get_new_fw_id()
                    old_new[fw.fw_id] = new_id
                    fw.fw_id = new_id
            with self._db as c:
                c.executemany('REPLACE INTO fireworks VALUES(?,?,?)',
                              (firework_to_sqlite(fw) for fw in fws))

        return old_new

    def rerun_fw(self, fw_id, **kwargs):
        raise NotImplementedError

    def get_recovery(self, fw_id, launch_id='last'):
        raise NotImplementedError

    def _refresh_wf(self, fw_id):
        # TODO: Locks check
        with self._db as c:
            # TODO: Make this lazy again
            wf = self.get_wf_by_fw_id(fw_id)
            updated_ids = wf.refresh(fw_id)
            self._update_wf(wf, updated_ids, cursor=c)
        # TODO: Extra junk in the 2nd except branch
        # ^ Can probably replicate and just update FIZZLED too

    def _update_wf(self, wf, updated_ids, cursor):
        # TODO: I've changed the API of this call, is this bad?
        # Inherits 'Lock' from calling function
        # in sqlite, 'Lock' is the context manager
        updated_fws = [wf.id_fw[fid] for fid in updated_ids]
        old_new = self._upsert_fws(updated_fws)
        wf._reassign_ids(old_new)

        query_node = [f for f in wf.id_fw
                      if f not in old_new.values() or old_new.get(f, None) == f][0]

        # TODO: We're finding workflow_id again here, despite
        #       the fact we were indirectly just using it...
        workflow_id = cursor.execute('SELECT workflow_id FROM mapping '
                                     'WHERE firework_id = ?',
                                     (query_node,)).fetchone()[0]
        # rewrite the payload of the workflow
        cursor.execute('UPDATE workflows SET data = ?'
                       'WHERE wf_id = ?',
                       (workflow_to_sqlite(wf), workflow_id))

    def _steal_launches(self, thief_fw):
        raise NotImplementedError

    def set_priority(self, fw_id, priority):
        raise NotImplementedError

    def get_logdir(self):
        return self.logdir

    def add_offline_run(self):
        raise NotImplementedError

    def recover_offline(self):
        raise NotImplementedError

    def forget_offline(self):
        raise NotImplementedError

    def get_tracker_data(self, fw_id):
        raise NotImplementedError

    def get_launchdir(self, fw_id, launch_idx=-1):
        raise NotImplementedError

    def log_message(self, level, message):
        raise NotImplementedError


class LazyFirework(Firework):
    # Yeah...
    def __init__(self, fw_id, hook):
        self.fw_id = fw_id
        self.hook = hook
