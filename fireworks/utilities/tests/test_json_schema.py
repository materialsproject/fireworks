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

    def test_validate_schema(self):
        """ validate the schema against the metaschema """
        schemas = [
            'backgroundtask.json',
            'commonadapter.json',
            'firetask.json',
            'fwconfig.json',
            'launch.json',
            'dupefinder.json',
            'firework.json',
            'fworker.json',
            'launchpad.json',
            'tracker.json',
            'fwaction.json',
            'generic.json',
            'links.json',
            'spec.json',
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

    def test_validate_from_file(self):
        """ validate a set of samples against the schema via from_file() """
        # currently the time stamps in Workflow, Firework do not validate due to
        # inteference of reconstitute_dates() in the fw_serializers module;
        # LaunchPad does not validate due to invalid path in samples (should not
        # be valid for testing)

        schemas = ['FWorker', 'CommonAdapter']
        modules = ['fireworks', 'fireworks.user_objects.queue_adapters.common_adapter']
        for schema, module in zip(schemas, modules):
            path = os.path.join(self.samples_dir, schema.lower())
            for sfile in os.listdir(path):
                cls = getattr(sys.modules[module], schema)
                try:
                    cls.from_file(os.path.join(path, sfile))
                except ValidationError as err:
                    self.fail('Validation error: '+err.message)

    def test_validate_from_dict(self):
        """ validate a set of samples against the schema via from_dict() """
        # currently the time stamps in Workflow, Firework do not validate due to
        # inteference of reconstitute_dates() in the fw_serializers module;
        # LaunchPad does not validate due to invalid path in samples (should not
        # be valid for testing) """

#        schemas = ['Workflow', 'Firework', 'FWorker', 'CommonAdapter']
#        modules = ['fireworks', 'fireworks.user_objects.queue_adapters.common_adapter']
        schemas = ['FWorker', 'CommonAdapter']
        modules = ['fireworks', 'fireworks.user_objects.queue_adapters.common_adapter']
        for schema, module in zip(schemas, modules):
            path = os.path.join(self.samples_dir, schema.lower())
            for sfile in os.listdir(path):
                cls = getattr(sys.modules[module], schema)
                with open(os.path.join(path, sfile), 'r') as fileh:
                    inst_dict = json.load(fileh)
                    try:
                        cls.from_dict(inst_dict)
                    except ValidationError as err:
                        self.fail('Validation error: '+err.message)

if __name__ == '__main__':
    unittest.main()
