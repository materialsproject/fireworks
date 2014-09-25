# coding: utf-8

from __future__ import unicode_literals

"""
This module contains the TemplateWriterTask, which writes files based on a template file and a Context using Jinja2's templating engine.
"""

import os
from jinja2 import Template
from fireworks.core.firework import FireTaskBase
from fireworks.fw_config import TEMPLATE_DIR

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 08, 2013'


class TemplateWriterTask(FireTaskBase):
    """
    Task to write templated files via Jinja2 library
    Required parameters:
        - template_file: (str) - path to template file
        - context: (dict) - variable replacements for the template file
        - output_file: (str) - output file
    Optional parameters:
        - append: (bool) - append to output file (instead of overwrite)
        - template_dir: (str) - directory in which to find the template file
    """
    _fw_name = 'TemplateWriterTask'

    def run_task(self, fw_spec):
        if self.get("use_global_spec"):
            self._load_params(fw_spec)
        else:
            self._load_params(self)

        with open(self.template_file) as f:
            t = Template(f.read())
            output = t.render(self.context)

            write_mode = 'w+' if self.append_file else 'w'
            with open(self.output_file, write_mode) as of:
                of.write(output)

    def _load_params(self, d):

        self.context = d['context']
        self.output_file = d['output_file']
        self.append_file = d.get('append')  # append to output file?

        if d.get('template_dir'):
            self.template_dir = d['template_dir']
        elif TEMPLATE_DIR:
            self.template_dir = TEMPLATE_DIR
        else:
            MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
            self.template_dir = os.path.join(MODULE_DIR, 'templates')

        self.template_file = os.path.join(self.template_dir, d['template_file'])
        if not os.path.exists(self.template_file):
            raise ValueError("TemplateWriterTask could not find a template file at: {}".format(self.template_file))
