""" Unit tests for FireWorks JSON schema """

__author__ = 'Ivan Kondov'
__copyright__ = 'Copyright 2020, Karlsruhe Institute of Technology'
__email__ = 'ivan.kondov@kit.edu'

import os
import sys
import unittest
import json
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import SchemaError
from jsonschema import Draft7Validator
import fireworks
import fireworks.user_objects.queue_adapters.common_adapter
from fireworks.utilities.json_schema import resolve_validate
from fireworks.utilities.json_schema import FW_SCHEMA_DIR

class JSONSchemaTest(unittest.TestCase):
    """ run tests for DAGFlow class """

    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'schema_samples')

    # skip reasons:
    # 1) deserialization before validation (with status Fail)
    # 2) runtime errors after validation (with status Error)
    skip_list_1 = [
      'dupefinder_1.json', # Validation error: {"_fw_name": "DupeFinderExact"} is not of type 'object'
      'dupefinder_2.json', # Validation error: {"_fw_name": "DupeFinderExact"} is not of type 'object'
      'background_task.json', # Validation error: {"tasks": [{"_fw_name": "ScriptTask", "script": ["echo \"hello from BACKGROUND thread"], "use_shell": true}], "num_launches": 0, "sleep_time": 10, "run_on_finish": false, "_fw_name": "BackgroundTask"} is not of type 'object'
    ]

    skip_list_2 = [
      'customtask.json', # ModuleNotFoundError: No module named 'fw_custom_tasks'
      'lambda_task.json', # ValueError: load_object() could not find a class with cls._fw_name LambdaTask
      'launchpad_ssl_x509.json', # FileNotFoundError: [Errno 2] No such file or directory: '/path/to/cacert.pem'
      'launchpad_ssl.json', # FileNotFoundError: [Errno 2] No such file or directory: '/path/to/cacert.pem'
      'file_transfer_task_2.json', # Required parameter dest not specified! the example from https://materialsproject.github.io/fireworks/fileiotasks.html does not work
      'file_transfer_task.json' # Required parameter dest not specified! the example from https://materialsproject.github.io/fireworks/fileiotasks.html does not work
    ]

    def test_validate_schema(self):
        """ validate the schema against the metaschema """
        schemas = [
            'backgroundtask.json',
            'commonadapter.json',
            'dupefinder.json',
            'firetask.json',
            'firework.json',
            'firework_workflow.json',
            'fwaction.json',
            'fwconfig.json',
            'fworker.json',
            'generic.json',
            'launch.json',
            'launchpad.json',
            'links.json',
            'spec.json',
            'tracker.json',
            'workflow.json'
        ]
        for schema in schemas:
            with open(os.path.join(FW_SCHEMA_DIR, schema), 'r') as fileh:
                schema_dict = json.load(fileh)
            try:
                Draft7Validator.check_schema(schema_dict)
            except SchemaError as err:
                self.fail('Schema validation error: '+err.message)

    def test_validate(self):
        """ validate a set of samples against the schema directly """
        schemas = ['Firework', 'Workflow', 'LaunchPad', 'FWorker', 'CommonAdapter']
        for schema in schemas:
            path = os.path.join(self.samples_dir, schema.lower())
            for wf_file in os.listdir(path):
                with open(os.path.join(path, wf_file), 'r') as fileh:
                    try:
                        resolve_validate(json.load(fileh), schema)
                    except ValidationError as err:
                        self.fail('Validation error: '+err.message)

    def test_validate_invalid(self):
        """ validate a set of invalid workflow samples against the schema """
        path = os.path.join(self.samples_dir, 'workflow-invalid')
        for wf_file in os.listdir(path):
            with open(os.path.join(path, wf_file), 'r') as fileh:
                inst = json.load(fileh)
                with self.assertRaises(ValidationError):
                    resolve_validate(inst, 'Workflow')

    def _validate_from_dict(self, module, classname):
        """ validate a set of samples against the schema via from_dict() """
        cls = getattr(sys.modules[module], classname)
        path = os.path.join(self.samples_dir, classname.lower())
        for sfile in os.listdir(path):
            if sfile in self.skip_list_1+self.skip_list_2:
                continue
            with open(os.path.join(path, sfile), 'r') as fileh:
                inst_dict = json.load(fileh)
                try:
                    cls.from_dict(inst_dict)
                except ValidationError as err:
                    self.fail('Validation error: '+err.message)

    def _validate_from_file(self, module, classname):
        """ validate a set of samples against the schema via from_file() """
        cls = getattr(sys.modules[module], classname)
        path = os.path.join(self.samples_dir, classname.lower())
        for sfile in os.listdir(path):
            if sfile in self.skip_list_1+self.skip_list_2:
                continue
            cls = getattr(sys.modules[module], classname)
            try:
                cls.from_file(os.path.join(path, sfile))
            except ValidationError as err:
                self.fail('Validation error: '+err.message)

    def test_workflow_from_dict(self):
        """ validate Workflow schema from dict """
        self._validate_from_dict('fireworks', 'Workflow')

    def test_firework_from_dict(self):
        """ validate Firework schema from dict """
        self._validate_from_dict('fireworks', 'Firework')

    def test_fworker_from_dict(self):
        """ validate FWorker schema from dict """
        self._validate_from_dict('fireworks', 'FWorker')

    def test_qadapter_from_dict(self):
        """ validate CommonAdapter schema from dict """
        self._validate_from_dict('fireworks.user_objects.queue_adapters.common_adapter', 'CommonAdapter')

    def test_lpad_from_dict(self):
        """ validate LaunchPad schema from dict """
        self._validate_from_dict('fireworks', 'LaunchPad')

    def test_workflow_from_file(self):
        """ validate Workflow schema from file """
        self._validate_from_file('fireworks', 'Workflow')

    def test_firework_from_file(self):
        """ validate Firework schema from file """
        self._validate_from_file('fireworks', 'Firework')

    def test_fworker_from_file(self):
        """ validate FWorker schema from file """
        self._validate_from_file('fireworks', 'FWorker')

    def test_qadapter_from_file(self):
        """ validate CommonAdapter schema from file """
        self._validate_from_file('fireworks.user_objects.queue_adapters.common_adapter', 'CommonAdapter')

    def test_lpad_from_file(self):
        """ validate LaunchPad schema from file """
        self._validate_from_file('fireworks', 'LaunchPad')


if __name__ == '__main__':
    unittest.main()
