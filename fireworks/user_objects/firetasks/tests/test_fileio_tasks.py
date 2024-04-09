__author__ = "Shyue Ping Ong"
__copyright__ = "Copyright 2013, The Materials Project"
__maintainer__ = "Shyue Ping Ong"
__email__ = "ongsp@ucsd.edu"
__date__ = "1/6/14"

import os
import unittest

import pytest

from fireworks.user_objects.firetasks.fileio_tasks import (
    ArchiveDirTask,
    CompressDirTask,
    DecompressDirTask,
    FileWriteTask,
)
from fireworks.utilities.fw_serializers import load_object_from_file

module_dir = os.path.abspath(os.path.dirname(__file__))


class FileWriteDeleteTest(unittest.TestCase):
    def test_init(self) -> None:
        FileWriteTask(files_to_write="hello")
        FileWriteTask({"files_to_write": "hello"})
        with pytest.raises(RuntimeError):
            FileWriteTask()

    def test_run(self) -> None:
        t = load_object_from_file(os.path.join(module_dir, "write.yaml"))
        t.run_task({})
        for i in range(2):
            assert os.path.exists(f"myfile{i + 1}")

        # Use delete task to remove the files created.
        t = load_object_from_file(os.path.join(module_dir, "delete.yaml"))
        t.run_task({})
        for i in range(2):
            assert not os.path.exists(f"myfile{i + 1}")


class CompressDecompressArchiveDirTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cwd = os.getcwd()
        os.chdir(module_dir)

    def test_compress_dir(self) -> None:
        c = CompressDirTask(compression="gz")
        c.run_task({})
        assert os.path.exists("delete.yaml.gz")
        assert not os.path.exists("delete.yaml")
        c = DecompressDirTask()
        c.run_task({})
        assert not os.path.exists("delete.yaml.gz")
        assert os.path.exists("delete.yaml")

    def test_archive_dir(self) -> None:
        a = ArchiveDirTask(base_name="archive", format="gztar")
        a.run_task({})
        assert os.path.exists("archive.tar.gz")
        os.remove("archive.tar.gz")

    def tearDown(self) -> None:
        os.chdir(self.cwd)
