""" This module includes tasks to integrate scripts and python functions """

import shlex
import subprocess
import sys
from fireworks.core.firework import FiretaskBase, FWAction
from six.moves import builtins
if sys.version_info[0] > 2:
    basestring = str

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 18, 2013'


class ScriptTask(FiretaskBase):
    """ Runs a user-defined script """
    required_params = ['script']
    _fw_name = 'ScriptTask'

    def run_task(self, fw_spec):
        if self.get('use_global_spec'):
            self._load_params(fw_spec)
        else:
            self._load_params(self)

        # get the standard in and run task internally
        if self.stdin_file:
            with open(self.stdin_file) as stdin_f:
                return self._run_task_internal(fw_spec, stdin_f)
        stdin = subprocess.PIPE if self.stdin_key else None
        return self._run_task_internal(fw_spec, stdin)

    def _run_task_internal(self, fw_spec, stdin):
        # run the program
        stdout = subprocess.PIPE if self.store_stdout or self.stdout_file else None
        stderr = subprocess.PIPE if self.store_stderr or self.stderr_file else None
        returncodes = []
        for s in self.script:
            p = subprocess.Popen(
                s, executable=self.shell_exe, stdin=stdin,
                stdout=stdout, stderr=stderr,
                shell=self.use_shell)

            # communicate in the standard in and get back the standard out and returncode
            if self.stdin_key:
                (stdout, stderr) = p.communicate(fw_spec[self.stdin_key])
            else:
                (stdout, stderr) = p.communicate()
            returncodes.append(p.returncode)

            # stop execution if any script command fails
            if p.returncode != 0:
                break

        # write out the output, error files if specified

        stdout = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr

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

        output['returncode'] = returncodes[-1]
        output['all_returncodes'] = returncodes

        if self.defuse_bad_rc and sum(returncodes) != 0:
            return FWAction(stored_data=output, defuse_children=True)

        elif self.fizzle_bad_rc and sum(returncodes) != 0:
            raise RuntimeError('ScriptTask fizzled! Return code: {}'.format(returncodes))

        return FWAction(stored_data=output)

    def _load_params(self, d):
        if d.get('stdin_file') and d.get('stdin_key'):
            raise ValueError('ScriptTask cannot process both a key and file as the standard in!')

        self.use_shell = d.get('use_shell', True)

        m_script = d['script']
        if isinstance(m_script, basestring):
            m_script = [m_script]

        if not self.use_shell:
            self.script = [shlex.split(str(s) for s in m_script)]
        else:
            self.script = m_script

        self.stdin_file = d.get('stdin_file')
        self.stdin_key = d.get('stdin_key')
        self.stdout_file = d.get('stdout_file')
        self.stderr_file = d.get('stderr_file')
        self.store_stdout = d.get('store_stdout')
        self.store_stderr = d.get('store_stderr')
        self.shell_exe = d.get('shell_exe')
        self.defuse_bad_rc = d.get('defuse_bad_rc')
        self.fizzle_bad_rc = d.get('fizzle_bad_rc', not self.defuse_bad_rc)

        if self.defuse_bad_rc and self.fizzle_bad_rc:
            raise ValueError('ScriptTask cannot both FIZZLE and DEFUSE a bad returncode!')

    @classmethod
    def from_str(cls, shell_cmd, parameters=None):
        parameters = parameters if parameters else {}
        parameters['script'] = [shell_cmd]
        parameters['use_shell'] = True
        return cls(parameters)


class PyTask(FiretaskBase):
    """
    Runs any python function! Extremely powerful, which allows you to
    essentially run any accessible method on the system. The optional inputs
    and outputs lists may contain spec keys to add to args list and to make
    the function output available in the curent and in children fireworks.

    Required parameters:
        - func (str): Fully qualified python method. E.g., json.dump, or shutil
            .copy, or some other function that is not part of the standard
            library!

    Optional parameters:
        - args (list): List of args. Default is empty.
        - kwargs (dict): Dictionary of keyword args. Default is empty.
        - auto_kwargs (bool): If True, all other params not starting with '_'
          are supplied as keyword args
        - stored_data_varname (str): Whether to store the output in FWAction.
          If this is a string that does not evaluate to False, the output of
          the function will be stored as
          FWAction(stored_data={stored_data_varname: output}). The name is
          deliberately long to avoid potential name conflicts.
        - inputs ([str]): a list of keys in spec which will be used as inputs;
          the generated arguments list will be appended to args
        - outputs ([str]): a list of spec keys that will be used to pass
          the function's outputs to child fireworks
        - chunk_number (int): a serial number of the Firetask within a
          group of Firetasks generated by a ForeachTask
    """
    _fw_name = 'PyTask'
    required_params = ['func']
    optional_params = ['args', 'kwargs', 'auto_kwargs', 'stored_data_varname',
                       'inputs', 'outputs', 'chunk_number']

    def run_task(self, fw_spec):
        toks = self['func'].rsplit('.', 1)
        if len(toks) == 2:
            modname, funcname = toks
            mod = __import__(modname, globals(), locals(), [str(funcname)], 0)
            func = getattr(mod, funcname)
        else:
            # Handle built in functions.
            func = getattr(builtins, toks[0])

        args = list(self.get('args', []))  # defensive copy

        inputs = self.get('inputs', [])
        assert isinstance(inputs, list)
        for item in inputs:
            args.append(fw_spec[item])

        if self.get('auto_kwargs'):
            kwargs = {k: v for k, v in self.items()
                      if not (k.startswith('_')
                              or k in self.required_params
                              or k in self.optional_params)}
        else:
            kwargs = self.get('kwargs', {})

        output = func(*args, **kwargs)

        if isinstance(output, FWAction):
            return output
        actions = {}
        outputs = self.get('outputs', [])
        assert isinstance(outputs, list)
        if len(outputs) == 1:
            if self.get('chunk_number') is None:
                actions['update_spec'] = {outputs[0]: output}
            else:
                if isinstance(output, (list, tuple, set)):
                    mod_spec = [{'_push': {outputs[0]: i}} for i in output]
                else:
                    mod_spec = [{'_push': {outputs[0]: output}}]
                actions['mod_spec'] = mod_spec
        elif len(outputs) > 1:
            assert isinstance(output, (list, tuple, set))
            assert len(output) == len(outputs)
            actions['update_spec'] = dict(zip(outputs, output))
        if self.get('stored_data_varname'):
            actions['stored_data'] = {self['stored_data_varname']: output}
        if len(actions) > 0:
            return FWAction(**actions)
