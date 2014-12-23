from __future__ import unicode_literals, division

from fireworks import FireTaskBase, FWAction
from fireworks.utilities.fw_utilities import explicit_serialize

class SerializableException(Exception):
    def __init__(self, exc_details):
        self.exc_details = exc_details

    def to_dict(self):
        return self.exc_details

@explicit_serialize
class ExceptionTestTask(FireTaskBase):
    exec_counter = 0

    def run_task(self, fw_spec):
        ExceptionTestTask.exec_counter += 1
        if not fw_spec.get('skip_exception', False):
            raise SerializableException(self['exc_details'])

@explicit_serialize
class ExecutionCounterTask(FireTaskBase):
    exec_counter = 0

    def run_task(self, fw_spec):
        ExecutionCounterTask.exec_counter += 1

@explicit_serialize
class MalformedAdditionTask(FireTaskBase):
    def run_task(self, fw_spec):
        return FWAction(additions=TodictErrorTask())

@explicit_serialize
class TodictErrorTask(FireTaskBase):
    def to_dict(self):
        raise RuntimeError("to_dict error")

    def run_task(self, fw_spec):
        return FWAction()