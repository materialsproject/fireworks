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
        self.identifier = "Fe3O4"

    def test_add_file(self):
        gfs_id, file_identifier = self.fp.add_file(self.chgcar_file, identifier=self.identifier)
        self.assertEqual(file_identifier, self.identifier)
        self.assertIsNotNone(gfs_id)

    def test_add_file_with_no_identifier(self):
        gfs_id, file_identifier = self.fp.add_file(self.chgcar_file)
        self.assertIsNotNone(gfs_id)
        self.assertEqual(file_identifier, gfs_id)

    def test_get_file(self):
        _, file_identifier = self.fp.add_file(self.chgcar_file, identifier="xxx", metadata={"author": "Kiran Mathew"})
        file_contents, doc = self.fp.get_file(file_identifier)
        self.assertEqual(file_contents, open(self.chgcar_file, "r").read().encode())
        self.assertEqual(doc["identifier"], file_identifier)
        self.assertEqual(doc["metadata"]["author"], "Kiran Mathew")
        abspath = os.path.abspath(self.chgcar_file)
        self.assertEqual(doc["original_file_name"], os.path.basename(abspath))
        self.assertEqual(doc["original_file_path"], abspath)
        self.assertEqual(doc["compressed"], True)

    def test_delete_file(self):
        _, file_identifier = self.fp.add_file(self.chgcar_file)
        self.fp.delete_file(file_identifier)
        contents, doc = self.fp.get_file(file_identifier)
        self.assertIsNone(contents)
        self.assertIsNone(doc)

    def test_update_file(self):
        gfs_id, _ = self.fp.add_file(self.chgcar_file, identifier="test_update_file")
        old_id, new_id = self.fp.update_file("test_update_file", self.chgcar_file)
        self.assertEqual(old_id, gfs_id)
        self.assertNotEqual(new_id, gfs_id)
        self.assertFalse(self.fp.gridfs.exists(old_id))

    def test_update_file_by_id(self):
        gfs_id, _ = self.fp.add_file(self.chgcar_file, identifier="some identifier")
        old, new = self.fp.update_file_by_id(gfs_id, self.chgcar_file)
        self.assertEqual(old, gfs_id)
        self.assertNotEqual(new, gfs_id)

    def tearDown(self):
        self.fp.reset()


if __name__ == "__main__":
    unittest.main()
