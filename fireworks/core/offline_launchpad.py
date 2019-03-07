"""Internet? Where we're going we don't need internet

Stores everything in a sqlite database (instead of MongoDB)

Implementation notes:

Currently there are 4 tableso storing everything

*meta* (table_name, next_id)

Stores the next_id for each other table.  Could maybe use autoincrement
instead, but I read a couple weird things about using that.

When new ids are requested (via get_new_X methods) the rows in the appropriate
table are also INSERTed.  **All** other operations should then just UPDATE,
rather than REPLACE.  Unless you're deleting, that's ok I guess.

*workflows* (workflow_id, data)

Stores the workflow objects as bson dumps of the objects.  Different to MongoDB,
each Workflow has an ID.  This is used to quickly move between Fireworks in
the same Workflow (without requiring the deserialisation of the Workflow).

*fireworks* (fw_id, workflow_id, useful attributes, data)

Stores Firework objects.  FW_ID is used as the index.  The mapping to Workflow
is second column.  Last column is the bson dump of the object.

Between all these, some useful attributes are pulled out to help with searching
currently:
 - state

In the future:
 - created_on (for sorting)
 - fworker name / category data (for FWorker.query)

*launches* (launch_id, fw_id, data)

Stores Launch objects.  These store the fw_id they are associated to, then
a bson dump of the object.


*duplicate launches* (launch_id, fw_id)

If I've understood the duplicate feature correctly, some Fireworks try and
piggyback on an existing Launch object if it also satisfies them. The current
many to one schema in *launches* won't allow for this as each Launch_ID must be
unique.

I think duplicates can be implemented with a duplicates table which map
existing Launch_IDs to FW_IDs.  Here Launch_ID aren't unique keys any more.
These FW_ID objects aren't the owners/original creators of the launch either,
but represent the FW_ID that has been satisfied with an existing Launch.



"""
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
from bson import json_util as json
import datetime
import sqlite3

from fireworks.utilities.fw_utilities import get_fw_logger
from .firework import Firework, Workflow, Launch
from .fworker import FWorker

# this is a dict with some mongodb mumbo jumbo
# we want to know what the default looks like to compare against later
_DEFAULT_FWORKER_QUERY = FWorker().query


def _nq(n):
    # for IN statements
    # generates a (?,...,?) block with *n* values
    return '(' + ','.join(['?'] * n) + ')'


def firework_to_sqlite(firework):
    d = firework.to_dict()
    fw_id = d.pop('fw_id')
    _ = d.pop('launches', None)
    _ = d.pop('archived_launches', None)
    d = json.dumps(d)

    return d

def sqlite_to_firework(firework):
    fw_id, _, state, data = firework
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
    def __init__(self, address=None, host='localhost',
                 logdir=None, strm_lvl=None, user_indices=None,
                 wf_user_indices=None):
        if address is None:
            # default location for sqlite file defined somewhere etc..
            raise NotImplementedError
        self._address = address  # store how we got here
        self._db = sqlite3.connect(address)
        with self._db as c:
            c.execute('PRAGMA foreign_keys = ON')

        self.host = host
        # set up logger
        self.logdir = logdir
        self.strm_lvl = strm_lvl if strm_lvl else 'INFO'
        self.m_logger = get_fw_logger('launchpad', l_dir=self.logdir, stream_level=self.strm_lvl)

        self.user_indices = user_indices if user_indices else []
        self.wf_user_indices = wf_user_indices if wf_user_indices else []


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
            # Drop in correct order to not offend foreign key constraints
            c.execute('DROP TABLE IF EXISTS launches')
            c.execute('DROP TABLE IF EXISTS fireworks')
            c.execute('DROP TABLE IF EXISTS workflows')
            c.execute('DROP TABLE IF EXISTS meta')

            # TODO: Can squish these commands into single call?
            # reset count of ids
            c.execute('CREATE TABLE meta(name TEXT, next_id INTEGER)')
            c.executemany('INSERT INTO meta VALUES(?, 1)',
                          (('workflows',),
                           ('fireworks',),
                           ('launches',)))
            c.execute('''CREATE TABLE workflows(workflow_id INTEGER UNIQUE,
                                                data TEXT)''')
            c.execute('''CREATE TABLE fireworks(fw_id INTEGER UNIQUE,
                                                workflow_id INTEGER,
                                                state TEXT,
                                                data TEXT,
                         FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
            )''')
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

        # Adds Workflow with single transaction
        with self._db as c:
            workflow_id = self._get_new_workflow_id(cursor=c)
            old_new = self._update_fws(list(wf.id_fw.values()),
                                       workflow_id, c,
                                       reassign_all=reassign_all)
            wf._reassign_ids(old_new)
            c.execute('UPDATE workflows SET data = ? '
                      'WHERE workflow_id = ?',
                      (workflow_to_sqlite(wf), workflow_id))
        return old_new

    def bulk_add_wfs(self, wfs):
        for wf in wfs:
            self.add_wf(wf)

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=True):
        # grab existing workflow
        wf = self.get_wf_by_fw_id(fw_ids[0])
        # call append_wf on that to get updated IDs
        updated_ids = wf.append_wf(new_wf, fw_ids, detour=detour,
                                   pull_spec_mods=pull_spec_mods)
        with self._db as c:
            # create firework stubs for new fireworks
            self._update_wf(wf, updated_ids, cursor=c)

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
                                 'WHERE fw_id = ?', (fw_id,)).fetchall()
        firework = sqlite_to_firework(val)
        # these are converted into Launch objects by Firework.from_dict?
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
            workflow = c.execute('SELECT * FROM workflows WHERE workflow_id = '
                                 '(SELECT workflow_id FROM fireworks WHERE '
                                 'fw_id = ?)', (fw_id,)).fetchone()
            wf_id, wf_payload = workflow
            fireworks = c.execute('SELECT * FROM fireworks '
                                  'WHERE workflow_id = ?', (wf_id,)).fetchall()
            launches = c.execute('SELECT l.* FROM launches AS l '
                                 'INNER JOIN fireworks AS f '
                                 'ON f.fw_id = l.fw_id '
                                 'WHERE f.workflow_id = ?', (wf_id,)).fetchall()
        workflow = sqlite_to_workflow(wf_payload)

        # Ugly little block, need to deserialise the fireworks
        # match them to launches (using dict of {fw_id: fw_dict}
        # them create the Firework objects (which also makes the Launch)
        fireworks = {fw[0]: sqlite_to_firework(fw) for fw in fireworks}
        for fw in fireworks.values():
            fw['launches'] = []
        # attach launches
        for payload in launches:
            l = sqlite_to_launch(payload)
            fireworks[l['fw_id']]['launches'].append(l)
        fireworks = [Firework.from_dict(fw) for fw in fireworks.values()]

        wf = Workflow(fireworks, workflow['links'], workflow['name'],
                      workflow['metadata'], workflow['created_on'],
                      workflow['updated_on'])
        # TODO: Remove? little hack to make things easier later
        wf._wf_id = wf_id

        return wf

    def get_wf_by_fw_id_lzyfw(self, fw_id):
        with self._db as c:
            workflow = c.execute('SELECT * FROM workflows WHERE workflow_id = '
                                 '(SELECT workflow_id FROM fireworks WHERE '
                                 'fw_id = ?)', (fw_id,)).fetchone()
            wf_id, wf_payload = workflow
            fireworks = c.execute('SELECT fw_id FROM fireworks '
                                  'WHERE workflow_id = ?', (wf_id)).fetchall()

        workflow = sqlite_to_workflow(wf_payload)
        fws = [LazyFirework(fw_id, self)
               for fw_id in fireworks]

        if 'fw_states' in workflow:
            fw_states = dict([(int(k), v)
                              for (k, v) in workflow['fw_states'].items()])
        else:
            fw_states = None

        wf = Workflow(fws, workflow['links'], workflow['name'],
                      workflow['metadata'], workflow['created_on'],
                      workflow['updated_on'], fw_states)
        # TODO: Remove this little hack
        wf._wf_id = wf_id

        return wf

    def delete_wf(self, fw_id, delete_launch_dirs=False):
        with self._db as c:
            (workflow_id,)= c.execute('SELECT workflow_id FROM mapping '
                                      'WHERE fw_id = ?', (fw_id,)).fetchone()
            if delete_launch_dirs:
                # iterate over launches in given workflow_id
                for launch in c.execute('SELECT l.* FROM launches AS l '
                                        'INNER JOIN fireworks AS f '
                                        'ON f.fw_id = l.fw_id '
                                        'WHERE f.workflow_id = ?',
                                        (workflow_id,)):
                    # rehydrate all launches so we can nuke the launch dir
                    m_launch = sqlite_to_launch(launch)
                    shutil.rmtree(m_launch['launch_dir'], ignore_errors=True)

            # delete launches
            c.execute('DELETE FROM launches '
                      'WHERE fw_id in '
                      '(SELECT fw_id FROM fireworks WHERE workflow_id = ?)',
                      (workflow_id,))
            # delete fireworks
            c.execute('DELETE FROM fireworks WHERE workflow_id = ?',
                      (workflow_id,))
            # finally delete workflow
            c.execute('DELETE FROM workflows WHERE workflow_id = ?',
                      (workflow_id,))

    def get_wf_summary_dict(self, fw_id, mode='more'):
        raise NotImplementedError

    def get_fw_ids(self, **kwargs):
        raise NotImplementedError

    def get_wf_ids(self, **kwargs):
        raise NotImplementedError

    def run_exists(self, fworker=None):
        # we can't do custom queries yet
        # so anything spicy gets rejected
        if fworker and not (fworker.query == _DEFAULT_FWORKER_QUERY):
            raise NotImplementedError
        return bool(self._get_a_fw_to_run(query=None,
                                          checkout=False))

    def future_run_exists(self, fworker=None):
        if self.run_exists(fworker):
            return True
        if fworker and not (fworker.query == _DEFAULT_FWORKER_QUERY):
            raise NotImplementedError
        with self._db as c:
            # iterate over 'active' fireworks checking for waiting children
            # grab firework IDs and workflow blobs
            for (fw_id, wf) in c.execute(
                    'SELECT f.fw_id, w.data FROM fireworks as f '
                    'INNER JOIN workflows AS w ON f.workflow_id = w.workflow_id '
                    'WHERE f.state in ("RUNNING", "RESERVED")'):
                wf = sqlite_to_workflow(wf)
                children = wf['links'][str(fw_id)]
                # If any children are "WAITING" then we've got future work
                if c.execute('SELECT 1 FROM fireworks '
                             'WHERE fw_id IN ' + _nq(len(children)) + ' '
                             'AND state = "WAITING"',
                             children).fetchone():
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
        # TODO: Make Lazy
        wf = self.get_wf_by_fw_id(fw_id)
        if wf.state != 'ARCHIVED':
            for fw in wf.fws:
                self.rerun_fw(fw.fw_id)

            # necessary to grab again?
            wf = self.get_wf_by_fw_id(fw_id)
            for fw in wf.fws:
                fw.state = 'ARCHIVED'
                # commit changes
                # TODO maybe revert like original and do manual?
                with self._db as c:
                    self._update_fws([fw], wf._wf_id, c)
                self._refresh_wf(fw.fw_id)

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
        m_fw.state = state
        with self._db as c:
            c.execute('UPDATE launches SET fw_id=?, data=? '
                      'WHERE launch_id = ?',
                      (m_fw.fw_id, launch_to_sqlite(m_launch), launch_id))
            c.execute('UPDATE fireworks SET state = ?, data = ? '
                      'WHERE fw_id = ?',
                      (m_fw.state, firework_to_sqlite(m_fw), m_fw.fw_id))

        if not reserved_launch:
            m_fw.launches.append(m_launch)
        else:
            raise NotImplementedError

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

    def _get_new_and_increment(self, table, quantity, cursor):
        # grabs the next value from the meta counter table
        # increments the meta counter table (by quantity)
        # inserts empty rows in the appropriate table
        # ie row allocation is only done here, allowing all other
        # methods to do UPDATE only (and never touch the index column)
        try:
            idxname = {
                'workflows': 'workflow_id',
                'fireworks': 'fw_id',
                'launches': 'launch_id',
            }[table]
        except KeyError:
            # quick safety check since we're doing string tricks
            raise ValueError

        # maybe start a transaction, maybe continue one
        if cursor is None:
            with self._db as c:
                (next_id,) = c.execute('SELECT next_id FROM meta WHERE name = ?',
                                       (table,)).fetchone()
                c.execute('UPDATE meta SET next_id = ? WHERE name = ?',
                          (next_id + quantity, table))
                # creates rows with all NULL values
                c.executemany('INSERT INTO {}({}) values(?)'
                              ''.format(table, idxname), (
                                  (i,) for i in range(next_id, next_id + quantity)))
        else:
            c = cursor
            (next_id,) = c.execute('SELECT next_id FROM meta WHERE name = ?',
                                   (table,)).fetchone()
            c.execute('UPDATE meta SET next_id = ? WHERE name = ?',
                      (next_id + quantity, table))
            c.executemany('INSERT INTO {}({}) values(?)'
                          ''.format(table, idxname), (
                              (i,) for i in range(next_id, next_id + quantity)))

        return next_id

    def _get_new_workflow_id(self, quantity=1, cursor=None):
        # not official API, a hack to make workflow->firework mapping work
        return self._get_new_and_increment('workflows',
                                           quantity=quantity,
                                           cursor=cursor)

    def get_new_fw_id(self, quantity=1, cursor=None):
        return self._get_new_and_increment('fireworks',
                                           quantity=quantity,
                                           cursor=cursor)

    def get_new_launch_id(self, cursor=None):
        return self._get_new_and_increment('launches',
                                           quantity=1,
                                           cursor=cursor)

    def _update_fws(self, fws, workflow_id, cursor, reassign_all=False):
        """Update Fireworks in collection

        Parameters
        ----------
        fws : list of Firework
          who to update
        workflow_id : int
          index of the workflow they belong to
        cursor : sqlite.Connection
          activate transaction
        reassign_all : bool
          if to give all fireworks a new id

        """
        old_new = {}
        fws.sort(key=lambda x: x.fw_id)

        if reassign_all:
            first_new_id = self.get_new_fw_id(quantity=len(fws),
                                              cursor=cursor)
            for new_id, fw in enumerate(fws, start=first_new_id):
                old_new[fw.fw_id] = new_id
                fw.fw_id = new_id
        else:
            for fw in fws:
                if fw.fw_id < 0:
                    new_id = self.get_new_fw_id(cursor=cursor)
                    old_new[fw.fw_id] = new_id
                    fw.fw_id = new_id

        cursor.executemany('UPDATE fireworks SET workflow_id = ?, state = ?, data = ? '
                           'WHERE fw_id = ?', (
                               (workflow_id, fw.state, firework_to_sqlite(fw), fw.fw_id)
                               for fw in fws
                           ))
        return old_new

    def rerun_fw(self, fw_id, rerun_duplicates=True, recover_launch=None,
                 recover_mode=None):
        # reset a Firework so it can be run again
        try:
            with self._db as c:
                (state,) = c.execute('SELECT state FROM fireworks '
                                     'WHERE fw_id = ?', (fw_id,)).fetchone()
        except TypeError:
            raise ValueError("Firework doesn't exist")

        # TODO: duplicates
        duplicates = []
        if rerun_duplicates:
            pass
        reruns = []

        # TODO: Launch recovery
        if recover_launch is not None:
            pass

        if state in ['ARCHIVED', 'DEFUSED']:
            # cannot rerun
            pass
        elif state == 'WAITING' and not recover_launch:
            # nothing to do
            pass
        else:
            # TODO: Make lazy
            with self._db as c:
                # grab the workflow
                wf = self.get_wf_by_fw_id(fw_id)
                updated_ids = wf.rerun_fw(fw_id)
                self._update_wf(wf, updated_ids, c)
                reruns.append(fw_id)

        for f in duplicates:
            # TODO: Duplicates
            pass
        
        return reruns

    def get_recovery(self, fw_id, launch_id='last'):
        raise NotImplementedError

    def _refresh_wf(self, fw_id):
        # TODO: Locks check
        with self._db as c:
            # TODO: Make this lazy again
            wf = self.get_wf_by_fw_id(fw_id)
            updated_ids = wf.refresh(fw_id)
            self._update_wf(wf, updated_ids, c)
        # TODO: Extra junk in the 2nd except branch
        # ^ Can probably replicate and just update FIZZLED too

    def _update_wf(self, wf, updated_ids, cursor):
        # TODO: Little hack that needs removing, see get_wf_from_wf_id
        workflow_id = wf._wf_id
        updated_fws = [wf.id_fw[fid] for fid in updated_ids]
        # old new will have some negative ids to positive ids
        old_new = self._update_fws(updated_fws, workflow_id, cursor)
        wf._reassign_ids(old_new)

        query_node = [f for f in wf.id_fw
                      if f not in old_new.values() or old_new.get(f, None) == f][0]
        # rewrite the payload of the workflow
        cursor.execute('UPDATE workflows SET data = ?'
                       'WHERE workflow_id = ?',
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
