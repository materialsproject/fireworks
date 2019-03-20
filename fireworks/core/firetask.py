__author__ = "Anubhav Jain"
__credits__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Anubhav Jain"
__email__ = "ajain@lbl.gov"
__date__ = "Feb 5, 2013"


@add_metaclass(abc.ABCMeta)
class Firetask(defaultdict, FWSerializable):
    """
    FiretaskBase is used like an abstract class that defines a computing task
    (Firetask). All Firetasks should inherit from FiretaskBase.

    You can set parameters of a Firetask like you'd use a dict.
    """
    # Specify required parameters with class variable. Consistency will be checked upon init.
    required_params = []

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        for k in self.required_params:
            if k not in self:
                raise ValueError("{}: Required parameter {} not specified!".format(self, k))

    @abc.abstractmethod
    def run_task(self, fw_spec):
        """
        This method gets called when the Firetask is run. It can take in a
        Firework spec, perform some task using that data, and then return an
        output in the form of a FWAction.

        Args:
            fw_spec (dict): A Firework spec. This comes from the master spec.
                In addition, this spec contains a special "_fw_env" key that
                contains the env settings of the FWorker calling this method.
                This provides for abstracting out certain commands or
                settings. For example, "foo" may be named "foo1" in resource
                1 and "foo2" in resource 2. The FWorker env can specify {
                "foo": "foo1"}, which maps an abstract variable "foo" to the
                relevant "foo1" or "foo2". You can then write a task that
                uses fw_spec["_fw_env"]["foo"] that will work across all
                these multiple resources.

        Returns:
            (FWAction)
        """
        raise NotImplementedError("You must have a run_task implemented!")

    @serialize_fw
    @recursive_serialize
    def to_dict(self):
        return dict(self)

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return cls(m_dict)

    def __repr__(self):
        return '<{}>:{}'.format(self.fw_name, dict(self))

    # not strictly needed here for pickle/unpickle, but complements __setstate__
    def __getstate__(self):
        return self.to_dict()

    # added to support pickle/unpickle
    def __setstate__(self, state):
        self.__init__(state)

    # added to support pickle/unpickle
    def __reduce__(self):
        t = defaultdict.__reduce__(self)
        return (t[0], (self.to_dict(),), t[2], t[3], t[4])


class BackgroundTask(FWSerializable, object):
    _fw_name = 'BackgroundTask'

    def __init__(self, tasks, num_launches=0, sleep_time=60, run_on_finish=False):
        """
        Args:
            tasks [Firetask]: a list of Firetasks to perform
            num_launches (int): the total number of times to run the process (0=infinite)
            sleep_time (int): sleep time in seconds between background runs
            run_on_finish (bool): always run this task upon completion of Firework
        """
        self.tasks = tasks if isinstance(tasks, (list, tuple)) else [tasks]
        self.num_launches = num_launches
        self.sleep_time = sleep_time
        self.run_on_finish = run_on_finish

    @recursive_serialize
    @serialize_fw
    def to_dict(self):
        return {'tasks': self.tasks, 'num_launches': self.num_launches,
                'sleep_time': self.sleep_time, 'run_on_finish': self.run_on_finish}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict):
        return BackgroundTask(m_dict['tasks'], m_dict['num_launches'],
                              m_dict['sleep_time'], m_dict['run_on_finish'])


class FWAction(FWSerializable):
    """
    A FWAction encapsulates the output of a Firetask (it is returned by a Firetask after the
    Firetask completes). The FWAction allows a user to store rudimentary output data as well
    as return commands that alter the workflow.
    """

    def __init__(self, stored_data: dict=None, exit: bool=False,
                 update_spec: dict=None, mod_spec: List[dict]=None,
                 additions: List[Workflow]=None, detours: List[Workflow]=None,
                 defuse_children: bool=False, defuse_workflow: bool=False):
        """
        Args:
            stored_data (dict): data to store from the run. Does not affect the operation of FireWorks.
            exit (bool): if set to True, any remaining Firetasks within the same Firework are skipped.
            update_spec (dict): specifies how to update the child FW's spec
            mod_spec ([dict]): update the child FW's spec using the DictMod language (more flexible
                than update_spec)
            additions ([Workflow]): a list of WFs/FWs to add as children
            detours ([Workflow]): a list of WFs/FWs to add as children (they will inherit the
                current FW's children)
            defuse_children (bool): defuse all the original children of this Firework
            defuse_workflow (bool): defuse all incomplete steps of this workflow
        """
        mod_spec = mod_spec if mod_spec is not None else []
        additions = additions if additions is not None else []
        detours = detours if detours is not None else []

        self.stored_data = stored_data if stored_data else {}
        self.exit = exit
        self.update_spec = update_spec if update_spec else {}
        self.mod_spec = mod_spec if isinstance(mod_spec, (list, tuple)) else [mod_spec]
        self.additions = additions if isinstance(additions, (list, tuple)) else [additions]
        self.detours = detours if isinstance(detours, (list, tuple)) else [detours]
        self.defuse_children = defuse_children
        self.defuse_workflow = defuse_workflow

    @recursive_serialize
    def to_dict(self) -> dict:
        return {'stored_data': self.stored_data,
                'exit': self.exit,
                'update_spec': self.update_spec,
                'mod_spec': self.mod_spec,
                'additions': self.additions,
                'detours': self.detours,
                'defuse_children': self.defuse_children,
                'defuse_workflow': self.defuse_workflow}

    @classmethod
    @recursive_deserialize
    def from_dict(cls, m_dict: dict) -> FWAction:
        d = m_dict
        additions = [Workflow.from_dict(f) for f in d['additions']]
        detours = [Workflow.from_dict(f) for f in d['detours']]
        return FWAction(d['stored_data'], d['exit'], d['update_spec'],
                        d['mod_spec'], additions, detours,
                        d['defuse_children'], d.get('defuse_workflow', False))

    @property
    def skip_remaining_tasks(self) -> bool:
        """
        If the FWAction gives any dynamic action, we skip the subsequent Firetasks

        Returns:
            bool
        """
        return self.exit or self.detours or self.additions or self.defuse_children or self.defuse_workflow

    def __str__(self):
        return "FWAction\n" + pprint.pformat(self.to_dict())


class Tracker(FWSerializable, object):
    """
    A Tracker monitors a file and returns the last N lines for updating the Launch object.
    """

    MAX_TRACKER_LINES = 1000

    def __init__(self, filename: str, nlines: int=TRACKER_LINES,
                 content: str='', allow_zipped: bool=False):
        """
        Args:
            filename (str)
            nlines (int): number of lines to track
            content (str): tracked content
            allow_zipped (bool): if set, will look for zipped file.
        """
        if nlines > self.MAX_TRACKER_LINES:
            raise ValueError("Tracker only supports a maximum of {} lines; you put {}.".format(
                self.MAX_TRACKER_LINES, nlines))
        self.filename = filename
        self.nlines = nlines
        self.content = content
        self.allow_zipped = allow_zipped

    def track_file(self, launch_dir: str=None) -> str:
        """
        Reads the monitored file and returns back the last N lines

        Args:
            launch_dir (str): directory where job was launched in case of relative filename

        Returns:
            str: the content(last N lines)
        """
        m_file = self.filename
        if launch_dir and not os.path.isabs(self.filename):
            m_file = os.path.join(launch_dir, m_file)
        lines = []
        if self.allow_zipped:
            m_file = zpath(m_file)
        if os.path.exists(m_file):
            with zopen(m_file, "rt") as f:
                for l in reverse_readline(f):
                    lines.append(l)
                    if len(lines) == self.nlines:
                        break
            self.content = '\n'.join(reversed(lines))
        return self.content

    def to_dict(self) -> dict:
        m_dict = {'filename': self.filename, 'nlines': self.nlines, 'allow_zipped': self.allow_zipped}
        if self.content:
            m_dict['content'] = self.content
        return m_dict

    @classmethod
    def from_dict(cls, m_dict: dict) -> Tracker:
        return Tracker(m_dict['filename'], m_dict['nlines'], m_dict.get('content', ''),
                       m_dict.get('allow_zipped', False))

    def __str__(self):
        return '### Filename: {}\n{}'.format(self.filename, self.content)