import pytest

from fireworks.scripts.qlaunch_run import qlaunch

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_qlaunch_report_version(capsys, arg):
    """Test qlaunch CLI version flag."""

    with pytest.raises(SystemExit):
        ret_code = qlaunch([arg])
        assert ret_code == 0

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("qlaunch v")
    assert stderr == ""
