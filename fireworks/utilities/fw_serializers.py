"""
This module aids in serializing and deserializing objects.

To serialize a FW object, refer to the documentation for the FWSerializable class. To de-serialize
an object, refer to the documentation for the FWSerializable class and load_object() method.
    - you can de-serialize explicitly, e.g. FWObject.from_dict() to enforce a FWObject instance as the result
    - you can de-serialize implicitly, e.g. load_object() to search for the correct Class dynamically

The implicit method is especially useful if you don't know in advance which subclass of a base class
your serialization might point to. e.g. if you require some type of Quadrilateral, a serialization
from your collaborator might point to a Square, Rhombus, or Rectangle, and you might not know which
one in advance...

Some advantages:
    - Robust with regard to code refactorings even in implicit loading given certain reasonable
        guidelines on fw_name.
    - Simple to allow a superclass to define all the serializations for its subclasses, removing
        code repetition(in particular, note that from_dict is a class method rather than a static
        method, allowing use of self)
    - Decorators aid in some of the routine parts of the serialization, such as adding the _fw_name key
    - Both JSON and YAML file import/export are naturally and concisely supported within the framework.
    - Auto-detect and proper loading of JSON and YAML files
    - Proper JSON handling of datetime (both encoding and decoding) and UTF-8 strings
    - In some cases, objects can be serialized/deserialized extremely concisely, by use of only
        their fw_name (if no parameters are needed to describe the object)

"""

import abc
import datetime
import importlib
import inspect
import json  # note that ujson is faster, but at this time does not support "default" in dumps()
import pkgutil
import traceback

import ruamel.yaml as yaml
from monty.json import MontyDecoder, MSONable

from fireworks.fw_config import (
    DECODE_MONTY,
    ENCODE_MONTY,
    FW_NAME_UPDATES,
    JSON_SCHEMA_VALIDATE,
    JSON_SCHEMA_VALIDATE_LIST,
    USER_PACKAGES,
    YAML_STYLE,
)

__author__ = "Anubhav Jain"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Dec 13, 2012"

# TODO: consider *somehow* switching FireWorks to monty serialization. e.g., numpy serialization is better handled.

SAVED_FW_MODULES = {}
DATETIME_HANDLER = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

ENCODING_PARAMS = {"encoding": "utf-8"}

try:
    import numpy as np

    NUMPY_INSTALLED = True
except Exception:
    NUMPY_INSTALLED = False

if JSON_SCHEMA_VALIDATE:
    import fireworks_schema


def recursive_dict(obj, preserve_unicode=True):
    if obj is None:
        return None

    if ENCODE_MONTY and hasattr(obj, "as_dict"):  # compatible with new monty JSONEncoder (MontyEncoder)
        return recursive_dict(obj.as_dict(), preserve_unicode)

    if hasattr(obj, "to_dict"):
        return recursive_dict(obj.to_dict(), preserve_unicode)

    if isinstance(obj, dict):
        return {recursive_dict(k, preserve_unicode): recursive_dict(v, preserve_unicode) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [recursive_dict(v, preserve_unicode) for v in obj]

    if isinstance(obj, int) or isinstance(obj, float):
        return obj

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if preserve_unicode and isinstance(obj, str) and obj != obj.encode("ascii", "ignore"):
        return obj

    if NUMPY_INSTALLED and isinstance(obj, np.ndarray):
        return [recursive_dict(v, preserve_unicode) for v in obj.tolist()]

    return str(obj)


# TODO: is reconstitute_dates really needed? Can this method just do everything?
def _recursive_load(obj):
    if obj is None:
        return None

    if hasattr(obj, "_fw_name") or isinstance(obj, MSONable):
        return obj

    if isinstance(obj, dict):
        if "_fw_name" in obj:
            return load_object(obj)

        if DECODE_MONTY and "@module" in obj and "@class" in obj:  # MontyDecoder compatibility
            return json.loads(json.dumps(obj), cls=MontyDecoder)

        return {k: _recursive_load(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_recursive_load(v) for v in obj]

    if isinstance(obj, str):
        try:
            # convert String to datetime if really datetime
            return reconstitute_dates(obj)
        except Exception:
            # convert unicode to ASCII if not really unicode
            if obj == obj.encode("ascii", "ignore"):
                return str(obj)

    return obj


def recursive_serialize(func):
    """
    a decorator to add FW serializations keys
    see documentation of FWSerializable for more details
    """

    def _decorator(self, *args, **kwargs):
        m_dict = func(self, *args, **kwargs)
        m_dict = recursive_dict(m_dict)
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
        m_dict["_fw_name"] = self.fw_name
        return m_dict

    return _decorator


class FWSerializable(metaclass=abc.ABCMeta):
    """
    To create a serializable object within FireWorks, you should subclass this
    class and implement the to_dict() and from_dict() methods.

    If you want the load_object() implicit de-serialization to work, you must
    also:
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
            return get_default_serialization(self.__class__)

    @abc.abstractmethod
    def to_dict(self):
        raise NotImplementedError("FWSerializable object did not implement to_dict()!")

    def to_db_dict(self):
        return self.to_dict()

    def as_dict(self):
        # strictly for pseudo-compatibility with MSONable
        # Note that FWSerializable is not MSONable, it uses _fw_name instead of __class__ and
        # __module__
        return self.to_dict()

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, m_dict):
        raise NotImplementedError("FWSerializable object did not implement from_dict()!")

    def __repr__(self):
        return json.dumps(self.to_dict(), default=DATETIME_HANDLER)

    def to_format(self, f_format="json", **kwargs):
        """
        returns a String representation in the given format

        Args:
            f_format (str): the format to output to (default json)
        """
        if f_format == "json":
            return json.dumps(self.to_dict(), default=DATETIME_HANDLER, **kwargs)
        elif f_format == "yaml":
            # start with the JSON format, and convert to YAML
            return yaml.safe_dump(self.to_dict(), default_flow_style=YAML_STYLE, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format {f_format}")

    @classmethod
    def from_format(cls, f_str, f_format="json"):
        """
        convert from a String representation to its Object.

        Args:
            f_str (str): the String representation
            f_format (str): serialization format of the String (default json)

        Returns:
            FWSerializable
        """
        if f_format == "json":
            dct = json.loads(f_str)
        elif f_format == "yaml":
            dct = yaml.safe_load(f_str)
        else:
            raise ValueError(f"Unsupported format {f_format}")
        if JSON_SCHEMA_VALIDATE and cls.__name__ in JSON_SCHEMA_VALIDATE_LIST:
            fireworks_schema.validate(dct, cls.__name__)
        return cls.from_dict(reconstitute_dates(dct))

    def to_file(self, filename, f_format=None, **kwargs):
        """
        Write a serialization of this object to a file.

        Args:
            filename(str): filename to write to
            f_format (str): serialization format, default checks the filename extension
        """
        if f_format is None:
            f_format = filename.split(".")[-1]
        with open(filename, "w", **ENCODING_PARAMS) as f:
            f.write(self.to_format(f_format=f_format, **kwargs))

    @classmethod
    def from_file(cls, filename, f_format=None):
        """
        Load a serialization of this object from a file.

        Args:
            filename (str): filename to read
            f_format (str): serialization format, default checks the filename extension

        Returns:
            FWSerializable
        """
        if f_format is None:
            f_format = filename.split(".")[-1]
        with open(filename, "r", **ENCODING_PARAMS) as f:
            return cls.from_format(f.read(), f_format=f_format)

    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, state):
        fw_obj = self.from_dict(state)
        for k, v in fw_obj.__dict__.items():
            self.__dict__[k] = v


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

    Args:
        obj_dict (dict): the dict representation of the class
    """

    # override the name in the obj_dict if there's an entry in FW_NAME_UPDATES
    fw_name = FW_NAME_UPDATES.get(obj_dict["_fw_name"], obj_dict["_fw_name"])
    obj_dict["_fw_name"] = fw_name

    # check for explicit serialization, e.g. {{fireworks.tasks.MyTask}} - based on pymatgen method
    if fw_name.startswith("{{") and fw_name.endswith("}}"):
        modname, classname = fw_name.strip("{} ").rsplit(".", 1)
        mod = __import__(modname, globals(), locals(), [classname], 0)
        if hasattr(mod, classname):
            cls_ = getattr(mod, classname)
            return cls_.from_dict(obj_dict)

    # first try to load from known location
    if fw_name in SAVED_FW_MODULES:
        m_module = importlib.import_module(SAVED_FW_MODULES[fw_name])
        m_object = _search_module_for_obj(m_module, obj_dict)
        if m_object is not None:
            return m_object

    # failing that, look for the object within all of USER_PACKAGES
    # this will be slow, but only needed the first time

    found_objects = []  # used to make sure we don't find multiple hits
    for package in USER_PACKAGES:
        root_module = importlib.import_module(package)
        for _, mod_name, is_pkg in pkgutil.walk_packages(root_module.__path__, package + "."):
            try:
                m_module = importlib.import_module(mod_name)
                m_object = _search_module_for_obj(m_module, obj_dict)
                if m_object is not None:
                    found_objects.append((m_object, mod_name))
            except ImportError as ex:
                import warnings

                warnings.warn(f"{m_object} in {mod_name} cannot be loaded because of {str(ex)}. Skipping..")
                traceback.print_exc(ex)

    if len(found_objects) == 1:
        SAVED_FW_MODULES[fw_name] = found_objects[0][1]
        return found_objects[0][0]
    elif len(found_objects) > 0:
        raise ValueError(f"load_object() found multiple objects with cls._fw_name {fw_name} -- {found_objects}")

    raise ValueError(f"load_object() could not find a class with cls._fw_name {fw_name}")


def load_object_from_file(filename, f_format=None):
    """
    Implicitly load an object from a file. just a friendly wrapper to
    load_object()

    Args:
        filename (str): the filename to load an object from
        f_format (str): the serialization format (default is auto-detect based on
            filename extension)
    """
    if f_format is None:
        f_format = filename.split(".")[-1]

    with open(filename, "r", **ENCODING_PARAMS) as f:
        if f_format == "json":
            dct = json.loads(f.read())
        elif f_format == "yaml":
            dct = yaml.safe_load(f)
        else:
            raise ValueError(f"Unknown file format {f_format} cannot be loaded!")

    classname = FW_NAME_UPDATES.get(dct["_fw_name"], dct["_fw_name"])
    if JSON_SCHEMA_VALIDATE and classname in JSON_SCHEMA_VALIDATE_LIST:
        fireworks_schema.validate(dct, classname)
    return load_object(reconstitute_dates(dct))


def _search_module_for_obj(m_module, obj_dict):
    """
    internal method that looks in a module for a class with a given _fw_name
    """
    obj_name = obj_dict["_fw_name"]

    for _, obj in inspect.getmembers(m_module):
        # check if the member is a Class matching our description
        if (
            inspect.isclass(obj)
            and obj.__module__ == m_module.__name__
            and getattr(obj, "_fw_name", get_default_serialization(obj)) == obj_name
        ):
            return obj.from_dict(obj_dict)


def reconstitute_dates(obj_dict):
    if obj_dict is None:
        return None

    if isinstance(obj_dict, dict):
        return {k: reconstitute_dates(v) for k, v in obj_dict.items()}

    if isinstance(obj_dict, (list, tuple)):
        return [reconstitute_dates(v) for v in obj_dict]

    if isinstance(obj_dict, str):
        try:
            return datetime.datetime.strptime(obj_dict, "%Y-%m-%dT%H:%M:%S.%f")
        except Exception:
            try:
                return datetime.datetime.strptime(obj_dict, "%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
    return obj_dict


def get_default_serialization(cls):
    root_mod = cls.__module__.split(".")[0]
    if root_mod == "__main__":
        raise ValueError(
            "Cannot get default serialization; try "
            "instantiating your object from a different module "
            "from which it is defined rather than defining your "
            "object in the __main__ (running) module."
        )
    return root_mod + "::" + cls.__name__  # e.g. fireworks.ABC
