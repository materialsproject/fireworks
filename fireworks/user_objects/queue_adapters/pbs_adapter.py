#!/usr/bin/env python

import os
from fireworks.queue.queue_adapter import QueueAdapterBase

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

    def parse_jobid(self, output_str):
        # output should of the form '2561553.sdb' or '352353.jessup' - just grab the first part for job id
        return int(output_str.split('.')[0])

    def get_status_cmd(self, username):
        return ['qstat', '-a', '-u', username]

    def parse_njobs(self, output_str, username):
        # lines should have this form
        # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
        # count lines that include the username in it
        # TODO: only count running or queued jobs. or rather, *don't* count jobs that are 'C'.
        outs = output_str.split('\n')
        return len([line.split() for line in outs if username in line])