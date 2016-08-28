# coding: utf-8

from __future__ import unicode_literals

"""
Support for simple timers, with CSV output.

The model is that timers have names, and within timers are multiple named "stages".
"""

import fnmatch
import os
import sys
import time
import six

#: Environment variable in which to list the enabled timers
#: Use comma-separated strings, e.g.:
timer_env_var = "FW_TIMERS"

# Module vars
# -----------

# Dict of timers parsed from env
_env_timers = None

# Flag to only write header once
_wrote_header = False

# All (non-null) timers so far
_timers = set()


# Functions
# ---------


def get_fw_timer(name):
    """G
    et timer, possibly a NullTimer, for a section of code.

    If the user did not enable timers for this section, will
    return a NullTimer. Otherwise will return a Timer.

    Usage:
        timer = get_fw_timer("StarWars")
        timer.start("jumpToLightSpeed")
        jumpToLightSpeed()
        timer.stop("jumpToLightSpeed")
        ...
        print_fw_timers()  # prints results of all timers

    Args:
        name (str): Name of a given timer.

    Returns:
        Timer: A timer instance
    """
    # Get enabled timer patterns from env., if this
    # hasn't already been done.
    if _env_timers is None:
        _set_env_timers()

    # See if this timer is enabled.
    enabled = any(map(lambda pat: fnmatch.fnmatch(name, pat),
                      _env_timers))

    # Return a real timer if enabled, else a Null one.
    if enabled:
        tm = Timer(name)
        _timers.add(tm)
    else:
        tm = NullTimer()
    return tm


def _set_env_timers():
    """
    Parse enabled timers from env.
    These are glob-style patterns like "LaunchPad*", separated by commas.
    """
    global _env_timers
    pstr = os.environ.get(timer_env_var, "")
    _env_timers = [s.strip() for s in pstr.split(",")]


def enable_fw_timer(name, is_enabled):
    """
    Enable or disable a timer.

    Args:
        name (str): Timer's name, or glob-style name pattern
        is_enabled (bool): Whether to enable (True) or disable (False)
    """
    _env_timers[name] = is_enabled


def any_fw_timers():
    """
    Whether any timers are enabled and non-empty

    Returns:
        bool: True if so, False if not
    """
    return sum(map(len, _timers)) > 0


def print_fw_timers(stream=sys.stdout):
    """
    Print results of all timers to the provided stream.

    Args:
        stream: Output stream, only needs to support 'write'

    Returns:
        int: number of items (data rows) printed
    """
    n = 0
    for tm in _timers:
        tm.write(stream)
        n += len(tm)
    return n


# Classes
# -------

class Timer(object):
    """
    Simple performance timer.

    Usage:
        p = Timer("myname")
        for thing in all_things:
            p.start("stage1")
            do_stage_1()
            p.stop("stage1")
            # alt. 'with' interface
            with p.block("stage2"):
                do_something_else()

    Limitations:
    - Instances are not thread-safe.
    - The set_ns() class method is not thread-safe.
    - The 'with' block() cannot be nested,
      instead use different stages with begin()/end() pairs.
    - The only output format is CSV.
    - There is no (easy) programmatic way to get the results.
    """

    _ns = None

    def __init__(self, name):
        self.name = name
        self._cur_stage = None
        self._stage_times = {}
        self._stage_counts = {}
        self._stage_active = set()

    def __len__(self):
        """
        Number of stages timed.

        Returns:
            int: number of stages
        """
        return len(self._stage_times)

    @classmethod
    def set_ns(cls, val):
        """
        Set a namespace (prefix) for all timers.
        In output, the namespace will be separated by the timer name by a "."
        """
        cls._ns = val

    def block(self, stage):
        self._cur_stage = stage
        return self

    def __enter__(self):
        self.start(self._cur_stage)

    def __exit__(self, type_, value, tb):
        self.stop(self._cur_stage)
        return type_ is None  # not an exception

    def start(self, stage="null"):
        """
        Begin timing.
        """
        tm = self._stage_times.get(stage, 0)
        self._stage_times[stage] = tm - time.time()
        self._stage_active.add(stage)

    def stop(self, stage="null"):
        """
        Stop timing.
        """
        self._stage_times[stage] += time.time()
        count = self._stage_counts.get(stage, 0)
        self._stage_counts[stage] = count + 1
        self._stage_active.remove(stage)

    def stop_all(self):
        """
        Stop all timers.
        Idempotent.
        """
        map(self.stop, list(self._stage_active))
        self._stage_active = set()

    def __str__(self):
        """
        Return results as CSV.
        """
        return self._csv()

    def write(self, stream=sys.stdout):
        """
        Write results (CSV) to a stream.
        """
        stream.write(str(self))
        stream.write("\n")

    def _csv(self):
        global _wrote_header
        self.stop_all()
        rows = []
        if not _wrote_header:
            rows.append("name,stage,count,time")
            _wrote_header = True
        ns = "{}.".format(self._ns) if self._ns else ""
        for stage in six.iterkeys(self._stage_times):
            rows.append("{ns}{n},{s},{c:d},{t:.3f}"
                        .format(ns=ns, n=self.name, s=stage,
                                c=self._stage_counts.get(stage, 0),
                                t=self._stage_times.get(stage, 0.0)))
        return '\n'.join(rows)


class NullTimer(Timer):
    """Support performance timer interface, but do absolutely nothing.
    This is useful to avoid many tiresome if/else blocks.
    """
    def __init__(self):
        Timer.__init__(self, "")

    def start(self, stage):
        pass

    def stop(self, stage):
        pass

    def write(self, **kwargs):
        pass

    def block(self, stage):
        return self

    def __enter__(self):
        pass

    def __exit__(self, type_, value, tb):
        return type_ is None  # re-raises exception, if there was one

    def __len__(self):
        return 0
