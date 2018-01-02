# coding: utf-8

from __future__ import unicode_literals

"""
Tracker unitest
"""


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

from fireworks.core.firework import Firework, Tracker, FWorker, Workflow
from fireworks.core.launchpad import LaunchPad
from fireworks.core.rocket_launcher import launch_rocket
from fireworks.features.multi_launcher import launch_multiprocess
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
    def tearDownClass(cls):
        if cls.lp:
            cls.lp.connection.drop_database(TESTDB_NAME)

    def setUp(self):
        self.old_wd = os.getcwd()
        self.dest1 = os.path.join(MODULE_DIR, 'numbers1.txt')
        self.dest2 = os.path.join(MODULE_DIR, 'numbers2.txt')

        self.tracker1 = Tracker(self.dest1,nlines=2)
        self.tracker2 = Tracker(self.dest2,nlines=2)

    def tearDown(self):
        self.lp.reset(password=None, require_password=False)
        if os.path.exists(os.path.join('FW.json')):
            os.remove('FW.json')
        os.chdir(self.old_wd)
        for i in glob.glob(os.path.join(MODULE_DIR,'launcher_*')):
            shutil.rmtree(i)

    @staticmethod
    def _teardown(dests):
        for f in dests:
            if os.path.exists(f):
                os.remove(f)

    def test_tracker(self):
        """
        Launch a workflow and track the files
        """
        self._teardown([self.dest1])
        try:
            fts =  []
            for i in range(5,100):
                ft = ScriptTask.from_str('echo "' + str(i) + '" >> ' + self.dest1, {'store_stdout':True})
                fts.append(ft)

            fw = Firework(fts, spec={'_trackers':[self.tracker1]}, fw_id=20, name='test_fw')
            self.lp.add_wf(fw)
            launch_rocket(self.lp, self.fworker)

            #print (self.tracker1.track_file())
            self.assertEqual('98\n99',self.tracker1.track_file())

        finally:
            self._teardown([self.dest1])

    def test_tracker_failed_fw(self):
        """
        Add a bad firetask to workflow and test the tracking
        """
        self._teardown([self.dest1])
        try:
            fts =  []
            for i in range(5,50):
                ft = ScriptTask.from_str('echo "' + str(i) + '" >> '+ self.dest1,
                                        {'store_stdout':True})
                fts.append(ft)
            fts.append(ScriptTask.from_str('cat 4 >> ' + self.dest1))
            for i in range(51,100):
                ft = ScriptTask.from_str('echo "' + str(i) + '" >> ' + self.dest1,
                                        {'store_stdout':True})
                fts.append(ft)

            fw = Firework(fts, spec={'_trackers':[self.tracker1]}, fw_id=21, name='test_fw')
            self.lp.add_wf(fw)

            try:
                print("===========================================")
                print("Bad rocket launched. The failure below is OK")
                print("===========================================")
                launch_rocket(self.lp, self.fworker)
            except:
                pass

            self.assertEqual('48\n49',self.tracker1.track_file())

        finally:
            self._teardown([self.dest1])

    def test_tracker_mlaunch(self):
        """
        Test the tracker for mlaunch
        """
        self._teardown([self.dest1,self.dest2])
        try:
            def add_wf(j, dest, tracker, name):
                fts = []
                for i in range(j,j+25):
                    ft = ScriptTask.from_str('echo "' + str(i) + '" >> '+ dest,
                                              {'store_stdout':True})
                    fts.append(ft)
                fw1 = Firework(fts, spec={'_trackers':[tracker]},
                               fw_id=j+1, name=name+'1')

                fts = []
                for i in range(j+25,j+50):
                    ft = ScriptTask.from_str('echo "' + str(i) + '" >> ' + dest,
                                              {'store_stdout':True})
                    fts.append(ft)
                fw2 = Firework(fts, spec={'_trackers':[tracker]},
                               fw_id=j+2, name=name+'2')
                wf = Workflow([fw1, fw2], links_dict={fw1:[fw2]})
                self.lp.add_wf(wf)

            add_wf(0, self.dest1, self.tracker1, 'a_test')
            add_wf(50, self.dest2, self.tracker2, 'b_test')

            try:
                launch_multiprocess(self.lp, self.fworker, 'ERROR',
                                    0, 2, 0, ppn=2)
            except:
                pass

            self.assertEqual('48\n49',self.tracker1.track_file())
            self.assertEqual('98\n99',self.tracker2.track_file())


        finally:
            self._teardown([self.dest1,self.dest2])
            pwd = os.getcwd()
            for ldir in glob.glob(os.path.join(pwd,'launcher_*')):
                shutil.rmtree(ldir)


if __name__ == '__main__':
    unittest.main()
