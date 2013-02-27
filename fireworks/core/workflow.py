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
                      'parent_links': dict([(str(k), v) for (k, v) in self.parent_links.iteritems()]),
                      'nodes': self.nodes}
            return m_dict

        @classmethod
        def from_dict(cls, m_dict):
            m_dict = dict([(int(k), list(v)) for (k, v) in m_dict.iteritems()])
            return Workflow.WFLinks(m_dict)

    def __init__(self, fireworks, wflinks_dict=None, metadata={}):

        """
        :param fireworks: a list of FireWork objects
        :param wflinks_dict: A dict representing workflow links
        :param metadata: metadata for this Workflow
        """

        wflinks_dict = wflinks_dict if wflinks_dict else {}

        self.id_fws = {}  # main dict containing mapping of an id to a FireWork object
        for fw in fireworks:
            if fw.fw_id in self.id_fws:
                raise ValueError("FW ids must be unique!")
            self.id_fws[fw.fw_id] = fw
            if fw.fw_id not in wflinks_dict:
                wflinks_dict[fw.fw_id] = []

        self.wflinks = Workflow.WFLinks(wflinks_dict)
        self.metadata = metadata

    def _reassign_ids(self, old_new):
        # update id_fw
        new_id_fw = {}
        for (fwid, fws) in self.id_fws.iteritems():
            new_id_fw[old_new.get(fwid, fwid)] = fws
        self.id_fws = new_id_fw

        # update the WFLinks
        new_wfl = {}
        for (parent, children) in self.wflinks.iteritems():
            new_parent = old_new.get(parent, parent)
            new_wfl[new_parent] = [old_new.get(child, child) for child in children]
        self.wflinks = Workflow.WFLinks(new_wfl)

    def to_dict(self):
        return {'fws': [f.to_dict() for f in self.id_fws.iteritems()], 'wflinks': self.wflinks.to_dict()}

    @classmethod
    def from_dict(cls, m_dict):
        return Workflow([FireWork.from_dict(f) for f in m_dict['fws']], Workflow.WFLinks.from_dict(m_dict['wflinks']))

    @classmethod
    def from_FireWork(cls, fw):
        return Workflow([fw], None)

    #TODO: add .gz support
    def to_tarfile(self, f_name='fwf.tar', f_format='json'):
        try:
            out = tarfile.open(f_name, "w")

            # write out the wflinks
            wfl_str = self.wflinks.to_format(f_format)
            wfl_info = tarfile.TarInfo('wflinks.' + f_format)
            wfl_info.size = len(wfl_str)
            out.addfile(wfl_info, StringIO(wfl_str))

            # write out fws
            for fw in self.id_fws.itervalues():
                fw_str = fw.to_format(f_format)
                fw_info = tarfile.TarInfo('fw_{}.{}'.format(fw.fw_id, f_format))
                fw_info.size = len(fw_str)
                out.addfile(fw_info, StringIO(fw_str))

        finally:
            out.close()

    @classmethod
    def from_tarfile(cls, tar_filename):
        t = tarfile.open(tar_filename, 'r')
        wflinks = None
        fws = []
        for f_name in t.getnames():
            m_file = t.extractfile(f_name)
            m_format = m_file.name.split('.')[-1]
            m_contents = m_file.read()
            if 'wflinks' in f_name:
                wflinks = Workflow.WFLinks.from_format(m_contents, m_format)
            else:
                fws.append(FireWork.from_format(m_contents, m_format))

        return Workflow(fws, dict(wflinks))