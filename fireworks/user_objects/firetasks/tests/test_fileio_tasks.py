# coding: utf-8

from __future__ import unicode_literals

__author__ = 'Shyue Ping Ong'
__copyright__ = 'Copyright 2013, The Materials Project'
__version__ = '0.1'
__maintainer__ = 'Shyue Ping Ong'
__email__ = 'ongsp@ucsd.edu'
__date__ = '1/6/14'

import unittest
import os

from fireworks.user_objects.firetasks.fileio_tasks import FileWriteTask, \
    CompressDirTask, ArchiveDirTask, DecompressDirTask
from fireworks.utilities.fw_serializers import load_object_from_file


module_dir = os.path.abspath(os.path.dirname(__file__))


class FileWriteDeleteTest(unittest.TestCase):

    def test_init(self):
        t = FileWriteTask(files_to_write="hello")
        t = FileWriteTask({"files_to_write": "hello"})
        self.assertRaises(ValueError, FileWriteTask)

    def test_run(self):
        t = load_object_from_file(os.path.join(module_dir, "write.yaml"))
        t.run_task({})
        for i in range(2):
            self.assertTrue(os.path.exists("myfile{}".format(i + 1)))

        #Use delete task to remove the files created.
        t = load_object_from_file(os.path.join(module_dir, "delete.yaml"))
        t.run_task({})
        for i in range(2):
            self.assertFalse(os.path.exists("myfile{}".format(i + 1)))


class CompressDecompressArchiveDirTest(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        os.chdir(module_dir)

    def test_compress_dir(self):
        c = CompressDirTask(compression="gz")
        c.run_task({})
        self.assertTrue(os.path.exists("delete.yaml.gz"))
        self.assertFalse(os.path.exists("delete.yaml"))
        c = DecompressDirTask()
        c.run_task({})
        self.assertFalse(os.path.exists("delete.yaml.gz"))
        self.assertTrue(os.path.exists("delete.yaml"))

    def test_archive_dir(self):
        a = ArchiveDirTask(base_name="archive", format="gztar")
        a.run_task({})
        self.assertTrue(os.path.exists("archive.tar.gz"))
        os.remove("archive.tar.gz")

    def tearDown(self):
        os.chdir(self.cwd)


if __name__ == '__main__':
    unittest.main()
