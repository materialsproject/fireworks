import pytest

from fireworks.scripts.qlaunch_run import qlaunch

from . import module_dir

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_qlaunch_report_version(capsys, arg) -> None:
    """Test qlaunch CLI version flag."""
    with pytest.raises(SystemExit):
        qlaunch([arg])

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("qlaunch v")
    assert stderr == ""


def test_qlaunch_config_file_flags() -> None:
    """Test qlaunch CLI throws errors on missing config file flags."""
    # qadapter.yaml is mandatory, test for ValueError if missing
    with pytest.raises(ValueError, match="No path specified for qadapter_file."):
        qlaunch([])

    # qadapter.yaml is mandatory, test for ValueError if missing
    with pytest.raises(FileNotFoundError, match="qadapter_file '' does not exist!"):
        qlaunch(["-q", ""])

    with pytest.raises(FileNotFoundError, match="qadapter_file 'missing_file' does not exist!"):
        qlaunch(["-q", "missing_file"])

    qadapter_file = f"{module_dir}/__init__.py"  # just any file that passes os.path.exists()
    with pytest.raises(FileNotFoundError, match="launchpad_file '' does not exist!"):
        qlaunch(["-q", qadapter_file, "-l", ""])
