from StringIO import StringIO
from collections import defaultdict
import tarfile
from fireworks.core.firework import FireWork
from fireworks.utilities.dict_mods import apply_mod
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 27, 2013'


class Workflow(FWSerializable):
    # TODO: if performance of parent_links is an issue, override delitem/setitem to ensure it's always updated
    class Links(dict, FWSerializable):

        @property
        def nodes(self):
            return self.keys()

        @property
        def parent_links(self):
            d = defaultdict(list)
            for (parent, children) in self.iteritems():
                # add the parents
                for child in children:
                    d[child].append(parent)
            return dict(d)

        def to_dict(self):
            return dict(self)

        def to_db_dict(self):
            # convert to str form for Mongo, which cannot have int keys
            m_dict = {'links': dict([(str(k), list(v)) for (k, v) in self.iteritems()]),
                      'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.iteritems()]),
                      'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            m_dict = dict([(int(k), list(v)) for (k, v) in m_dict.iteritems()])
            return Workflow.Links(m_dict)

    def __init__(self, fireworks, links_dict=None, metadata={}):

        """
        :param fireworks: a list of FireWork objects
        :param links_dict: A dict representing workflow links
        :param metadata: metadata for this Workflow
        """

        links_dict = links_dict if links_dict else {}

        self.id_fw = {}  # main dict containing mapping of an id to a FireWork object
        for fw in fireworks:
            # check uniqueness, cannot have two FWs with the same id!
            if fw.fw_id in self.id_fw:
                raise ValueError('FW ids must be unique!')
            self.id_fw[fw.fw_id] = fw

            if fw.fw_id not in links_dict:
                links_dict[fw.fw_id] = []

            # transform any non-iterable values to iterables
            for k, v in links_dict.iteritems():
                if not isinstance(v, list):
                    links_dict[k] = [v]

        self.links = Workflow.Links(links_dict)

        # sanity: make sure the set of nodes from the links_dict is equal to the set of nodes from id_fw
        if set(self.links.nodes) != set(self.id_fw.keys()):
            raise ValueError("Specified links don't match given FW")

        self.metadata = metadata

    def apply_action(self, action, fw_id):
        updated_ids = []

        if action.command in ['CONTINUE', 'BREAK']:
            # Do nothing
            pass

        if action.command == 'DEFUSE':
            # mark all children as defused
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].state = 'DEFUSED'
                updated_ids.append(cfid)

        if action.command == 'MODIFY' or 'CREATE':
            for cfid in self.links[fw_id]:
                self.id_fw[cfid].spec.update(action.mod_spec.get('dict_update', {}))

                for mod in action.mod_spec.get('dict_mods', []):
                    apply_mod(mod, self.id_fw[cfid].spec)
                    updated_ids.append(cfid)

        if action.command == 'CREATE':
            create_fw = action.mod_spec['create_fw']
            self.links[fw_id].append(create_fw.fw_id)
            self.links[create_fw.fw_id] = []  # TODO: allow this to be children of original FW
            self.id_fw[create_fw.fw_id] = create_fw
            updated_ids.append(create_fw.fw_id)

        # TODO: implement the remaining actions
        return updated_ids

    def refresh(self, fw_id, updated_ids=None):
        #TODO: document this better

        updated_ids = updated_ids if updated_ids else set()

        fw = self.id_fw[fw_id]
        prev_state = fw.state

        # if we're defused, just skip altogether
        if fw.state == 'DEFUSED':
            return updated_ids

        # what are the parent states?
        parent_states = [self.id_fw[p].state for p in self.links.parent_links.get(fw_id, [])]

        if len(parent_states) != 0 and not all([s == 'COMPLETED' for s in parent_states]):
            m_state = 'WAITING'

        else:
            # my state depends on launch
            max_score = 0
            m_state = 'READY'
            m_action = None

            # TODO: pick the first launch in terms of end date that matches 'COMPLETED'; multiple might exist
            for l in fw.launches:
                if FireWork.STATE_RANKS[l.state] > max_score:
                    max_score = FireWork.STATE_RANKS[l.state]
                    m_state = l.state
                    if m_state == 'COMPLETED':
                        m_action = l.action

        fw.state = m_state

        if m_state != prev_state:
            if m_state == 'COMPLETED':
                updated_ids = updated_ids.union(self.apply_action(m_action, fw.fw_id))

            updated_ids.add(fw_id)
            # refresh all the children
            for child_id in self.links[fw_id]:
                updated_ids = updated_ids.union(self.refresh(child_id, updated_ids))

        return updated_ids

    @property
    def root_fw_ids(self):
        all_ids = set(self.links.nodes)
        child_ids = set(self.links.parent_links.keys())
        root_ids = all_ids.difference(child_ids)
        return list(root_ids)

    def _reassign_ids(self, old_new):
        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fw.iteritems():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fw = new_id_fw

        # update the Links
        new_l = {}
        for (parent, children) in self.links.iteritems():
            new_parent = old_new.get(parent, parent)
            new_l[new_parent] = [old_new.get(child, child) for child in children]
        self.links = Workflow.Links(new_l)

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self.id_fw.itervalues()], 'links': self.links.to_dict(), 'metadata': self.metadata}

    def to_db_dict(self):
        m_dict = self.links.to_db_dict()
        m_dict['metadata'] = self.metadata
        return m_dict

    @classmethod
    def from_dict(cls, m_dict):
        return Workflow([FireWork.from_dict(f) for f in m_dict['fws']], Workflow.Links.from_dict(m_dict['links']), m_dict['metadata'])

    @classmethod
    def from_FireWork(cls, fw):
        return Workflow([fw], None)

    #TODO: add .gz support
    def to_tarfile(self, f_name='fwf.tar', f_format='json'):
        try:
            out = tarfile.open(f_name, "w")

            # write out the links
            l_str = self.links.to_format(f_format)
            l_info = tarfile.TarInfo('links.' + f_format)
            l_info.size = len(l_str)
            out.addfile(l_info, StringIO(l_str))

            # write out fws
            for fw in self.id_fw.itervalues():
                fw_str = fw.to_format(f_format)
                fw_info = tarfile.TarInfo('fw_{}.{}'.format(fw.fw_id, f_format))
                fw_info.size = len(fw_str)
                out.addfile(fw_info, StringIO(fw_str))

        finally:
            out.close()

    @classmethod
    def from_tarfile(cls, tar_filename):
        t = tarfile.open(tar_filename, 'r')
        links = None
        fws = []
        for f_name in t.getnames():
            m_file = t.extractfile(f_name)
            m_format = m_file.name.split('.')[-1]
            m_contents = m_file.read()
            if 'links' in f_name:
                links = Workflow.Links.from_format(m_contents, m_format)
            else:
                fws.append(FireWork.from_format(m_contents, m_format))

        return Workflow(fws, dict(links))