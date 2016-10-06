# coding: utf-8

from __future__ import unicode_literals
import copy

"""
This module implements a CommonAdaptor that supports standard PBS and SGE
queues.
"""
import getpass
import os
import stat
import re
import subprocess
from fireworks.queue.queue_adapter import QueueAdapterBase, Command
from fireworks.utilities.fw_serializers import serialize_fw
from fireworks.utilities.fw_utilities import log_exception, log_fancy

__author__ = 'Anubhav Jain, Michael Kocher, Shyue Ping Ong, David Waroquiers, Felix Brockherde'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class CommonAdapter(QueueAdapterBase):
    """
    An adapter that works on most PBS (including derivatives such as
    TORQUE), SGE, and SLURM queues.
    """
    _fw_name = 'CommonAdapter'

    default_q_commands = {
        "PBS": {"submit_cmd": "qsub", "status_cmd": "qstat"},
        "SGE": {"submit_cmd": "qsub", "status_cmd": "qstat"},
        "Cobalt": {"submit_cmd": "qsub", "status_cmd": "qstat"},
        "SLURM": {"submit_cmd": "sbatch", "status_cmd": "squeue"},
        "LoadLeveler": {"submit_cmd": "llsubmit", "status_cmd": "llq"},
        "LoadSharingFacility": {"submit_cmd": "bsub", "status_cmd": "bjobs"}
    }

    def __init__(self, q_type, q_name=None, template_file=None, **kwargs):
        """
        :param q_type: The type of queue. Right now it should be either PBS,
                       SGE, SLURM, Cobalt or LoadLeveler.
        :param q_name: A name for the queue. Can be any string.
        :param template_file: The path to the template file. Leave it as
                              None (the default) to use Fireworks' built-in
                              templates for PBS and SGE, which should work
                              on most queues.
        :param **kwargs: Series of keyword args for queue parameters.
        """
        if q_type not in CommonAdapter.default_q_commands:
            raise ValueError(
                "{} is not a supported queue type. "
                "CommonAdaptor supports {}".format(
                    q_type, list(self.default_q_commands.keys())))
        self.q_type = q_type
        self.template_file = os.path.abspath(template_file) if template_file is not None else \
            CommonAdapter._get_default_template_file(q_type)
        self.q_name = q_name or q_type
        self.update(dict(kwargs))

        self.q_commands = copy.deepcopy(CommonAdapter.default_q_commands)
        if '_q_commands_override' in self:
            self.q_commands[self.q_type].update(self["_q_commands_override"])

    def _parse_jobid(self, output_str):
        if self.q_type == "SLURM":
            for l in output_str.split("\n"):
                if l.startswith("Submitted batch job"):
                    return int(l.split()[-1])
        if self.q_type == "LoadLeveler":
            # Load Leveler: "llsubmit: The job "abc.123" has been submitted"
            re_string = r"The job \"(.*?)\" has been submitted"
        elif self.q_type == "Cobalt":
            # 99% of the time you just get:
            # Cobalt: "199768"
            # but there's a version that also includes project and queue
            # information on preceeding lines and both of those  might 
            # contain a number in any position.
            re_string = r"(\b\d+\b)"
        else:
            # PBS: "1234.whatever",
            # SGE: "Your job 44275 ("jobname") has been submitted"
            # Cobalt: "199768"
            re_string = r"(\d+)"
        m = re.search(re_string, output_str)
        if m:
            return m.group(1)
        raise RuntimeError("Unable to parse jobid")

    def _get_status_cmd(self, username):
        status_cmd = [self.q_commands[self.q_type]["status_cmd"]]

        if self.q_type == 'SLURM':
            # by default, squeue lists pending and running jobs
            # -p: filter queue (partition)
            # -h: no header line
            # -o: reduce output to user only (shorter string to parse)
            status_cmd.extend(['-o "%u"', '-u', username, '-h'])
            if 'queue' in self and self['queue']:
                status_cmd.extend(['-p', self['queue']])
        elif self.q_type == "LoadSharingFacility":
            #use no header and the wide format so that there is one line per job, and display only running and pending jobs
            status_cmd.extend(['-p','-r','-o', 'jobID user queue', '-noheader', '-u', username])
        elif self.q_type == "Cobalt":
            header="JobId:User:Queue:Jobname:Nodes:Procs:Mode:WallTime:State:RunTime:Project:Location"
            status_cmd.extend(['--header', header, '-u', username])
        elif self.q_type == 'SGE':
            status_cmd.extend(['-q', self['queue'], '-u', username])
        else:
            status_cmd.extend(['-u', username])

        return status_cmd

    def _parse_njobs(self, output_str, username):
        # TODO: what if username is too long for the output and is cut off?

        # WRS: I may come back to this after confirming that Cobalt
        #      strictly follows the PBS standard and replace the spliting
        #      with a regex that would solve length issues

        if self.q_type == 'SLURM':
            # subtract one due to trailing '\n' and split behavior
            return len(output_str.split('\n'))-1

        if self.q_type == "LoadLeveler":
            if 'There is currently no job status to report' in output_str:
                return 0
            else:
                # last line is: "1 job step(s) in query, 0 waiting, ..."
                return int(output_str.split('\n')[-2].split()[0])
        if self.q_type == "LoadSharingFacility":
            #Just count the number of lines
            return len(output_str.split('\n'))
        if self.q_type == "SGE":
            # want only lines that include username;
            # this will exclude e.g. header lines
            return len([l for l in output_str.split('\n') if username in l])

        count = 0
        for l in output_str.split('\n'):
            if l.lower().startswith("job"):
                if self.q_type == "Cobalt":
                    # Cobalt capitalzes headers
                    l=l.lower()
                header = l.split()
                if self.q_type == "PBS":
                    #PBS has a ridiculous two word "Job ID" in header
                    state_index = header.index("S") - 1
                    queue_index = header.index("Queue") - 1
                else:
                    state_index = header.index("state")
                    queue_index = header.index("queue")
            if username in l:
                toks = l.split()
                if toks[state_index] != "C":
                    # note: the entire queue name might be cutoff from the output if long queue name
                    # so we are only ensuring that our queue matches up until cutoff point
                    if "queue" in self and self["queue"][0:len(toks[queue_index])] in toks[queue_index]:
                        count += 1

        return count

    def submit_to_queue(self, script_file):
        """
        submits the job to the queue and returns the job id

        :param script_file: (str) name of the script file to use (String)
        :return: (int) job_id
        """
        if not os.path.exists(script_file):
            raise ValueError(
                'Cannot find script file located at: {}'.format(
                    script_file))

        queue_logger = self.get_qlogger('qadapter.{}'.format(self.q_name))
        submit_cmd = self.q_commands[self.q_type]["submit_cmd"]
        # submit the job
        try:
            if self.q_type == "Cobalt":
                # Cobalt requires scripts to be executable
                os.chmod(script_file,stat.S_IRWXU|stat.S_IRGRP|stat.S_IXGRP)
            cmd = [submit_cmd, script_file]
            #For most of the queues handled by common_adapter, it's best to simply submit the file name
            #as an argument.  LoadSharingFacility doesn't handle the header section (queue name, nodes, etc)
            #when taking file arguments, so the file needs to be passed as stdin to make it work correctly.
            if self.q_type == 'LoadSharingFacility':
                with open(script_file, 'r') as inputFile:
                    p = subprocess.Popen([submit_cmd],stdin=inputFile,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            else:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.wait()

            # grab the returncode. PBS returns 0 if the job was successful
            if p.returncode == 0:
                try:
                    job_id = self._parse_jobid(p.stdout.read().decode())
                    queue_logger.info(
                        'Job submission was successful and job_id is {}'.format(
                            job_id))
                    return job_id
                except Exception as ex:
                    # probably error parsing job code
                    log_exception(queue_logger,
                                  'Could not parse job id following {} due to error {}...'
                                  .format(submit_cmd, str(ex)))
            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = [
                    'Error in job submission with {n} file {f} and cmd {c}'.format(
                        n=self.q_name, f=script_file, c=cmd),
                    'The error response reads: {}'.format(p.stderr.read())]
                log_fancy(queue_logger, msgs, 'error')

        except Exception as ex:
            # random error, e.g. no qsub on machine!
            log_exception(queue_logger,
                          'Running the command: {} caused an error...'
                          .format(submit_cmd))

    def get_njobs_in_queue(self, username=None):
        """
        returns the number of jobs currently in the queu efor the user

        :param username: (str) the username of the jobs to count (default is to autodetect)
        :return: (int) number of jobs in the queue
        """
        queue_logger = self.get_qlogger('qadapter.{}'.format(self.q_name))

        # initialize username
        if username is None:
            username = getpass.getuser()

        # run qstat
        qstat = Command(self._get_status_cmd(username))
        p = qstat.run(timeout=5)

        # parse the result
        if p[0] == 0:
            njobs = self._parse_njobs(p[1], username)
            queue_logger.info(
                'The number of jobs currently in the queue is: {}'.format(
                    njobs))
            return njobs

        # there's a problem talking to qstat server?
        msgs = ['Error trying to get the number of jobs in the queue',
                'The error response reads: {}'.format(p[2])]
        log_fancy(queue_logger, msgs, 'error')
        return None

    @staticmethod
    def _get_default_template_file(q_type):
        return os.path.join(os.path.dirname(__file__), '{}_template.txt'.format(q_type))

    @serialize_fw
    def to_dict(self):
        d = dict(self)
        # _fw_* names are used for the specific instance variables.
        d["_fw_q_type"] = self.q_type
        if self.q_name != self.q_type:
            d["_fw_q_name"] = self.q_name
        if self.template_file != CommonAdapter._get_default_template_file(self.q_type):
            d["_fw_template_file"] = self.template_file
        return d

    @classmethod
    def from_dict(cls, m_dict):
        return cls(
            q_type=m_dict["_fw_q_type"],
            q_name=m_dict.get("_fw_q_name"),
            template_file=m_dict.get("_fw_template_file"),
            **{k: v for k, v in m_dict.items() if not k.startswith("_fw")})
