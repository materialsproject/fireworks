from StringIO import StringIO
from collections import defaultdict
import tarfile
from fireworks.core.firework import FireWork
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 27, 2013'


class Workflow(FWSerializable):
    # TODO: if performance of child_parents is an issue, override delitem/setitem to ensure it's always updated
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

        self.links = Workflow.Links(links_dict)

        # sanity: make sure the set of nodes from the links_dict is equal to the set of nodes from id_fw
        if set(self.links.nodes) != set(self.id_fw.keys()):
            raise ValueError("Specified links don't match given FW")

        self.metadata = metadata

    def apply_action(self, action):
        return []

    def refresh(self):
        return {}

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
        return {'links': self.links.to_db_dict(), 'metadata': self.metadata}

    @classmethod
    def from_dict(cls, m_dict):
        return Workflow([FireWork.from_dict(f) for f in m_dict['fws']], Workflow.Links.from_dict(m_dict['links']))

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


        """
        def _refresh_fw(self, fw_id, parent_ids):
            # if we are defused, just skip this whole thing
        if self._get_fw_state(fw_id) == 'DEFUSED':
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
            launches = self.get_launches(fw_id)
            max_score = 0
            m_state = 'READY'

            for l in launches:
                if LAUNCH_RANKS[l.state] > max_score:
                    max_score = LAUNCH_RANKS[l.state]
                    m_state = l.state

        self._update_fw_state(fw_id, m_state)
        """
        """
        # get the wf_dict
        wfc = WFConnections.from_dict(self.links.find_one({'nodes': m_fw.fw_id}))
        # get all the children
        child_fw_ids = wfc.children_links[m_fw.fw_id]

        # depending on the decision, you might have to do additional actions
        if fw_decision.action in ['CONTINUE', 'BREAK']:
            pass
        elif fw_decision.action == 'DEFUSE':
            # mark all children as defused
            for cfid in child_fw_ids:
                self._update_fw_state(cfid, 'DEFUSED')

        elif fw_decision.action == 'MODIFY':
            for cfid in child_fw_ids:
                self._update_fw_spec(cfid, fw_decision.mod_spec['dict_mods'])

        elif fw_decision.action == 'DETOUR':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'ADD':
            old_new = self._insert_fws(fw_decision.mod_spec['add_fws'])
            self._insert_children(m_fw.fw_id, old_new.values())
        elif fw_decision.action == 'ADDIFY':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        elif fw_decision.action == 'PHOENIX':
            # TODO: implement
            raise NotImplementedError('{} action not implemented yet'.format(fw_decision.action))
        """