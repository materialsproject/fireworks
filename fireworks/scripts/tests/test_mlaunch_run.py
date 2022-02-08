import pytest

from fireworks.scripts.mlaunch_run import mlaunch

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_mlaunch_report_version(capsys, arg):
    """Test mlaunch CLI version flag."""

    with pytest.raises(SystemExit):
        ret_code = mlaunch([arg])
        assert ret_code == 0

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("mlaunch v")
    assert stderr == ""
