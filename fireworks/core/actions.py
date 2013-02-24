#!/usr/bin/env python

'''
This module defines various classes of supported actions. All actions are
implemented as static methods, but are defined using classes (as opposed to
modules) so that a set of well-defined actions can be namespaced easily.
'''

from __future__ import division

__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyue@mit.edu"
__date__ = "Jun 2, 2012"


import os
import shutil


from pymatgen import zopen


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


class FileActions(object):
    """
    Class of supported file actions. For FileActions, the modder class takes in
    a filename as a string. The filename should preferably be a full path to
    avoid ambiguity.
    """

    @staticmethod
    def file_create(filename, settings):
        """
        Creates a file.

        Args:
            filename:
                Filename.
            settings:
                Must be {"content": actual_content}
        """
        if len(settings) != 1:
            raise ValueError("Settings must only contain one item with key "
                             "'content'.")
        for k, v in settings.items():
            if k == "content":
                with zopen(filename, 'wb') as f:
                    f.write(v)

    @staticmethod
    def file_move(filename, settings):
        """
        Moves a file. {'_file_move': {'dest': 'new_file_name'}}

        Args:
            filename:
                Filename.
            settings:
                Must be {"dest": path of new file}
        """
        if len(settings) != 1:
            raise ValueError("Settings must only contain one item with key "
                             "'dest'.")
        for k, v in settings.items():
            if k == "dest":
                shutil.move(filename, v)

    @staticmethod
    def file_delete(filename, settings):
        """
        Deletes a file. {'_file_delete': {'mode': "actual"}}

        Args:
            filename:
                Filename.
            settings:
                Must be {"mode": actual/simulated}. Simulated mode only prints
                the action without performing it.
        """
        if len(settings) != 1:
            raise ValueError("Settings must only contain one item with key "
                             "'mode'.")
        for k, v in settings.items():
            if k == "mode" and v == "actual":
                os.remove(filename)
            elif k == "mode" and v == "simulated":
                print "Simulated removal of {}".format(filename)

    @staticmethod
    def file_copy(filename, settings):
        """
        Copies a file. {'_file_copy': {'dest': 'new_file_name'}}

        Args:
            filename:
                Filename.
            settings:
                Must be {"dest": path of new file}
        """
        for k, v in settings.items():
            if k.startswith("dest"):
                shutil.copyfile(filename, v)
