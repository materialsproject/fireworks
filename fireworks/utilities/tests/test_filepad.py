# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

import os
import unittest

from fireworks.utilities.filepad import FilePad

module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class FilePadTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.chgcar_file = os.path.join(module_dir, "CHGCAR.Fe3O4")
        cls.fs = FilePad.auto_load()
        cls.label = "fe3o4"

    def test_add_file(self):
        file_id, file_label = self.fs.add_file(self.chgcar_file, label=self.label)
        self.assertEqual(file_label, self.label)
        self.assertIsNotNone(file_id)

    def test_get_file(self):
        file_id, file_label = self.fs.add_file(self.chgcar_file, label=self.label)
        file_contents, doc = self.fs.get_file(self.label)
        self.assertEqual(file_contents, open(self.chgcar_file,"r").read().encode())
        self.assertEqual(doc["label"], self.label)

    def test_delete_file(self):
        file_id, file_label = self.fs.add_file(self.chgcar_file, label=self.label)
        self.fs.delete_file(self.label)
        x = self.fs.get_file(self.label)
        self.assertIsNone(x)

    def test_update_file_by_id(self):
        file_id, file_label = self.fs.add_file(self.chgcar_file, label=self.label)
        old, new = self.fs.update_file_by_id(file_id, self.chgcar_file, delete_old=False)
        self.assertEqual(old, file_id)
        self.assertNotEqual(new, file_id)


if __name__ == "__main__":
    unittest.main()
