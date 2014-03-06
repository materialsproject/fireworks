__author__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = '3/6/14'


class ResourceBase(object):
    """
    Defines an abstraction for mapping of commands. A Resource is essentially a
    machine specific setting for variables. Though it can be used for many
    purposes, the main usage is to decorate FireTasks so that they can
    function on many computing resources in a transparent manner. For
    example, a particular command, say "foo", may be available as "foo1" on
    one machine and as "foo2" on another machine (very common esp for version
    specific executables). A Resource will define an abstraction such that::

        class Machine1(ResourceBase):

            env = {"foo": "foo1"}

            @classmethod
            def at_resource(self):
                return socket.gethostname() == "machine1"

        class Machine2(ResourceBase):

            env = {"foo": "foo2"}

            @classmethod
            def at_resource(self):
                return socket.gethostname() == "machine2"

    This is used together with the supported_resources decorator so that
    within the FireTask, a special _fw_resource variable is set according to
    the detected Resource and is available for use within the system.
    """
    env = {}

    def __getitem__(self, item):
        if item in self.env:
            return self.env[item]
        raise ValueError("No command %s specified for resource %s" %
                         (item, self.__class__.__name__))

    def __getattr__(self, item):
        return self.__getitem__(item)

    @classmethod
    def at_resource(cls):
        """
        (bool) indicating whether the current code is being executed at a
        defined resource.
        """
        pass


def supported_resources(*resources):
    """
    Decorator to mark supported resources for FireTasks. For example,

        @supported_resources(Resource1, Resource2, ...)
        class MyTask(FireTaskBase):
            ...

    Note that the resources are searched in the order they are defined in the
    args.

    Args:
        \*resources: Supported resources.
    """
    def wrap(f):
        current_resource = None
        for r in resources:
            if r.at_resource():
                current_resource = r
                break

        def wrapped_firetask(*args, **kwargs):
            if current_resource is None:
                raise FWResourceError("No valid resources found")
            instance = f(*args, **kwargs)
            instance["_fw_resource"] = r()
            return instance

        return wrapped_firetask
    return wrap


class FWResourceError(Exception):
    pass