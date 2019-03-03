"""Internet? Where we're going we don't need internet

"""
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
from bson import json_util
import datetime
import json
import pathlib
import sqlite3

from .firework import Firework, Workflow, Launch


class Collection(object):
    """Mimics a MongoDB collection, kinda"""
    def __init__(self, rootdir, name):
        self.rootdir = pathlib.Path(rootdir) / name
        if not self.rootdir.exists():
            self.rootdir.mkdir(parents=True)

    def read(self, item):
        """Read given entry"""
        item += '.json'

        with (self.rootdir / item).open('r') as f:
            return json.loads(f.read(),
                              object_hook=json_util.object_hook)

    def write(self, item, content):
        """Write given entry, overwriting if exists"""
        item += '.json'

        with (self.rootdir / item).open('w') as f:
            f.write(json.dumps(content,
                               default=json_util.default))

    def find_one(self, **kwargs):
        for item in self.rootdir.glob('*json'):
            with item.open('r') as f:
                stuff = json.loads(f.read(),
                                   object_hook=json_util.object_hook)
                if all(stuff[k] == kwargs[k]
                       for k in kwargs):
                    return stuff


class OfflineLaunchPad(object):
    def __init__(self, *args, logdir=None, **kwargs):
        self._db = sqlite3.connect(':memory:')

        self._metadata = Collection('.launchpad', 'metadata')
        self.fireworks = Collection('.launchpad', 'fireworks')
        self.workflows = Collection('.launchpad', 'workflows')
        self.launches = Collection('.launchpad', 'launches')

        self.logdir = logdir

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
            # reset count of ids
            c.execute('DROP TABLE IF EXISTS meta')
            c.execute('CREATE TABLE meta(name TEXT, value INTEGER)')
            c.executemany('INSERT INTO meta VALUES(?, 1)',
                          [('next_fw_id',), ('next_launch_id',)])
            c.execute('DROP TABLE IF EXISTS fireworks')
            c.execute('''CREATE TABLE fireworks(fw_id INTEGER,
                                                state TEXT,
                                                data TEXT)''')

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
        self.workflows.write('1', wf.to_db_dict())

        return old_new

    def bulk_add_wfs(self, wfs):
        raise NotImplementedError

    def append_wf(self, new_wf, fw_ids, detour=False, pull_spec_mods=True):
        raise NotImplementedError

    def get_launch_by_id(self, launch_id):
        raise NotImplementedError

    def get_fw_dict_by_id(self, fw_id):
        try:
            fw_dict = self.fireworks.load(str(fw_id))
        except FileNotFoundError:
            raise ValueError

        return fw_dict

    def get_fw_by_id(self, fw_id):
        return Firework.from_dict(self.get_fw_dict_by_id(fw_id))

    def get_wf_by_fw_id(self, fw_id):
        # search through all Workflows, looking for correct fw_id?
        # or could have some index file, but this could get stale
        raise NotImplementedError

    def get_wf_by_fw_id_lzyfw(self, fw_id):
        wf = self.workflows.find_one(fw_id=fw_id)

        fws = [LazyFirework(fw_id, self.fireworks, self.launches)
               for fw_id in wf['nodes']]

        if 'fw_states' in wf:
            fw_states = dict([(int(k), v)
                              for (k, v) in wf['fw_states'].items()])
        else:
            fw_states = None

        return Workflow(fws, wf['links'], wf['name'],
                        wf['metadata'], wf['created_on'],
                        wf['updated_on'], fw_states)

    def delete_wf(self, fw_id, delete_launch_dirs=False):
        raise NotImplementedError

    def get_wf_summary_dict(self, fw_id, mode='more'):
        raise NotImplementedError

    def get_fw_ids(self, **kwargs):
        raise NotImplementedError

    def get_wf_ids(self, **kwargs):
        raise NotImplementedError

    def run_exists(self, fworker=None):
        raise NotImplementedError

    def future_run_exists(self, fworker=None):
        raise NotImplementedError

    def tuneup(self, bkground=True):
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
        # some stuff about priority todo

        if fw_id:
            firework = self.fireworks.read(str(fw_id))
        else:
            firework = self.fireworks.find_one(state='READY')

        if checkout:
            firework.state = 'RESERVED'
            firework.updated_on = datetime.datetime.utcnow()

            self.fireworks.write(str(fw_id), firework)



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

        self.launches.write(str(m_launch.launch_id),
                            m_launch)

        if not reserved_launch:
            m_fw.launches.append(m_launch)
        else:
            raise NotImplementedError

        m_fw.state = state
        self._upsert_fws([m_fw])
        self._refresh_wf(m_fw.fw_id)

        # TODO: Duplicate run stuff
        # if state == "RUNNING"

        # TODO: Backup fw_data?

    def change_launch_dir(self, launch_id, launch_dir):
        raise NotImplementedError

    def restore_backup_data(self, launch_id, fw_id):
        # Doesn't seem to ever be used by anything, can ignore
        raise NotImplementedError

    def complete_launch(self, launch_id, action=None, state='COMPLETED'):
        raise NotImplementedError

    def ping_launch(self, launch_id, ptime=None, checkpoint=None):
        raise NotImplementedError

    def _get_new_and_increment(self, table, increment):
        with self._db as c:
            c2 = c.execute('SELECT value FROM meta WHERE name = ?',
                           (table,))
            next_id = c2.fetchone()[0]
            c.execute('UPDATE meta SET value = ? WHERE name = ?',
                      (next_id + increment, table))

        return next_id

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
                c.executemany('DELETE FROM fireworks WHERE fw_id = ?',
                              [(i,) for i in used_ids])
                c.executemany('INSERT INTO fireworks VALUES(?,?,?)',
                              [self._fw_to_sqlite(fw) for fw in fws])
        else:
            for fw in fws:
                if fw.fw_id < 0:
                    new_id = self.get_new_fw_id()
                    old_new[fw.fw_id] = new_id
                    fw.fw_id = new_id
            with self._db as c:
                c.executemany('INSERT INTO fireworks VALUES(?,?,?)',
                              [self._fw_to_sqlite(fw) for fw in fws])

        return old_new

    def rerun_fw(self, fw_id, **kwargs):
        raise NotImplementedError

    def get_recovery(self, fw_id, launch_id='last'):
        raise NotImplementedError

    def _refresh_wf(self, fw_id):
        # TODO: Locks
        wf = self.get_wf_by_fw_id_lzyfw(fw_id)
        updated_ids = wf.refresh(fw_id)
        self._update_wf(wf, updated_ids)
        # TODO: Extra junk in the 2nd except branch

    def _update_wf(self, wf, updated_ids):
        updated_fws = [wf.id_fw[fid] for fid in updated_ids]
        old_new = self._upsert_fws(updated_fws)
        wf._reassign_ids(old_new)

        query_node = None
        for f in wf.id_fw:
            if f not in old_new.values() or old_new.get(f, None) == f:
                query_node = f
                break
        else:
            raise ValueError

        wf = wf.to_db_dict()
        wf['locked'] = True
        self.workflows.write('1', wf)

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
    pass
