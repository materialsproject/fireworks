import pytest

from fireworks.scripts.rlaunch_run import rlaunch

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_rlaunch_report_version(capsys, arg) -> None:
    """Test rlaunch CLI version flag."""
    with pytest.raises(SystemExit, match="0"):
        rlaunch([arg])

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("rlaunch v")
    assert stderr == ""


def test_rlaunch_config_file_flags() -> None:
    """Test rlaunch CLI throws errors on missing config file flags."""
    with pytest.raises(FileNotFoundError, match="launchpad_file '' does not exist!"):
        rlaunch(["-l", ""])

    with pytest.raises(FileNotFoundError, match="fworker_file 'missing_file' does not exist!"):
        rlaunch(["-w", "missing_file"])
