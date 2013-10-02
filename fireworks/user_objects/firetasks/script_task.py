import shlex
import subprocess
import sys

from fireworks.core.firework import FireTaskBase, FWAction
from fireworks.utilities.fw_serializers import FWSerializable

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 18, 2013'

# TODO: document!
# TODO: add maximum length of 10,000 chars for stored fields


class ScriptTask(FireTaskBase, FWSerializable):
    _fw_name = "Script Task"

    def __init__(self, parameters):
        self.update(parameters)

        if not parameters.get("use_global_spec"):
            self._load_parameters(parameters)

    def run_task(self, fw_spec):
        if self.get("use_global_spec"):
            self._load_parameters(fw_spec)

        # get the standard in and run task internally
        if self.stdin_file:
            with open(self.stdin_file) as stdin_f:
                return self._run_task_internal(fw_spec, stdin_f)
        stdin = subprocess.PIPE if self.stdin_key else None
        return self._run_task_internal(fw_spec, stdin)

    def _run_task_internal(self, fw_spec, stdin):
        # run the program
        stdout = subprocess.PIPE if self.store_stdout or self.stdout_file else sys.stdout
        stderr = subprocess.PIPE if self.store_stderr or self.stderr_file else sys.stderr

        p = subprocess.Popen(self.script, executable=self.shell_exe, stdin=stdin, stdout=stdout, stderr=stderr,
                             shell=self.use_shell)

        # communicate in the standard in and get back the standard out and returncode
        if self.stdin_key:
            (stdout, stderr) = p.communicate(fw_spec[self.stdin_key])
        else:
            (stdout, stderr) = p.communicate()
        returncode = p.returncode

        # write out the output, error files if specified

        if self.stdout_file:
            with open(self.stdout_file, 'a+') as f:
                f.write(stdout)

        if self.stderr_file:
            with open(self.stderr_file, 'a+') as f:
                f.write(stderr)

        # write the output keys
        output = {}

        if self.store_stdout:
            output['stdout'] = stdout

        if self.store_stderr:
            output['stderr'] = stderr

        output['returncode'] = returncode

        if self.defuse_bad_rc and returncode != 0:
            return FWAction(stored_data=output, defuse_children=True)

        elif self.fizzle_bad_rc and returncode != 0:
            raise RuntimeError('ScriptTask fizzled! Return code: {}'.format(returncode))

        return FWAction(stored_data=output)

    def _load_parameters(self, params):
        if params.get('stdin_file') and params.get('stdin_key'):
            raise ValueError("Script Task cannot process both a key and file as the standard in!")

        self.use_shlex = params.get('use_shlex', True)
        self.use_shell = params.get('use_shell', True)

        if self.use_shlex and not self.use_shell:
            self.script = shlex.split(str(params['script']))
        else:
            self.script = params['script']

        self.stdin_file = params.get('stdin_file')
        self.stdin_key = params.get('stdin_key')
        self.stdout_file = params.get('stdout_file')
        self.stderr_file = params.get('stderr_file')
        self.store_stdout = params.get('store_stdout')
        self.store_stderr = params.get('store_stderr')
        self.defuse_bad_rc = params.get('defuse_bad_rc')
        self.fizzle_bad_rc = params.get('fizzle_bad_rc', True)
        self.shell_exe = params.get('shell_exe')

    @classmethod
    def from_str(cls, shell_cmd, parameters=None):
        parameters = parameters if parameters else {}
        parameters['script'] = shell_cmd
        parameters['use_shell'] = True
        return ScriptTask(parameters)