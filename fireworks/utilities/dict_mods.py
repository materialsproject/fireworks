# coding: utf-8

from __future__ import unicode_literals

"""
This module allows you to modify a dict (a spec) using another dict (an instruction).
The main method of interest is apply_dictmod().

This code is based heavily on the Ansible class of custodian <https://pypi.python.org/pypi/custodian>,
but simplifies it considerably for the limited use cases required by FireWorks.
"""

import re

from monty.design_patterns import singleton

__author__ = "Shyue Ping Ong"
__credits__ = "Anubhav Jain"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Jun 1, 2012"


def get_nested_dict(input_dict, key):
    current = input_dict
    toks = key.split("->")
    n = len(toks)
    for i, tok in enumerate(toks):
        if tok not in current and i < n - 1:
            current[tok] = {}
        elif i == n - 1:
            return current, toks[-1]
        current = current[tok]


@singleton
class DictMods(object):
    """
    Class to implement the supported mongo-like modifications on a dict.
    Supported keywords include the following Mongo-based keywords, with the
    usual meanings (refer to Mongo documentation for information):
        _inc
        _set
        _unset
        _push
        _push_all
        _add_to_set (but _each is not supported)
        _pop
        _pull
        _pull_all
        _rename

    However, note that "_set" does not support modification of nested dicts
    using the mongo {"a.b":1} notation. This is because mongo does not allow
    keys with "." to be inserted. Instead, nested dict modification is
    supported using a special "->" keyword, e.g. {"a->b": 1}
    """

    def __init__(self):
        self.supported_actions = {}
        for i in dir(self):
            if (not re.match('__\w+__', i)) and callable(getattr(self, i)):
                self.supported_actions["_" + i] = getattr(self, i)

    @staticmethod
    def set(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            d[key] = v

    @staticmethod
    def unset(input_dict, settings):
        for k in settings.keys():
            (d, key) = get_nested_dict(input_dict, k)
            del d[key]

    @staticmethod
    def push(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d:
                d[key].append(v)
            else:
                d[key] = [v]

    @staticmethod
    def push_all(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d:
                d[key].extend(v)
            else:
                d[key] = v

    @staticmethod
    def inc(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d:
                d[key] += v
            else:
                d[key] = v

    @staticmethod
    def rename(input_dict, settings):
        for k, v in settings.items():
            if k in input_dict:
                input_dict[v] = input_dict[k]
                del input_dict[k]

    @staticmethod
    def add_to_set(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d and (not isinstance(d[key], (list, tuple))):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            if key in d and v not in d[key]:
                d[key].append(v)
            elif key not in d:
                d[key] = v

    @staticmethod
    def pull(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d and (not isinstance(d[key], (list, tuple))):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            if key in d:
                d[key] = [i for i in d[key] if i != v]

    @staticmethod
    def pull_all(input_dict, settings):
        for k, v in settings.items():
            if k in input_dict and (not isinstance(input_dict[k], (list, tuple))):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            for i in v:
                DictMods.pull(input_dict, {k: i})

    @staticmethod
    def pop(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d and (not isinstance(d[key], (list, tuple))):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            if v == 1:
                d[key].pop()
            elif v == -1:
                d[key].pop(0)


def apply_mod(modification, obj):
    """
    Note that modify makes actual in-place modifications. It does not
    return a copy.

    Args:
        modification:
            Modification must be {action_keyword : settings}, where action_keyword is a
            supported DictMod
        obj:
            A dict to be modified
    """
    for action, settings in modification.items():
        if action in DictMods().supported_actions:
            DictMods().supported_actions[action].__call__(obj, settings)
        else:
            raise ValueError("{} is not a supported action!".format(action))
