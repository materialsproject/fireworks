import pytest

from fireworks.scripts.rlaunch_run import rlaunch

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_rlaunch_report_version(capsys, arg):
    """Test rlaunch CLI version flag."""

    with pytest.raises(SystemExit):
        ret_code = rlaunch([arg])
        assert ret_code == 0

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("rlaunch v")
    assert stderr == ""
