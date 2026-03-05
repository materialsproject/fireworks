import pytest

from fireworks.scripts.mlaunch_run import mlaunch

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_mlaunch_report_version(capsys, arg) -> None:
    """Test mlaunch CLI version flag."""
    with pytest.raises(SystemExit, match="0"):
        mlaunch([arg])

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("mlaunch v")
    assert stderr == ""


def test_mlaunch_config_file_flags() -> None:
    """Test mlaunch CLI throws errors on missing config file flags."""
    num_jobs = "1"

    with pytest.raises(FileNotFoundError, match="launchpad_file '' does not exist!"):
        mlaunch([num_jobs, "-l", ""])

    with pytest.raises(FileNotFoundError, match="fworker_file 'missing_file' does not exist!"):
        mlaunch([num_jobs, "-w", "missing_file"])
