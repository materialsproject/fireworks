# coding: utf-8

from __future__ import division, print_function, unicode_literals, absolute_import

import os
import unittest

from fireworks.utilities.filepad import FilePad

module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class FilePadTest(unittest.TestCase):

    def setUp(self):
        self.chgcar_file = os.path.join(module_dir, "CHGCAR.Fe3O4")
        self.fp = FilePad.auto_load()
        self.label = "Fe3O4"

    def test_add_file(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file, label=self.label)
        self.assertEqual(file_label, self.label)
        self.assertIsNotNone(file_id)

    def test_add_file_with_no_label(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file)
        self.assertIsNotNone(file_id)
        self.assertEqual(file_label, file_id)

    def test_get_file(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file, label="xxx", metadata={"author": "Kiran Mathew"})
        file_contents, doc = self.fp.get_file(file_label)
        self.assertEqual(file_contents, open(self.chgcar_file, "r").read().encode())
        self.assertEqual(doc["label"], file_label)
        self.assertEqual(doc["metadata"]["author"], "Kiran Mathew")
        abspath = os.path.abspath(self.chgcar_file)
        self.assertEqual(doc["original_file_name"], os.path.basename(abspath))
        self.assertEqual(doc["original_file_path"], abspath)
        self.assertEqual(doc["compressed"], True)

    def test_delete_file(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file)
        self.fp.delete_file(file_label)
        contents, doc = self.fp.get_file(file_label)
        self.assertIsNone(contents)
        self.assertIsNone(doc)

    def test_update_file(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file, label="test_update_file")
        old_id, new_id = self.fp.update_file("test_update_file", self.chgcar_file)
        self.assertEqual(old_id, file_id)
        self.assertNotEqual(new_id, file_id)
        self.assertFalse(self.fp.gridfs.exists(old_id))

    def test_update_file_by_id(self):
        file_id, file_label = self.fp.add_file(self.chgcar_file, label="some label")
        old, new = self.fp.update_file_by_id(file_id, self.chgcar_file)
        self.assertEqual(old, file_id)
        self.assertNotEqual(new, file_id)

    def tearDown(self):
        self.fp.reset()


if __name__ == "__main__":
    unittest.main()
