from fireworks import explicit_serialize, FireTaskBase


@explicit_serialize
class HelloTask(FireTaskBase):

    def run_task(self, fw_spec):
        print("Hello, world!")