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

    def get_new_fw_id(self, quantity=1):
        try:
            next_id = self._metadata.read('next_fw_id')
        except FileNotFoundError:
            next_id = 1
        self._metadata.write('next_fw_id', next_id + quantity)

        return next_id

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
