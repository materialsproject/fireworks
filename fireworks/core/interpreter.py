#!/usr/bin/env python

"""
This module implements a Modder class that performs modifications on objects
using support actions.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Jun 1, 2012"


import re

from custodian.ansible.actions import DictActions


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
