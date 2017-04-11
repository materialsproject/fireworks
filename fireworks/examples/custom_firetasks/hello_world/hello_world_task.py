from fireworks import explicit_serialize, FiretaskBase


@explicit_serialize
class HelloTask(FiretaskBase):

    def run_task(self, fw_spec):
        print("Hello, world!")