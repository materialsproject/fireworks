from fireworks import FiretaskBase, explicit_serialize


@explicit_serialize
class HelloTask(FiretaskBase):
    def run_task(self, fw_spec) -> None:
        print("Hello, world!")
