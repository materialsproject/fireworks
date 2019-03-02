"""Internet? Where we're going we don't need internet

"""
# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
from bson import json_util
import json
import pathlib

from .firework import Firework, Workflow


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


class OfflineLaunchPad(object):
    def __init__(self, *args, **kwargs):
        self._metadata = Collection('.launchpad', 'metadata')
        self.fireworks = Collection('.launchpad', 'firework')
        self.workflows = Collection('.launchpad', 'workflow')

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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

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
        raise NotImplementedError

    def change_launch_dir(self, launch_id, launch_dir):
        raise NotImplementedError

    def restore_backup_data(self, launch_id, fw_id):
        raise NotImplementedError

    def complete_launch(self, launch_id, action=None, state='COMPLETED'):
        raise NotImplementedError

    def ping_launch(self, launch_id, ptime=None, checkpoint=None):
        raise NotImplementedError

    def get_new_fw_id(self, quantity=1):
        try:
            next_id = self._metadata.read('next_fw_id')
        except FileNotFoundError:
            next_id = 1
        self._metadata.write('next_fw_id', next_id + quantity)

        return next_id

    def get_new_launch_id(self):
        raise NotImplementedError

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

            self.fireworks.write(str(fw.fw_id), fw.to_db_dict())
        else:
            for fw in fws:
                if fw.fw_id < 0:
                    new_id = self.get_new_fw_id()
                    old_new[fw.fw_id] = new_id
                    fw.fw_id = new_id
                self.fireworks.write(str(fw.fw_id), fw.to_db_dict())

        return old_new

    def rerun_fw(self, fw_id, **kwargs):
        raise NotImplementedError

    def get_recovery(self, fw_id, launch_id='last'):
        raise NotImplementedError

    def _refresh_wf(self, fw_id):
        raise NotImplementedError

    def _update_wf(self, wf, updated_ids):
        raise NotImplementedError

    def _steal_launches(self, thief_fw):
        raise NotImplementedError

    def set_priority(self, fw_id, priority):
        raise NotImplementedError

    def get_logdir(self):
        raise NotImplementedError

    def add_offline_run(self):
        raise NotImplementedError

    def recover_offline(self):
        raise NotImplementedError

    def forget_offline(self):
        raise NotImplementedError

    def get_tracker_data(self, fw_id):
        raise NotImplementedError

    def get_launchdir(self, fw-id, launch_idx=-1):
        raise NotImplementedError

    def log_message(self, level, message):
        raise NotImplementedError
