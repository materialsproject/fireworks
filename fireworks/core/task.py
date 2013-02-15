#!/usr/bin/env python

'''
TODO: add docs
'''
import subprocess
import shlex


__author__ = 'Anubhav Jain'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Feb 15, 2013'


class TaskBase():
    '''
    TODO: add docs
    '''
    
    def init(self, parameters):
        self.parameters = parameters
        
    def register_lp(self, launchpad):
        self.launchpad = launchpad
    
    # TODO: add previous outputs and FireWork to this?
    def run_task(self, fw, previous_output):
        '''
        returns an output
        :param fw:
        :param previous_output:
        '''
        raise NotImplementedError('Need to implement run_task!')
    
    # TODO: add a write to log method
    
# TODO: Task for committing a file to DB?
# TODO: add checkpoint function

class SubprocessTask(TaskBase):
    
    _fw_name = "Subprocess Task"
    
    #TODO: warn that the shell option is DANGEROUS!
    # set shell to BASH, allow CSH option
    #TODO: use shlex!
    
    def init(self, parameters):
        # dynamic parameters
        
        # stdout = dict with key and/or file parameter, or "_PIPE".
        # stderr = stdout plus _MERGE
        
        self.stdout_file = parameters.get('stdout_file', None)
        self.stdout_key = parameters.get('stdout_key', '_stdout')
        self.stdout = parameters.get('stdout', subprocess.PIPE)
        
        self.stderr_file = parameters.get('stderr_file', None)
        self.stderr_key = parameters.get('stderr_key', '_stderr')
        self.stderr = parameters.get('stderr', subprocess.PIPE)
        
        self.returncode_key = parameters.get('returncode_key', '_returncode')
            
        self.stdin_file = parameters.get('stdin_file', None)
        self.stdin_key = parameters.get('stdin_key', None)
        if self.stdin_file and self.stdin_key:
            raise ValueError("Subprocess Task cannot process both a key and file as the standard in!")
        
        self.use_shlex = parameters.get('use_shlex', True)
        
        self.script = parameters['script']
        
        if self.use_shlex and isinstance(self.script, basestring):
            self.script = shlex.split(self.script)
        
        self.use_shell = parameters.get('use_shell', False)
        self.shell_exe = parameters.get('shell_exe', None)
        
    def run_task(self, fw, prev_output):
        
        output = {}
        
        # get the standard in
        self.stdin = None
        if self.stdin_file:
            with open(self.stdin_file) as f:
                self.stdin = f.read()
        elif self.stdin_key:
            self.stdin = subprocess.PIPE
        
        # run the program
        p = subprocess.Popen(self.script, executable=self.shell_exe, stdin=self.stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=self.use_shell)
        
        # communicate in the standard in and get back the standard out and returncode
        (stdout, stderr) = p.communicate(prev_output[self.stdin_key])
        returncode = p.returncode
        
        # write out the output, error files if specified
        if self.stdout_file:
            with open(self.stdout_file, 'w+') as f:
                f.write(stdout)
        
        if self.stderr_file:
            with open(self.stderr_file, 'w+') as f:
                f.write(stderr)
        
        # write the output keys
        if self.stdout_key:
            output[self.stdout_key] = stdout
        
        if self.stderr_key:
            output[self.stderr_key] = stderr
        
        if self.returncode_key:
            output[self.returncode_key] = returncode