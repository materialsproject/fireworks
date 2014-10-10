from fireworks.core.firework import FireTaskBase, FWAction
from fireworks.core.firework import Firework
from fireworks.utilities.fw_utilities import explicit_serialize
from fireworks.utilities.fw_serializers import FWSerializable, serialize_fw


@explicit_serialize
class ApparentlyFineTask(FireTaskBase):

    def __init__(self, input_variable):
        self.input_variable = input_variable

    @serialize_fw
    def to_dict(self):
        return {'input_variable': self.input_variable}

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict['input_variable'])

    def run_task(self, fw_spec):
        print "This is my variable: ", self.input_variable

        return FWAction()

@explicit_serialize
class FailingTask(FireTaskBase):

    def run_task(self, fw_spec):
        print "This will fail"

        new_fw = Firework(ApparentlyFineTask('test string'))
        return FWAction(additions=new_fw)

@explicit_serialize
class FixedTask(ApparentlyFineTask):

    def __getitem__(self, item):
        return self.to_dict()[item]

    def items(self):
        return self.to_dict().items()

@explicit_serialize
class WorkingTask(FireTaskBase):

    def run_task(self, fw_spec):
        print "This will work"

        new_fw = Firework(FixedTask('working test'))
        return FWAction(additions=new_fw)

@explicit_serialize
class DuckTypedTask(FWSerializable):
    def __init__(self, input_variable):
        self.input_variable = input_variable

    @serialize_fw
    def to_dict(self):
        return {'input_variable': self.input_variable}

    @classmethod
    def from_dict(cls, m_dict):
        return cls(m_dict['input_variable'])

    def run_task(self, fw_spec):
        print "This is my variable: ", self.input_variable

        new_fw = Firework(DuckTypedTask('test string'))
        return FWAction(additions=new_fw)