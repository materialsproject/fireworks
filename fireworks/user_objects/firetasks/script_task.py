import shlex
import subprocess
import sys

from fireworks.core.firework import FireTaskBase, FWAction

__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 18, 2013'

# TODO: document!
# TODO: add maximum length of 10,000 chars for stored fields


class ScriptTask(FireTaskBase):
    required_params = ["script"]
    _fw_name = 'ScriptTask'

    def run_task(self, fw_spec):
        if self.get("use_global_spec"):
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
        stdout = subprocess.PIPE if self.store_stdout or self.stdout_file else sys.stdout
        stderr = subprocess.PIPE if self.store_stderr or self.stderr_file else sys.stderr
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

            #Stop execution if any script command fails.
            if p.returncode != 0:
                break

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

        output['returncode'] = returncodes[-1]
        output['all_returncodes'] = returncodes

        if self.defuse_bad_rc and sum(returncodes) != 0:
            return FWAction(stored_data=output, defuse_children=True)

        elif self.fizzle_bad_rc and sum(returncodes) != 0:
            raise RuntimeError('ScriptTask fizzled! Return code: {}'.format(returncodes))

        return FWAction(stored_data=output)

    def _load_params(self, d):
        if d.get('stdin_file') and d.get('stdin_key'):
            raise ValueError("ScriptTask cannot process both a key and file as the standard in!")

        self.use_shell = d.get('use_shell', True)

        m_script = d['script']
        if (sys.version_info < (3, 0) and isinstance(m_script, unicode)) or\
                isinstance(m_script, str):
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
            raise ValueError("ScriptTask cannot both FIZZLE and DEFUSE a bad returncode!")

    @classmethod
    def from_str(cls, shell_cmd, parameters=None):
        parameters = parameters if parameters else {}
        parameters['script'] = [shell_cmd]
        parameters['use_shell'] = True
        return ScriptTask(parameters)
