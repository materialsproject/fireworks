#!/usr/bin/env python

import os
from fireworks.queue.queue_adapter import QueueAdapterBase

__author__ = 'David Waroquiers, Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'David Waroquiers'
__email__ = 'david.waroquiers@uclouvain.be'
__date__ = 'Dec 12, 2012'


class SLURMAdapterUCL(QueueAdapterBase):
    """
    A SLURM adapter that works on UCL machines
    """
    _fw_name = 'SLURMAdapter (UCL)'
    template_file = os.path.join(os.path.dirname(__file__), 'SLURM_template.txt')
    submit_cmd = 'sbatch'
    q_name = 'slurm'
    defaults = {'ntasks': 1, 'cpus_per_task': 1}

    def parse_jobid(self, output_str):
        return int(output_str.split()[3])

    def get_status_cmd(self, username):
        return ['squeue', '-o "%u"', '-u', username]

    def parse_njobs(self, output_str, username):
        # lines should have this form
        # username
        # count lines that include the username in it
        outs = output_str.split('\n')
        return len([line.split() for line in outs if username in line])