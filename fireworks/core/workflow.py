from collections import defaultdict
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 27, 2013'


class Workflow(FWSerializable):
    # TODO: if performance of child_parents is an issue, override the __delitem__ and __setitem__ of dict and make
    # sure it's always updated
    class WFLinks(dict, FWSerializable):

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
                      'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.iteritems()])}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            m_dict = dict([(int(k), list(v)) for (k, v) in m_dict.iteritems()])
            return Workflow.WFLinks(m_dict)


    # TODO: add methods for adding children, removing children

    def __init__(self, child_nodes_dict=None, metadata=None):

        child_nodes_dict = child_nodes_dict if child_nodes_dict else {}
        self._parent_links = defaultdict(list)
        self.children_links = defaultdict(set)
        self.metadata = metadata if metadata else {}

        for (parent, children) in child_nodes_dict.iteritems():
            # make sure children is a list
            if not isinstance(children, list):
                children = [children]

            # make sure parents and children are ints
            parent = int(parent)
            children = [int(c) for c in children]

            # add the children
            self.children_links[parent].update(children)

            # add the parents
            for child in children:
                self._parent_links[child].append(parent)

    def to_dict(self):
        m_dict = {'children_links': dict([(k, list(v)) for (k, v) in self.children_links.iteritems()])}
        if self.metadata:
            m_dict['metadata'] = self.metadata
        return m_dict

    def to_db_dict(self):
        m_dict = {'children_links': dict([(str(k), list(v)) for (k, v) in self.children_links.iteritems()])}
        m_dict['parent_links'] = dict([(str(k), v) for (k, v) in self._parent_links.iteritems()])
        m_dict['metadata'] = self.metadata
        return m_dict

    @classmethod
    def from_dict(cls, m_dict):
        metadata = m_dict.get('metadata', None)
        return WFConnections(m_dict['children_links'], metadata)

    def __init__(self, fireworks, wf_connections, metadata={}):

        """
        :param fireworks: a list of FireWork objects
        :param wf_connections: A WorkflowConnections object
        :param metadata: metadata for this Workflow
        """

        self.id_fw = {}
        self.nodes = set()

        # reset id_fw
        for fw in fireworks:
            if not fw.fw_id or fw.fw_id in self.id_fw:
                raise ValueError("FW ids must be well-defined and unique!")
                # note we have a String key, this matches the WFConnections format
            self.id_fw[fw.fw_id] = fw
            self.nodes.add(fw.fw_id)

        # TODO: validate that the connections is valid given the FW

        # (e.g., all the connection ids must be present in the list of FW)
        self.wf_connections = wf_connections if isinstance(wf_connections, WFConnections) else WFConnections(
            wf_connections)

        self.metadata = self.wf_connections.metadata
        self._fws = fireworks

    def _reassign_ids(self, old_new):
        # update the nodes
        new_nodes = [old_new.get(id, id) for id in self.nodes]
        self.nodes = new_nodes

        # update the WFConnections
        old_cl = self.wf_connections.children_links
        new_cl = {}
        for (parent, children) in old_cl.iteritems():
            # make sure children is a list
            children = list(children)

            new_parent = old_new.get(parent, parent)
            new_children = [old_new.get(child, child) for child in children]
            new_cl[new_parent] = new_children

        self.wf_connections = WFConnections(new_cl)

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self._fws], 'wf_connections': self.wf_connections.to_dict()}

    @classmethod
    def from_dict(cls, m_dict):
        return FWorkflow([FireWork.from_dict(f) for f in m_dict['fws']],
                         WFConnections.from_dict(m_dict['wf_connections']))

    def to_db_dict(self):
        m_dict = self.wf_connections.to_db_dict()
        m_dict['nodes'] = list(self.nodes)
        return m_dict

    #TODO: add .gz support
    def to_tarfile(self, f_name='fwf.tar', f_format='json'):
        try:
            out = tarfile.open(f_name, "w")

            # write out the wfconnections
            wfc_str = self.wf_connections.to_format(f_format)
            wfc_info = tarfile.TarInfo('wfconnections.' + f_format)
            wfc_info.size = len(wfc_str)
            out.addfile(wfc_info, StringIO(wfc_str))

            # write out fws
            for fw in self.id_fw.itervalues():
                fw_str = fw.to_format(f_format)
                fw_info = tarfile.TarInfo('fw_' + str(fw.fw_id) + '.' + f_format)
                fw_info.size = len(fw_str)
                out.addfile(fw_info, StringIO(fw_str))

        finally:
            out.close()

    @classmethod
    def from_tarfile(cls, tar_filename):
        t = tarfile.open(tar_filename, 'r')
        wf_connections = None
        fws = []
        for f_name in t.getnames():
            m_file = t.extractfile(f_name)
            m_format = m_file.name.split('.')[-1]
            m_contents = m_file.read()
            if 'wfconnections' in f_name:
                wf_connections = WFConnections.from_format(m_contents, m_format)
            else:
                fws.append(FireWork.from_format(m_contents, m_format))

        return FWorkflow(fws, wf_connections)

    @classmethod
    def from_FireWork(cls, fw):
        return FWorkflow([fw], None)

if __name__ == '__main__':
    a = Workflow.WFLinks({1: [2, 3]})
    print a.to_dict()
    print a.nodes
    print a.parent_links