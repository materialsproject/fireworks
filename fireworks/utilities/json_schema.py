""" JSON schema validator for FireWorks working with relative paths """

__author__ = 'Ivan Kondov'
__copyright__ = 'Copyright 2020, Karlsruhe Institute of Technology'
__email__ = 'ivan.kondov@kit.edu'

import os
import json
from pathlib import Path
import jsonschema

FW_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW_SCHEMA_DIR = os.path.join(FW_ROOT_DIR, 'schema')


def resolve_validate(instance, schema_name):
    """ JSON schema validator working with relative paths """
    schema_file = schema_name.lower() + '.json'
    schema_path = os.path.join(FW_SCHEMA_DIR, schema_file)
    with open(schema_path, 'rt') as fileh:
        schema_dict = json.load(fileh)
    base_uri = Path(os.path.abspath(schema_path)).as_uri()
    custom_res = jsonschema.RefResolver(base_uri, schema_dict)
    jsonschema.validate(instance, schema_dict, resolver=custom_res,
                        format_checker=jsonschema.FormatChecker())
