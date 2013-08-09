#!/usr/bin/env python

"""
This module aids in serializing and deserializing objects.

To serialize a FW object, refer to the documentation for the FWSerializable class. To de-serialize an object,
refer to the documentation for the FWSerializable class and load_object() method.
    - you can de-serialize explicitly, e.g. FWObject.from_dict() to enforce a FWObject instance as the result
    - you can de-serialize implicitly, e.g. load_object() to search for the correct Class dynamically

The implicit method is especially useful if you don't know in advance which subclass of a base class your \
serialization might point to. e.g. if you require some type of Quadrilateral, a serialization from your \
collaborator might point to a Square, Rhombus, or Rectangle, and you might not know which one in advance...

Some advantages:
    - Robust with regard to code refactorings even in implicit loading given certain reasonable guidelines on fw_name.
    - Simple to allow a superclass to define all the serializations for its subclasses, removing code repetition
    (in particular, note that from_dict is a class method rather than a static method, allowing use of self)
    - Decorators aid in some of the routine parts of the serialization, such as adding the _fw_name key
    - Both JSON and YAML file import/export are naturally and concisely supported within the framework.
    - Auto-detect and proper loading of JSON and YAML files
    - Proper JSON handling of datetime (both encoding and decoding) and UTF-8 strings
    - In some cases, objects can be serialized/deserialized extremely concisely, by use of only their fw_name (if no
    parameters are needed to describe the object)

A dict created using FWSerializer's to_dict() method should be readable by Pymatgen's PMGDecoder,
when the serialize_fw() decorator is used.
"""

import yaml
import pkgutil
import inspect
import json  # note that ujson is faster, but at this time does not support "default" in dumps()
import importlib
import datetime
from fireworks.core.fw_config import FWConfig

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 13, 2012'

SAVED_FW_MODULES = {}
DATETIME_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None


def _recursive_dict(obj):
    if obj is None:
        return None

    if hasattr(obj, 'to_dict'):
        return _recursive_dict(obj.to_dict())

    if isinstance(obj, dict):
        return {k: _recursive_dict(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_recursive_dict(v) for v in obj]

    if isinstance(obj, int) or isinstance(obj, float):
        return obj

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if isinstance(obj, unicode) and obj != obj.encode('ascii', 'ignore'):
        return obj

    return str(obj)


# TODO: is reconstitute_dates really needed? Can this method just do everything?
def _recursive_load(obj):
    if obj is None:
        return None

    if isinstance(obj, dict):
        if '_fw_name' in obj:
            return load_object(obj)
        return {k: _recursive_load(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_recursive_load(v) for v in obj]

    if isinstance(obj, basestring):
        try:
            # convert String to datetime if really datetime
            return datetime.datetime.strptime(obj, "%Y-%m-%dT%H:%M:%S.%f")
        except:
            # convert unicode to ASCII if not really unicode
            if obj == obj.encode('ascii', 'ignore'):
                return str(obj)

    return obj


def recursive_serialize(func):
    """
    a decorator to add FW serializations keys
    see documentation of FWSerializable for more details
    """

    def _decorator(self, *args, **kwargs):
        m_dict = func(self, *args, **kwargs)
        m_dict = _recursive_dict(m_dict)
        return m_dict

    return _decorator


def recursive_deserialize(func):
    """
    a decorator to add FW serializations keys
    see documentation of FWSerializable for more details
    """

    def _decorator(self, *args, **kwargs):
        new_args = [a for a in args]
        new_args[0] = {k: _recursive_load(v) for k, v in args[0].items()}
        m_dict = func(self, *new_args, **kwargs)
        return m_dict

    return _decorator


def serialize_fw(func):
    """
    a decorator to add FW serializations keys
    see documentation of FWSerializable for more details
    """

    def _decorator(self, *args, **kwargs):
        m_dict = func(self, *args, **kwargs)
        m_dict['_fw_name'] = self.fw_name
        return m_dict

    return _decorator


class FWSerializable():
    """
    To create a serializable object within FireWorks, you should subclass this class and implement
    the to_dict() and from_dict() methods.
    
    If you want the load_object() implicit de-serialization to work, you must also:
        - Use the @serialize_fw decorator on to_dict()
        - Override the _fw_name parameter with a unique key.
    
    See documentation of load_object() for more details.
    
    The use of @classmethod for from_dict allows you to define a superclass 
    that implements the to_dict() and from_dict() for all its subclasses.
    
    For an example of serialization, see the class QueueAdapterBase.
    """

    @property
    def fw_name(self):
        try:
            return self._fw_name
        except AttributeError:
            return self.__class__.__name__

    def to_dict(self):
        raise NotImplementedError('FWSerializable object did not implement to_dict()!')

    def to_db_dict(self):
        return self.to_dict()

    @classmethod
    def from_dict(cls, m_dict):
        raise NotImplementedError('FWSerializable object did not implement from_dict()!')

    def to_format(self, f_format='json', **kwargs):
        """
        returns a String representation in the given format
        :param f_format: the format to output to (default json)
        """
        if f_format == 'json':
            return json.dumps(self.to_dict(), default=DATETIME_HANDLER, **kwargs)
        elif f_format == 'yaml':
            # start with the JSON format, and convert to YAML
            return yaml.dump(self.to_dict(), default_flow_style=FWConfig().YAML_STYLE,
                             allow_unicode=True)
        else:
            raise ValueError('Unsupported format {}'.format(f_format))

    @classmethod
    def from_format(cls, f_str, f_format='json'):
        """
        convert from a String representation to its Object
        :param f_str: the String representation
        :param f_format: serialization format of the String (default json)
        """
        if f_format == 'json':
            return cls.from_dict(_reconstitute_dates(json.loads(f_str)))
        elif f_format == 'yaml':
            return cls.from_dict(_reconstitute_dates(yaml.load(f_str)))
        else:
            raise ValueError('Unsupported format {}'.format(f_format))

    def to_file(self, filename, f_format=None, **kwargs):
        """
        Write a serialization of this object to a file
        :param filename: filename to write to
        :param f_format: serialization format, default checks the filename extension
        """
        if f_format is None:
            f_format = filename.split('.')[-1]
        with open(filename, 'w') as f:
            f.write(self.to_format(f_format=f_format, **kwargs))

    @classmethod
    def from_file(cls, filename, f_format=None):
        """
        Load a serialization of this object from a file
        :param filename: filename to read
        :param f_format: serialization format, default checks the filename extension
        """
        if f_format is None:
            f_format = filename.split('.')[-1]
        with open(filename, 'r') as f:
            return cls.from_format(f.read(), f_format=f_format)


# TODO: make this quicker the first time around
def load_object(obj_dict):
    """
    Creates an instantiation of a class based on a dictionary representation. We implicitly
    determine the Class through introspection along with information in the dictionary.
    
    We search for a class with the _fw_name property equal to obj_dict['_fw_name']
    If the @module key is set, that module is checked first for a matching class
    to improve speed of lookup.
    Afterwards, the modules in the USER_PACKAGES global parameter are checked.
    
    Refactoring class names, module names, etc. will not break object loading
    as long as:
    
    i) the _fw_name property is maintained the same AND
    ii) the refactored module is kept within USER_PACKAGES
    
    You can get around these limitations if you really want:
    i) If you want to change the fw_name of an object you can set the FW_NAME_UPDATES key
    ii) If you want to put a refactored module in a new place add an entry to USER_PACKAGES

    :param obj_dict: the dict representation of the class
    """

    # override the name in the obj_dict if there's an entry in FW_NAME_UPDATES
    fw_name = FWConfig().FW_NAME_UPDATES.get(obj_dict['_fw_name'], obj_dict['_fw_name'])
    obj_dict['_fw_name'] = fw_name

    # first try to load from known location
    if fw_name in SAVED_FW_MODULES:
        m_module = importlib.import_module(SAVED_FW_MODULES[fw_name])
        m_object = _search_module_for_obj(m_module, obj_dict)
        if m_object:
            return m_object

    # failing that, look for the object within all of USER_PACKAGES
    # this will be slow, but only needed the first time

    found_objects = [] # used to make sure we don't find multiple hits
    for package in FWConfig().USER_PACKAGES:
        root_module = importlib.import_module(package)
        for loader, module_name, is_pkg in pkgutil.walk_packages(root_module.__path__,
                                                                 package + '.'):
            m_module = loader.find_module(module_name).load_module(module_name)
            m_object = _search_module_for_obj(m_module, obj_dict)
            if m_object:
                found_objects.append((m_object, module_name))

    if len(found_objects) == 1:
        SAVED_FW_MODULES[fw_name] = found_objects[0][1]
        return found_objects[0][0]
    elif len(found_objects) > 0:
        raise ValueError(
            'load_object() found multiple objects with cls._fw_name {} -- {}'.format(fw_name,
                                                                                     found_objects))

    raise ValueError('load_object() could not find a class with cls._fw_name {}'.format(fw_name))


def load_object_from_file(filename, f_format=None):
    """
    implicitly load an object from a file. just a friendly wrapper to load_object()
    
    :param filename: the filename to load an object from
    :param f_format: the serialization format (default is auto-detect based on filename extension)
    """

    m_dict = {}
    if f_format is None:
        f_format = filename.split('.')[-1]

    with open(filename, 'r') as f:
        if f_format == 'json':
            m_dict = _reconstitute_dates(json.loads(f.read()))
        elif f_format == 'yaml':
            m_dict = _reconstitute_dates(yaml.load(f.read()))
        else:
            raise ValueError('Unknown file format {} cannot be loaded!'.format(f_format))

    return load_object(m_dict)


def _search_module_for_obj(m_module, obj_dict):
    """
    internal method that looks in a module for a class with a given _fw_name
    """
    obj_name = obj_dict['_fw_name']

    for name, obj in inspect.getmembers(m_module):
        # check if the member is a Class matching our description
        if inspect.isclass(obj) and obj.__module__ == m_module.__name__ and \
                        getattr(obj, '_fw_name', None) == obj_name:
            return obj.from_dict(obj_dict)


def _reconstitute_dates(obj_dict):
    if obj_dict is None:
        return None

    if isinstance(obj_dict, dict):
        return {k: _reconstitute_dates(v) for k, v in obj_dict.items()}

    if isinstance(obj_dict, list):
        return [_reconstitute_dates(v) for v in obj_dict]

    if isinstance(obj_dict, basestring):
        try:
            return datetime.datetime.strptime(obj_dict, "%Y-%m-%dT%H:%M:%S.%f")
        except:
            pass

    return obj_dict
