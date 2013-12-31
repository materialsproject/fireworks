#!/usr/bin/env python

import os
from fireworks.queue.queue_adapter import QueueAdapterBase
from fireworks.utilities.fw_serializers import serialize_fw

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class PBSAdapterNERSC(QueueAdapterBase):
    """
    A PBS adapter that works on NERSC (Hopper, Carver)
    """
    _fw_name = 'PBSAdapter (NERSC)'
    template_file = os.path.join(os.path.dirname(__file__), 'PBS_template.txt')
    submit_cmd = 'qsub'
    q_name = 'pbs'
    defaults = {}

    def _parse_jobid(self, output_str):
        # output should of the form '2561553.sdb' or '352353.jessup' - just grab the first part for job id
        return int(output_str.split('.')[0])

    def _get_status_cmd(self, username):
        return ['qstat', '-a', '-u', username]

    def _parse_njobs(self, output_str, username):
        # lines should have this form
        # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
        # count lines that include the username in it
        # TODO: only count running or queued jobs. or rather, *don't* count jobs that are 'C'.
        outs = output_str.split('\n')
        return len([line.split() for line in outs if username in line])


class PBSAdapter(QueueAdapterBase):
    """
    A PBS adapter that works on NERSC (Hopper, Carver)
    """
    _fw_name = 'PBSAdapter'
    submit_cmd = 'qsub'
    defaults = {}
    default_template_file = os.path.join(os.path.dirname(__file__), 'PBS_template.txt')

    def __init__(self, q_name, template_file=None, **kwargs):
        """
        :param q_name
        :param template_file
        """
        self.template_file = os.path.abspath(template_file) \
            if template_file is not None \
            else PBSAdapter.default_template_file
        self.q_name = q_name
        self.update(dict(kwargs))

    def _parse_jobid(self, output_str):
        # output should of the form '2561553.sdb' or '352353.jessup' - just grab the first part for job id
        return int(output_str.split('.')[0])

    def _get_status_cmd(self, username):
        return ['qstat', '-a', '-u', username]

    def _parse_njobs(self, output_str, username):
        # lines should have this form
        # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
        # count lines that include the username in it
        outs = output_str.split('\n')
        return len([1 for line in outs
                    if username in line and line.split()[-2] != "C"])

    @serialize_fw
    def to_dict(self):
        d = dict(self)
        #_fw names are used for the specific instance variables.
        d["_fw_q_name"] = self.q_name
        # Use None is it is the default template. This keeps the serialized
        # dict simple and also makes it more portable across multiple
        # installations if a template file was not actually specified.
        d["_fw_template_file"] = self.template_file if self\
            .template_file != PBSAdapter.default_template_file else None
        return d

    @classmethod
    def from_dict(cls, m_dict):
        return cls(
            q_name=m_dict["_fw_q_name"],
            template_file=m_dict["_fw_template_file"],
            **{k: v for k, v in m_dict.items() if not k.startswith("_fw")})