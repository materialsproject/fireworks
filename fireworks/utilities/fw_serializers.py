#!/usr/bin/env python

'''
This module aids in serializing and deserializing objects.

To serialize a FW object, refer to the documentation for the FWSerializable class. \
To de-serialize an object, refer to the documentation for the FWSerializable class and load_object() method.
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
    - In some cases, objects can be serialized/deserialized extremely concisely, by knowledge of only their fw_name

A dict created using FWSerializer's to_dict() method should be readable by Pymatgen's PMGDecoder, when the \
serialize_fw() decorator is used.
'''

import yaml
from fireworks.core.fw_constants import YAML_STYLE, USER_PACKAGES,\
    FW_NAME_UPDATES
import pkgutil
import inspect
import simplejson as json  # note that ujson is faster, but at this time does not support "default" in dumps()
import importlib
import datetime

# TODO: remember the module and class of objects so you don't need to search through all the user packages
# every single time...


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 13, 2012'


def serialize_fw(func):
    '''
    a decorator to add FW serializations keys
    see documentation of FWSerializable for more details
    '''
    def _decorator(self, *args, **kwargs):
        m_dict = func(self, *args, **kwargs)
        m_dict['_fw_name'] = self.fw_name
        m_dict['@module'] = self.__class__.__module__
        m_dict['@class'] = self.__class__.__name__
        
        return m_dict
    return _decorator


class FWSerializable():
    '''
    To create a serializable object within FireWorks, you should subclass this class and implement
    the to_dict() and from_dict() methods.
    
    If you want the load_object() implicit de-serialization to work, you must also:
        - Use the @serialize_fw decorator on to_dict()
        - Override the _fw_name parameter with a unique key.
    
    See documentation of load_object() for more details.
    
    The use of @classmethod for from_dict allows you to define a superclass 
    that implements the to_dict() and from_dict() for all its subclasses.
    
    For an example of serialization, see the class QueueAdapterBase.
    '''
    
    @property
    def fw_name(self):
        try:
            return self._fw_name
        except AttributeError:
            return self.__class__.__name__
    
    @classmethod
    def to_dict(self):
        raise NotImplementedError('FWSerializable object did not implement to_dict()!')

    @classmethod
    def from_dict(self, m_dict):
        raise NotImplementedError('FWSerializable object did not implement from_dict()!')
    
    def to_format(self, f_format='json'):
        '''
        returns a String representation in the given format
        :param f_format: the format to output to (default json)
        '''
        if f_format == 'json':
            dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
            return json.dumps(self.to_dict(), default=dthandler)
        elif f_format == 'yaml':
            # start with the JSON format, and convert to YAML
            return yaml.dump(self.to_dict(), default_flow_style=YAML_STYLE, allow_unicode=True)
        else:
            raise ValueError('Unsupported format {}'.format(f_format))
    
    @classmethod
    def from_format(self, f_str, f_format='json'):
        '''
        convert from a String representation to its Object
        :param f_str: the String representation
        :param f_format: serialization format of the String (default json)
        '''
        if f_format == 'json':
            return self.from_dict(_reconstitute_dates(json.loads(f_str)))
        elif f_format == 'yaml':
            return self.from_dict(_reconstitute_dates(yaml.load(f_str)))
        else:
            raise ValueError('Unsupported format {}'.format(f_format))

    def to_file(self, filename, f_format='AUTO_DETECT'):
        '''
        Write a serialization of this object to a file
        :param filename: filename to write to
        :param f_format: serialization format, default checks the filename extension
        '''
        if f_format == 'AUTO_DETECT':
            f_format = filename.split('.')[-1]
        with open(filename, 'w') as f:
            f.write(self.to_format(f_format=f_format))
        
    @classmethod
    def from_file(self, filename, f_format='AUTO_DETECT'):
        '''
        Load a serialization of this object from a file
        :param filename: filename to read
        :param f_format: serialization format, default checks the filename extension
        '''
        if f_format == 'AUTO_DETECT':
            f_format = filename.split('.')[-1]
        with open(filename, 'r') as f:
            return self.from_format(f.read(), f_format=f_format)


def load_object(obj_dict):
    '''
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
    '''

    # override the name in the obj_dict if there's an entry in FW_NAME_UPDATES
    fw_name = obj_dict['_fw_name']
    fw_name = FW_NAME_UPDATES.get(fw_name, fw_name)
    obj_dict['_fw_name'] = fw_name
    
    # first try to load from the serialized module name
    if obj_dict.get('@module', None):
        m_module = importlib.import_module(obj_dict['@module'])
        m_object = _search_module_for_obj(m_module, obj_dict)
        if m_object:
            return m_object
    
    # failing that, look for the object within all of USER_PACKAGES
    for package in USER_PACKAGES:
        root_module = importlib.import_module(package)
        for loader, module_name, is_pkg in pkgutil.walk_packages(root_module.__path__, package + '.'):
            m_module = loader.find_module(module_name).load_module(module_name)
            m_object = _search_module_for_obj(m_module, obj_dict)
            if m_object:
                return m_object
    
    raise ValueError('load_object() could not find a class with cls._fw_name {}'.format(fw_name))


def load_object_from_file(filename, f_format='AUTO_DETECT'):
    '''
    implicitly load an object from a file. just a friendly wrapper to load_object()
    
    :param filename: the filename to load an object from
    :param f_format: the serialization format (default is auto-detect based on filename extension)
    '''
    m_dict = {}
    if f_format == 'AUTO_DETECT':
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
    '''
    internal method that looks in a module for a class with a given _fw_name
    '''
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
