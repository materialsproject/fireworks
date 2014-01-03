#!/usr/bin/env python

"""
This module implements a CommonAdaptor that supports standard PBS and SGE
queues.
"""
import getpass
import os
import re
import subprocess
from fireworks.queue.queue_adapter import QueueAdapterBase, Command
from fireworks.utilities.fw_serializers import serialize_fw
from fireworks.utilities.fw_utilities import log_exception, log_fancy

__author__ = 'Anubhav Jain, Michael Kocher'
__copyright__ = 'Copyright 2012, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Anubhav Jain'
__email__ = 'ajain@lbl.gov'
__date__ = 'Dec 12, 2012'


class CommonAdapter(QueueAdapterBase):
    """
    A PBS adapter that works on most PBS (including derivatives such as
    TORQUE) and SGE queues.
    """
    _fw_name = 'CommonAdapter'
    submit_cmd = 'qsub'
    defaults = {}
    default_template_file = os.path.join(os.path.dirname(__file__),
                                         '{}_template.txt')
    supported_q_types = ["PBS", "SGE"]

    def __init__(self, q_type, q_name, template_file=None, **kwargs):
        """
        :param q_type: The type of queue. Right now it should be either PBS
                       or SGE.
        :param q_name: A name for the queue. Can be any string.
        :param template_file: The path to the template file. Leave it as
                              None (the default) to use Fireworks' built-in
                              templates for PBS and SGE, which should work
                              on most queues.
        :param **kwargs: Series of keyword args for queue parameters.
        """
        if q_type not in CommonAdapter.supported_q_types:
            raise ValueError(
                "{} is not a supported queue type. "
                "CommonAdaptor supports {}".format(q_type,
                                                   CommonAdapter.supported_q_types))
        self.q_type = q_type
        self.template_file = os.path.abspath(template_file) \
            if template_file is not None \
            else CommonAdapter.default_template_file.format(self.q_type)
        self.q_name = q_name
        self.update(dict(kwargs))

    def _parse_jobid(self, output_str):
        #This should work regardless of PBS or SGE.
        #PBS returns somehting like 1234.whatever
        #SGE returns something like "Your job 44275 ("O3") has been submitted"
        #In both cases, the first series of integers is the jobid.
        m = re.search("(\d+)", output_str)
        if m:
            return m.group(1)
        raise RuntimeError("Unable to parse jobid")

    def _get_status_cmd(self, username):
        # Removed -a. Not sure why it was necessary since it seems to give
        # the same output. Simple -u works for both PBS and SGE.
        return ['qstat', '-u', username]

    def _parse_njobs(self, output_str, username):
        # lines should have this form
        # '1339044.sdb          username  queuename    2012-02-29-16-43  20460   --   --    --  00:20 C 00:09'
        # count lines that include the username in it
        count = 0
        for l in output_str.split('\n'):
            if l.lower().startswith("job"):
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
                if toks[state_index] != "C" and self["queue"] in toks[queue_index]:
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

        # submit the job
        try:
            cmd = [self.submit_cmd, script_file]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.wait()

            # grab the returncode. PBS returns 0 if the job was successful
            if p.returncode == 0:
                try:
                    job_id = self._parse_jobid(p.stdout.read())
                    queue_logger.info(
                        'Job submission was successful and job_id is {}'.format(
                            job_id))
                    return job_id
                except:
                    # probably error parsing job code
                    log_exception(queue_logger,
                                  'Could not parse job id following {}...'.format(
                                      self.submit_cmd))

            else:
                # some qsub error, e.g. maybe wrong queue specified, don't have permission to submit, etc...
                msgs = [
                    'Error in job submission with {n} file {f} and cmd {c}'.format(
                        n=self.q_name, f=script_file, c=cmd),
                    'The error response reads: {}'.format(p.stderr.read())]
                log_fancy(queue_logger, msgs, 'error')

        except:
            # random error, e.g. no qsub on machine!
            log_exception(queue_logger,
                          'Running the command: {} caused an error...'.format(
                              self.submit_cmd))

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

    @serialize_fw
    def to_dict(self):
        d = dict(self)
        #_fw names are used for the specific instance variables.
        d["_fw_q_type"] = self.q_type
        d["_fw_q_name"] = self.q_name
        # Use None if it is the default template. This keeps the serialized
        # dict simple and also makes it more portable across multiple
        # installations if a template file was not actually specified.
        d["_fw_template_file"] = self.template_file if self\
            .template_file != CommonAdapter.default_template_file.format(self.q_type) else None
        return d

    @classmethod
    def from_dict(cls, m_dict):
        return cls(
            q_type=m_dict["_fw_q_type"],
            q_name=m_dict["_fw_q_name"],
            template_file=m_dict.get("_fw_template_file", None),
            **{k: v for k, v in m_dict.items() if not k.startswith("_fw")})