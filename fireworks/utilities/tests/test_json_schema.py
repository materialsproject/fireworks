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
from fireworks.utilities import json_schema
from fireworks.utilities.json_schema import FW_SCHEMA_DIR
from fireworks.utilities.fw_serializers import load_object_from_file

class JSONSchemaTest(unittest.TestCase):
    """ validate the FireWorks JSON schema """

    def test_validate_schema(self):
        """ validate the schema against the metaschema """
        schemas = [
            'addfilestask.json',
            'archivedirtask.json',
            'backgroundtask.json',
            'commandlinetask.json',
            'commonadapter.json',
            'compressdirtask.json',
            'deletefilestask.json',
            'dupefinder.json',
            'filedeletetask.json',
            'filetransfertask.json',
            'filewritetask.json',
            'firetask.json',
            'firework.json',
            'foreachtask.json',
            'fwaction.json',
            'fwconfig.json',
            'fworker.json',
            'generic.json',
            'getfilestask.json',
            'importdatatask.json',
            'joindicttask.json',
            'joinlisttask.json',
            'launch.json',
            'launchpad.json',
            'links.json',
            'pytask.json',
            'scripttask.json',
            'spec.json',
            'templatewritertask.json',
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

class JSONSchemaValidatorTest(unittest.TestCase):
    """ test the FireWorks schema validator using sample documents """

    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'schema_samples')

    # skip due to runtime errors after validation (with status Error)
    skip_list = [
        'customtask.json',
        'lambda_task.json',
        'launchpad_ssl_x509.json',
        'launchpad_ssl.json',
        'file_transfer_task_2.json',
        'file_transfer_task.json',
        'filetransfertask1.json'
    ]

    def test_validate(self):
        """ validate a set of samples against the schema directly """
        schemas = ['Firetask', 'Firework', 'Workflow', 'LaunchPad', 'FWorker',
                   'CommonAdapter']
        for schema in schemas:
            path = os.path.join(self.samples_dir, schema.lower())
            for wf_file in os.listdir(path):
                with open(os.path.join(path, wf_file), 'r') as fileh:
                    try:
                        json_schema.validate(json.load(fileh), schema)
                    except ValidationError as err:
                        self.fail('Validation error: '+err.message)

    def test_validate_invalid(self):
        """ validate a set of invalid workflow samples against the schema """
        path = os.path.join(self.samples_dir, 'workflow-invalid')
        for wf_file in os.listdir(path):
            with open(os.path.join(path, wf_file), 'r') as fileh:
                inst = json.load(fileh)
                with self.assertRaises(ValidationError):
                    json_schema.validate(inst, 'Workflow')

    def test_validate_load_object_from_file(self):
        """ test the validator in load_object_from_file() """
        schemas = ['Firetask', 'CommonAdapter']
        for schema in schemas:
            path = os.path.join(self.samples_dir, schema.lower())
            for sfile in os.listdir(path):
                if sfile in self.skip_list:
                    continue
                try:
                    load_object_from_file(os.path.join(path, sfile))
                except ValidationError as err:
                    self.fail('Validation error: '+err.message)

    def _validate_from_dict(self, module, classname):
        """ validate a set of samples against the schema via from_dict() """
        cls = getattr(sys.modules[module], classname)
        path = os.path.join(self.samples_dir, classname.lower())
        for sfile in os.listdir(path):
            if sfile in self.skip_list:
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
            if sfile in self.skip_list:
                continue
            cls = getattr(sys.modules[module], classname)
            try:
                cls.from_file(os.path.join(path, sfile))
            except ValidationError as err:
                self.fail('Validation error: '+err.message)

    def test_qadapter_from_dict(self):
        """ validate CommonAdapter schema from dict """
        modulename = 'fireworks.user_objects.queue_adapters.common_adapter'
        self._validate_from_dict(modulename, 'CommonAdapter')

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
        modulename = 'fireworks.user_objects.queue_adapters.common_adapter'
        self._validate_from_file(modulename, 'CommonAdapter')

    def test_lpad_from_file(self):
        """ validate LaunchPad schema from file """
        self._validate_from_file('fireworks', 'LaunchPad')


if __name__ == '__main__':
    unittest.main()
