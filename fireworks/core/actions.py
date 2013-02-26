#!/usr/bin/env python

'''
This module defines various classes of supported actions. All actions are
implemented as static methods, but are defined using classes (as opposed to
modules) so that a set of well-defined actions can be namespaced easily.

It also implements a Modder class that performs modifications on objects
using support actions.
'''

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Jun 1, 2012"


import re


def get_nested_dict(input_dict, key):
    current = input_dict
    toks = key.split("->")
    n = len(toks)
    for i, tok in enumerate(toks):
        if tok not in current and i < n - 1:
            current[tok] = {}
        elif i == n - 1:
            return (current, toks[-1])
        current = current[tok]


class DictActions(object):
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
            if key in d and (not isinstance(d[key], list)):
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
            if key in d and (not isinstance(d[key], list)):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            if key in d:
                d[key] = [i for i in d[key] if i != v]

    @staticmethod
    def pull_all(input_dict, settings):
        for k, v in settings.items():
            if k in input_dict and (not isinstance(input_dict[k], list)):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            for i in v:
                DictActions.pull(input_dict, {k: i})

    @staticmethod
    def pop(input_dict, settings):
        for k, v in settings.items():
            (d, key) = get_nested_dict(input_dict, k)
            if key in d and (not isinstance(d[key], list)):
                raise ValueError("Keyword {} does not refer to an array."
                .format(k))
            if v == 1:
                d[key].pop()
            elif v == -1:
                d[key].pop(0)

class Modder(object):
    """
    Class to modify a dict/file/any object using a mongo-like language.
    Keywords are mostly adopted from mongo's syntax, but instead of $, an
    underscore precedes action keywords. This is so that the modification can
    be inserted into a mongo db easily.

    Allowable actions are supplied as a list of classes as an argument. Refer
    to the action classes on what the actions do. Action classes are in
    pymatpro.ansible.actions.

    Examples:
    >>> modder = Modder()
    >>> d = {"Hello": "World"}
    >>> mod = {'_set': {'Hello':'Universe', 'Bye': 'World'}}
    >>> modder.modify(mod, d)
    >>> d['Bye']
    'World'
    >>> d['Hello']
    'Universe'
    """
    def __init__(self, actions=None, strict=True):
        """
        Args:
            actions:
                A sequence of supported actions. Default is None, which means
                only DictActions are supported.
            strict:
                Boolean indicating whether to use strict mode. In non-strict
                mode, unsupported actions are simply ignored without any
                errors raised. In strict mode, if an unsupported action is
                supplied, a ValueError is raised. Defaults to True.
        """
        self.supported_actions = {}
        actions = actions if actions is not None else [DictActions]
        for action in actions:
            for i in dir(action):
                if (not re.match('__\w+__', i)) and \
                        callable(getattr(action, i)):
                    self.supported_actions["_" + i] = getattr(action, i)
        self.strict = strict

    def modify(self, modification, obj):
        """
        Note that modify makes actual in-place modifications. It does not
        return a copy.

        Args:
            modification:
                Modification must be {action_keyword : settings}
            obj:
                Object to modify depending on actions. For example, for
                DictActions, obj will be a dict to be modified. For
                FileActions, obj will be a string with a full pathname to a
                file.
        """
        for action, settings in modification.items():
            if action in self.supported_actions:
                self.supported_actions[action].__call__(obj, settings)
            elif self.strict:
                raise ValueError("{} is not a supported action!"
                .format(action))

    def modify_object(self, modification, obj):
        """
        Modify an object that supports pymatgen's to_dict and from_dict API.

        Args:
            modification:
                Modification must be {action_keyword : settings}
            obj:
                Object to modify
        """
        d = obj.to_dict
        self.modify(modification, d)
        return obj.from_dict(d)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
