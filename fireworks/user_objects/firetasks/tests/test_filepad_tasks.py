__author__ = "Kiran Mathew, Johannes Hoermann"

import os
import unittest

import pytest
from ruamel.yaml import YAML

from fireworks.user_objects.firetasks.filepad_tasks import (
    AddFilesTask,
    DeleteFilesTask,
    GetFilesByQueryTask,
    GetFilesTask,
)
from fireworks.utilities.filepad import FilePad

module_dir = os.path.abspath(os.path.dirname(__file__))


class FilePadTasksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.paths = [os.path.join(module_dir, "write.yaml"), os.path.join(module_dir, "delete.yaml")]
        self.identifiers = ["write", "delete"]
        self.fp = FilePad.auto_load()

    @pytest.mark.mongodb
    def test_addfilestask_run(self) -> None:
        t = AddFilesTask(paths=self.paths, identifiers=self.identifiers)
        t.run_task({})
        write_file_contents, _ = self.fp.get_file("write")
        with open(self.paths[0]) as f:
            assert write_file_contents == f.read().encode()
        del_file_contents, _ = self.fp.get_file("delete")
        with open(self.paths[1]) as f:
            assert del_file_contents == f.read().encode()

    def test_deletefilestask_run(self) -> None:
        t = DeleteFilesTask(identifiers=self.identifiers)
        t.run_task({})
        file_contents, doc = self.fp.get_file("write")
        assert file_contents is None
        assert doc is None
        file_contents, doc = self.fp.get_file("delete")
        assert file_contents is None
        assert doc is None

    @pytest.mark.mongodb
    def test_getfilestask_run(self) -> None:
        t = AddFilesTask(paths=self.paths, identifiers=self.identifiers)
        t.run_task({})
        dest_dir = os.path.abspath(".")
        identifiers = ["write"]
        new_file_names = ["write_2.yaml"]
        t = GetFilesTask(identifiers=identifiers, dest_dir=dest_dir, new_file_names=new_file_names)
        t.run_task({})
        write_file_contents, _ = self.fp.get_file("write")
        with open(os.path.join(dest_dir, new_file_names[0])) as f:
            assert write_file_contents == f.read().encode()
        os.remove(os.path.join(dest_dir, new_file_names[0]))

    @pytest.mark.mongodb
    @pytest.mark.skip(reason='fails after fixing the identical names with the next test')
    def test_getfilesbyquerytask_run(self) -> None:
        """Tests querying objects from FilePad by metadata."""
        t = AddFilesTask(paths=self.paths, identifiers=self.identifiers, metadata={"key": "value"})
        t.run_task({})
        dest_dir = os.path.abspath(".")
        new_file_names = ["test_file.yaml"]
        t = GetFilesByQueryTask(query={"metadata->key": "value"}, dest_dir=dest_dir, new_file_names=new_file_names)
        t.run_task({})
        test_file_contents, _ = self.fp.get_file("test_idenfifier")
        with open(os.path.join(dest_dir, new_file_names[0])) as file:
            assert test_file_contents == file.read().encode()
        os.remove(os.path.join(dest_dir, new_file_names[0]))

    @pytest.mark.mongodb
    def test_getfilesbyquerytask_run_some_identifier(self) -> None:
        """Tests querying objects from FilePad by metadata."""
        with open("original_test_file.txt", "w") as f:
            f.write("Some file with some content")
        t = AddFilesTask(paths=["original_test_file.txt"], identifiers=["some_identifier"], metadata={"key": "value"})
        t.run_task({})
        os.remove("original_test_file.txt")

        dest_dir = os.path.abspath(".")
        t = GetFilesByQueryTask(
            query={"metadata->key": "value"}, dest_dir=dest_dir, new_file_names=["queried_test_file.txt"]
        )
        t.run_task({})
        test_file_contents, _ = self.fp.get_file("some_identifier")
        with open(os.path.join(dest_dir, "queried_test_file.txt")) as f:
            assert test_file_contents == f.read().encode()
        os.remove(os.path.join(dest_dir, "queried_test_file.txt"))

    @pytest.mark.mongodb
    def test_getfilesbyquerytask_metafile_run(self) -> None:
        """Tests writing metadata to a yaml file."""
        with open("original_test_file.txt", "w") as f:
            f.write("Some file with some content")
        t = AddFilesTask(paths=["original_test_file.txt"], identifiers=["test_identifier"], metadata={"key": "value"})
        t.run_task({})
        os.remove("original_test_file.txt")

        dest_dir = os.path.abspath(".")
        t = GetFilesByQueryTask(
            query={"metadata->key": "value"},
            meta_file=True,
            meta_file_suffix=".meta.yaml",
            dest_dir=dest_dir,
            new_file_names=["queried_test_file.txt"],
        )
        t.run_task({})

        with open("queried_test_file.txt.meta.yaml") as f:
            yaml = YAML(typ="safe")
            metadata = yaml.load(f)
        assert metadata["key"] == "value"

        os.remove(os.path.join(dest_dir, "queried_test_file.txt"))
        os.remove(os.path.join(dest_dir, "queried_test_file.txt.meta.yaml"))

    def test_getfilesbyquerytask_ignore_empty_result_run(self) -> None:
        """Tests on ignoring empty results from FilePad query."""
        dest_dir = os.path.abspath(".")
        t = GetFilesByQueryTask(
            query={"metadata->key": "value"},
            fizzle_empty_result=False,
            dest_dir=dest_dir,
            new_file_names=["queried_test_file.txt"],
        )
        t.run_task({})
        # test successful if no exception raised

    def test_getfilesbyquerytask_raise_empty_result_run(self) -> None:
        """Tests on raising exception on empty results from FilePad query."""
        dest_dir = os.path.abspath(".")
        t = GetFilesByQueryTask(
            query={"metadata->key": "value"},
            fizzle_empty_result=True,
            dest_dir=dest_dir,
            new_file_names=["queried_test_file.txt"],
        )
        with pytest.raises(ValueError):
            t.run_task({})
        # test successful if exception raised

    @pytest.mark.mongodb
    def test_getfilesbyquerytask_ignore_degenerate_file_name(self) -> None:
        """Tests on ignoring degenerate file name in result from FilePad query."""
        with open("degenerate_file.txt", "w") as f:
            f.write("Some file with some content")
        t = AddFilesTask(paths=["degenerate_file.txt"], identifiers=["some_identifier"], metadata={"key": "value"})
        t.run_task({})

        with open("degenerate_file.txt", "w") as f:
            f.write("Some other file with some other content BUT same file name")
        t = AddFilesTask(
            paths=["degenerate_file.txt"], identifiers=["some_other_identifier"], metadata={"key": "value"}
        )
        t.run_task({})

        os.remove("degenerate_file.txt")

        t = GetFilesByQueryTask(query={"metadata->key": "value"}, fizzle_degenerate_file_name=False)
        t.run_task({})
        # test successful if no exception raised

    def test_getfilesbyquerytask_raise_degenerate_file_name(self) -> None:
        """Tests on raising exception on degenerate file name from FilePad query."""
        with open("degenerate_file.txt", "w") as f:
            f.write("Some file with some content")
        t = AddFilesTask(paths=["degenerate_file.txt"], identifiers=["some_identifier"], metadata={"key": "value"})
        t.run_task({})

        with open("degenerate_file.txt", "w") as f:
            f.write("Some other file with some other content BUT same file name")
        t = AddFilesTask(
            paths=["degenerate_file.txt"], identifiers=["some_other_identifier"], metadata={"key": "value"}
        )
        t.run_task({})

        os.remove("degenerate_file.txt")

        t = GetFilesByQueryTask(query={"metadata->key": "value"}, fizzle_degenerate_file_name=True)
        with pytest.raises(ValueError):
            t.run_task({})
        # test successful if exception raised

    @pytest.mark.mongodb
    def test_getfilesbyquerytask_sort_ascending_name_run(self) -> None:
        """Tests on sorting queried files in ascending order."""
        file_contents = ["Some file with some content", "Some other file with some other content"]

        with open("degenerate_file.txt", "w") as f:
            f.write(file_contents[0])
        t = AddFilesTask(
            paths=["degenerate_file.txt"], identifiers=["some_identifier"], metadata={"key": "value", "sort_key": 0}
        )
        t.run_task({})

        with open("degenerate_file.txt", "w") as f:
            f.write(file_contents[-1])
        t = AddFilesTask(
            paths=["degenerate_file.txt"],
            identifiers=["some_other_identifier"],
            metadata={"key": "value", "sort_key": 1},
        )
        t.run_task({})

        os.remove("degenerate_file.txt")

        t = GetFilesByQueryTask(
            query={"metadata->key": "value"}, fizzle_degenerate_file_name=False, sort_key="sort_key", sort_direction=1
        )
        t.run_task({})

        with open("degenerate_file.txt") as f:
            assert file_contents[-1] == f.read()

    @pytest.mark.mongodb
    def test_getfilesbyquerytask_sort_descending_name_run(self) -> None:
        """Tests on sorting queried files in descending order."""
        file_contents = ["Some file with some content", "Some other file with some other content"]

        with open("degenerate_file.txt", "w") as f:
            f.write(file_contents[0])
        t = AddFilesTask(
            paths=["degenerate_file.txt"], identifiers=["some_identifier"], metadata={"key": "value", "sort_key": 10}
        )
        t.run_task({})

        with open("degenerate_file.txt", "w") as f:
            f.write(file_contents[-1])
        t = AddFilesTask(
            paths=["degenerate_file.txt"],
            identifiers=["some_other_identifier"],
            metadata={"key": "value", "sort_key": 20},
        )
        t.run_task({})

        os.remove("degenerate_file.txt")

        t = GetFilesByQueryTask(
            query={"metadata->key": "value"},
            fizzle_degenerate_file_name=False,
            sort_key="metadata.sort_key",
            sort_direction=-1,
        )
        t.run_task({})

        with open("degenerate_file.txt") as f:
            assert file_contents[0] == f.read()

        os.remove("degenerate_file.txt")

    @pytest.mark.mongodb
    def test_addfilesfrompatterntask_run(self) -> None:
        t = AddFilesTask(paths="*.yaml", directory=module_dir)
        t.run_task({})
        write_file_contents, _ = self.fp.get_file(self.paths[0])
        with open(self.paths[0]) as f:
            assert write_file_contents == f.read().encode()
        del_file_contents, _wdoc = self.fp.get_file(self.paths[1])
        with open(self.paths[1]) as f:
            assert del_file_contents == f.read().encode()

    def tearDown(self) -> None:
        self.fp.reset()
