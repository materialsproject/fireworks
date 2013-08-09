import os
from django.template import Template, Context
from fireworks.core.firework import FireTaskBase
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Aug 08, 2013'

# TODO: allow FWConfig() to set the template dir

# TODO: remove this hack...
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fireworks.base_site.settings")


class TemplateWriterTask(FireTaskBase, FWSerializable):
    _fw_name = "Template Writer Task"

    def __init__(self, parameters):
        self.update(parameters)

        self.context = self['context']
        self.output_file = self['output_file']
        self.append_file = self.get('append', False)  # append to output file?

        MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.template_dir = self.get('template_dir', os.path.join(MODULE_DIR, 'templates'))

        self.template_file = os.path.join(self.template_dir, self['template_file'])
        if not os.path.exists(self.template_file):
            raise ValueError("Template Writer Task could not find a template file at: {}".format(self.template_file))

    def run_task(self, fw_spec):
        with open(self.template_file) as f:
            t = Template(f.read())
            output = t.render(Context(self.context))

            write_mode = 'w+' if self.append_file else 'w'
            with open(self.output_file, write_mode) as of:
                of.write(output)