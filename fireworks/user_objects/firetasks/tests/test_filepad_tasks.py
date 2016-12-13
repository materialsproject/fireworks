# coding: utf-8

from __future__ import unicode_literals

__author__ = 'Kiran Mathew'

import unittest
import os

from fireworks.user_objects.firetasks.filepad_tasks import AddFilesTask, DeleteFilesTask, GetFilesTask
from fireworks.utilities.filepad import FilePad


module_dir = os.path.abspath(os.path.dirname(__file__))


class FilePadTasksTest(unittest.TestCase):

    def setUp(self):
        self.paths = [os.path.join(module_dir, "write.yaml"), os.path.join(module_dir, "delete.yaml")]
        self.labels = ["write", "delete"]
        self.fp = FilePad.auto_load()

    def test_addfilestask_run(self):
        t = AddFilesTask(paths=self.paths, labels=self.labels)
        t.run_task({})
        write_file_contents, wdoc = self.fp.get_file("write")
        self.assertEqual(write_file_contents, open(self.paths[0], "r").read().encode())
        del_file_contents, wdoc = self.fp.get_file("delete")
        self.assertEqual(del_file_contents, open(self.paths[1], "r").read().encode())

    def test_deletefilestask_run(self):
        t = DeleteFilesTask(labels=self.labels)
        t.run_task({})
        file_contents, doc = self.fp.get_file("write")
        self.assertIsNone(file_contents)
        self.assertIsNone(doc)
        file_contents, doc = self.fp.get_file("delete")
        self.assertIsNone(file_contents)
        self.assertIsNone(doc)

    def test_getfilestask_run(self):
        t = AddFilesTask(paths=self.paths, labels=self.labels)
        t.run_task({})
        dest_dir = os.path.abspath(".")
        labels = ["write"]
        new_file_names = ["write_2.yaml"]
        t = GetFilesTask(labels=labels, dest_dir=dest_dir, new_file_names=new_file_names)
        t.run_task({})
        write_file_contents, wdoc = self.fp.get_file("write")
        self.assertEqual(write_file_contents,
                         open(os.path.join(dest_dir, new_file_names[0]), "r").read().encode())
        os.remove(os.path.join(dest_dir, new_file_names[0]))

    def tearDown(self):
        self.fp.reset()


if __name__ == '__main__':
    unittest.main()
