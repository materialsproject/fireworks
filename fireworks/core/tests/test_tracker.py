#!/usr/bin/env python

"""
Tracker unitest
"""

from __future__ import division

__author__ = "Bharat medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Bharat medasani"
__email__ = "mbkumar@gmail.com"
__date__ = "8/12/14"

import unittest
import os
import glob
import shutil
import sys
import argparse

from fireworks.core.firework import FireWork, Tracker, FWorker
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket
from fireworks.scripts.lpad_run import track_fws
from fireworks.user_objects.firetasks.script_task import ScriptTask
from fireworks.user_objects.firetasks.templatewriter_task import TemplateWriterTask

TESTDB_NAME = 'fireworks_unittest'
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class TrackerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lp = None
        cls.fworker = FWorker()
        try:
            cls.lp = LaunchPad(name=TESTDB_NAME, strm_lvl='ERROR')
            cls.lp.reset(password=None,require_password=False)
        except:
            raise unittest.SkipTest("MongoDB is not running in localhost:27017! Skipping tests.")

    @classmethod
    def tearDown(self):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        self.old_wd = os.getcwd()

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for i in glob.glob(os.path.join(MODULE_DIR,'launcher_*')):
            shutil.rmtree(i)

    def _teardown(self, dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def test_tracker(self):

        dest1 = os.path.join(MODULE_DIR, 'inputs.txt')
        dest2 = os.path.join(MODULE_DIR, 'words.txt')
        dest3 = os.path.join(MODULE_DIR,'test_launchpad.yaml')
        dest4 = os.path.join(MODULE_DIR,'tmp_log.txt')
        self._teardown([dest1,dest2])
        fts =  []
        try:
            tracker1 = Tracker(dest2,nlines=2)
            tracker2 = Tracker(dest1,nlines=2)
            for i in range(5,100):
                ft1 = TemplateWriterTask({'context':{'opt1':i,'opt2':'fast method'},
                                          'template_file':'simple_template.txt',
                                          'output_file': dest1})
                ft2 = ScriptTask.from_str('echo "' + str(i) + '" >> ' + dest2, {'store_stdout':True})
                fts += [ft1, ft2]

            fw = FireWork(fts, spec={'_trackers':[tracker1,tracker2]}, fw_id=20, name='test_fw')
            self.lp.add_wf(fw)
            self.lp.to_file(dest3)
            fw_ids = self.lp.get_fw_ids(query={'name':'test_fw'})
            #print 'length', len(fw_ids)
            fw_id = fw_ids[0]
            #print fw_id
            launch_rocket(self.lp, self.fworker)

            fw_id_args = ["-i", "--fw_id"]
            fw_id_kwargs = {"type": int, "nargs": "+", "help": "fw_id"}

            state_args = ['-s', '--state']
            state_kwargs = {"type": str.upper, "help": "Select by state.",
                            "choices": FireWork.STATE_RANKS.keys()}
            disp_args = ['-d', '--display_format']
            disp_kwargs = {"type": str, "help": "Display format.", "default": "less",
                            "choices": ["all", "more", "less", "ids", "count"]}

            query_args = ["-q", "--query"]
            query_kwargs = {"help": 'Query (enclose pymongo-style dict in '
                            'single-quotes, e.g. \'{"state":"COMPLETED"}\')'}

            parser = argparse.ArgumentParser()
            parser.add_argument(*fw_id_args, **fw_id_kwargs)
            parser.add_argument('-n', '--name')
            parser.add_argument(*state_args, **state_kwargs)
            parser.add_argument(*query_args, **query_kwargs)
            parser.add_argument('-c', '--include', nargs="+",
                                        help='only include these files in the report')
            parser.add_argument('-x', '--exclude', nargs="+",
                                        help='exclude these files from the report')
            parser.add_argument('--launchpad_file', default=dest3)

            args = parser.parse_args('-i 1'.split())
            with open(dest4,'w') as fp:
                sys.stdout = fp
                sys.stderr = fp
                track_fws(args)
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            expected_output_string = "# FW id: 1, FW name: test_fw\n"+\
                         "## Launch id: 1\n### Filename: "+dest2+"\n"+\
                         "98\n99\n## Launch id: 1\n"+\
                         "### Filename: "+dest1+"\noption1 = 99\n"+\
                         "option2 = fast method\n"
            #print expected_output_string
            with open(dest4) as fp:
                output = fp.read()
                #print output
                self.assertEqual(output,expected_output_string)

        finally:
            self._teardown([dest1,dest2,dest3,dest4])

    def test_tracker_failed_fw(self):

        dest1 = os.path.join(MODULE_DIR, 'inputs.txt')
        dest2 = os.path.join(MODULE_DIR, 'words.txt')
        dest3 = os.path.join(MODULE_DIR,'tmp_log.txt')
        dest4 = os.path.join(MODULE_DIR,'test_launchpad.yaml')
        #print 'MODULE_DIR', MODULE_DIR
        #print dest1, dest2, dest3, dest4
        self._teardown([dest1,dest2])
        fts =  []
        try:
            tracker1 = Tracker(dest2,nlines=2)
            tracker2 = Tracker(dest1,nlines=2)
            for i in range(5,50):
                ft1 = TemplateWriterTask({'context':{'opt1':i,'opt2':'fast method'},
                                          'template_file':'simple_template.txt',
                                          'output_file':dest1})
                ft2 = ScriptTask.from_str('echo "' + str(i) + '" >> '+ dest2,
                                          {'store_stdout':True})
                fts += [ft1, ft2]
            fts.append(ScriptTask.from_str('cat 4 >> ' + dest2))
            for i in range(51,100):
                ft1 = TemplateWriterTask({'context':{'opt1':i,'opt2':'fast method'},
                                          'template_file':'simple_template.txt',
                                          'output_file':dest1})
                ft2 = ScriptTask.from_str('echo "' + str(i) + '" >> ' + dest2)
                fts += [ft1, ft2]

            fw = FireWork(fts, spec={'_trackers':[tracker1,tracker2]}, fw_id=21, name='test_fw')
            self.lp.add_wf(fw)
            self.lp.to_file(dest4)
            fw_id = self.lp.get_fw_ids(query={'name':'test_fw'})[0]
            #print fw_id
            try:
                launch_rocket(self.lp, self.fworker)
            except:
                #print 'error in running fw'
                pass

            fw_id_args = ["-i", "--fw_id"]
            fw_id_kwargs = {"type": int, "nargs": "+", "help": "fw_id"}

            state_args = ['-s', '--state']
            state_kwargs = {"type": str.upper, "help": "Select by state.",
                            "choices": FireWork.STATE_RANKS.keys()}
            disp_args = ['-d', '--display_format']
            disp_kwargs = {"type": str, "help": "Display format.", "default": "less",
                            "choices": ["all", "more", "less", "ids", "count"]}

            query_args = ["-q", "--query"]
            query_kwargs = {"help": 'Query (enclose pymongo-style dict in '
                            'single-quotes, e.g. \'{"state":"COMPLETED"}\')'}

            parser = argparse.ArgumentParser()
            parser.add_argument(*fw_id_args, **fw_id_kwargs)
            parser.add_argument('-n', '--name')
            parser.add_argument(*state_args, **state_kwargs)
            parser.add_argument(*query_args, **query_kwargs)
            parser.add_argument('-c', '--include', nargs="+",
                                        help='only include these files in the report')
            parser.add_argument('-x', '--exclude', nargs="+",
                                        help='exclude these files from the report')
            parser.add_argument('--launchpad_file', default=dest4)

            args = parser.parse_args('-i 1'.split())
            with open(dest3,'w') as fp:
                sys.stdout = fp
                sys.stderr = fp
                try:
                    track_fws(args)
                except:
                    pass
                    #print 'error here'
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            expected_output_string = "# FW id: 1, FW name: test_fw\n"+\
                         "## Launch id: 1\n### Filename: "+dest2+"\n"+\
                         "48\n49\n## Launch id: 1\n"+\
                         "### Filename: "+dest1+"\noption1 = 49\n"+\
                         "option2 = fast method\n"
            #print expected_output_string
            with open(dest3) as fp:
                output = fp.read()
                #print output
                self.assertEqual(output,expected_output_string)

        finally:
            self._teardown([dest1,dest2,dest3,dest4])
            pass


if __name__ == '__main__':
    unittest.main()
