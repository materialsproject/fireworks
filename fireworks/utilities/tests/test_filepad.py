import os
import unittest

from fireworks.utilities.filepad import FilePad

module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))


class FilePadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chgcar_file = os.path.join(module_dir, "CHGCAR.Fe3O4")
        self.fp = FilePad.auto_load()
        self.identifier = "Fe3O4"

    def test_add_file(self) -> None:
        gfs_id, file_identifier = self.fp.add_file(self.chgcar_file, identifier=self.identifier)
        assert file_identifier == self.identifier
        assert gfs_id is not None

    def test_add_file_with_no_identifier(self) -> None:
        gfs_id, file_identifier = self.fp.add_file(self.chgcar_file)
        assert gfs_id is not None
        assert file_identifier == gfs_id

    def test_get_file(self) -> None:
        _, file_identifier = self.fp.add_file(self.chgcar_file, identifier="xxx", metadata={"author": "Kiran Mathew"})
        file_contents, doc = self.fp.get_file(file_identifier)
        with open(self.chgcar_file) as file:
            assert file_contents == file.read().encode()

        assert doc["identifier"] == file_identifier
        assert doc["metadata"]["author"] == "Kiran Mathew"
        abspath = os.path.abspath(self.chgcar_file)
        assert doc["original_file_name"] == os.path.basename(abspath)
        assert doc["original_file_path"] == abspath
        assert doc["compressed"] is True

    def test_delete_file(self) -> None:
        _, file_identifier = self.fp.add_file(self.chgcar_file)
        self.fp.delete_file(file_identifier)
        contents, doc = self.fp.get_file(file_identifier)
        assert contents is None
        assert doc is None

    def test_update_file(self) -> None:
        gfs_id, _ = self.fp.add_file(self.chgcar_file, identifier="test_update_file")
        old_id, new_id = self.fp.update_file("test_update_file", self.chgcar_file)
        assert old_id == gfs_id
        assert new_id != gfs_id
        assert not self.fp.gridfs.exists(old_id)

    def test_update_file_by_id(self) -> None:
        gfs_id, _ = self.fp.add_file(self.chgcar_file, identifier="some identifier")
        old, new = self.fp.update_file_by_id(gfs_id, self.chgcar_file)
        assert old == gfs_id
        assert new != gfs_id

    def tearDown(self) -> None:
        self.fp.reset()
