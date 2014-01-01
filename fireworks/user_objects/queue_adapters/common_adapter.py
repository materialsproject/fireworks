#!/usr/bin/env python

"""
This module implements a CommonAdaptor that supports standard PBS and SGE
queues.
"""
import os
import re
from fireworks.queue.queue_adapter import QueueAdapterBase
from fireworks.utilities.fw_serializers import serialize_fw

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class CommonAdapter(QueueAdapterBase):
    """
    A PBS adapter that works on most PBS (including derivatives such as
    TORQUE) and SGE queues.
    """
    _fw_name = 'CommonAdapter'
    submit_cmd = 'qsub'
    defaults = {}
    default_template_file = os.path.join(os.path.dirname(__file__),
                                         '{}_template.txt')
    supported_q_types = ["PBS", "SGE"]

    def __init__(self, q_type, q_name, template_file=None, **kwargs):
        """
        :param q_type: The type of queue. Right now it should be either PBS
                       or SGE.
        :param q_name: A name for the queue. Can be any string.
        :param template_file: The path to the template file. Leave it as
                              None (the default) to use Fireworks' built-in
                              templates for PBS and SGE, which should work
                              on most queues.
        :param **kwargs: Series of keyword args for queue parameters.
        """
        if q_type not in CommonAdapter.supported_q_types:
            raise ValueError(
                "{} is not a supported queue type. "
                "CommonAdaptor supports {}".format(q_type,
                                                   CommonAdapter.supported_q_types))
        self.q_type = q_type
        self.template_file = os.path.abspath(template_file) \
            if template_file is not None \
            else CommonAdapter.default_template_file.format(self.q_type)
        self.q_name = q_name
        self.update(dict(kwargs))

    def _parse_jobid(self, output_str):
        #This should work regardless of PBS or SGE.
        #PBS returns somehting like 1234.whatever
        #SGE returns something like "Your job 44275 ("O3") has been submitted"
        #In both cases, the first series of integers is the jobid.
        m = re.search("(\d+)", output_str)
        if m:
            return m.group(1)
        raise RuntimeError("Unable to parse jobid")

    def _get_status_cmd(self, username):
        # Removed -a. Not sure why it was necessary since it seems to give
        # the same output. Simple -u works for both PBS and SGE.
        return ['qstat', '-u', username]

    def _parse_njobs(self, output_str, username):
        # lines should have this form
        # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
        # count lines that include the username in it
        count = 0
        for l in output_str.split('\n'):
            if l.lower().startswith("job"):
                header = l.split()
                if self.q_type == "PBS":
                    #PBS has a ridiculous two word "Job ID" in header
                    state_index = header.index("S") - 1
                    queue_index = header.index("Queue") - 1
                else:
                    state_index = header.index("state")
                    queue_index = header.index("queue")
            if username in l:
                toks = l.split()
                if toks[state_index] != "C" and self["queue"] in toks[queue_index]:
                    count += 1
        return count

    @serialize_fw
    def to_dict(self):
        d = dict(self)
        #_fw names are used for the specific instance variables.
        d["_fw_q_type"] = self.q_type
        d["_fw_q_name"] = self.q_name
        # Use None if it is the default template. This keeps the serialized
        # dict simple and also makes it more portable across multiple
        # installations if a template file was not actually specified.
        d["_fw_template_file"] = self.template_file if self\
            .template_file != CommonAdapter.default_template_file.format(self.q_type) else None
        return d

    @classmethod
    def from_dict(cls, m_dict):
        return cls(
            q_type=m_dict["_fw_q_type"],
            q_name=m_dict["_fw_q_name"],
            template_file=m_dict.get("_fw_template_file", None),
            **{k: v for k, v in m_dict.items() if not k.startswith("_fw")})