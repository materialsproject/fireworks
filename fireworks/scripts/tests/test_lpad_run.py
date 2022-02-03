import pytest

from fireworks import Firework, ScriptTask
from fireworks.core.launchpad import LaunchPad
from fireworks.scripts.lpad_run import lpad

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.fixture(scope="function")
def lp(capsys):
    # prevent this fixture from polluting std{out,err} of tests that use it
    with capsys.disabled():
        lp = LaunchPad()
        lp.reset(password=None, require_password=False)

        yield lp

        lp.reset(password=None, require_password=False)


@pytest.mark.parametrize("detail, expec1, expec2", [("count", "0\n", "1\n"), ("ids", "[]\n", "1\n")])
def test_lpad_get_fws(capsys, lp, detail, expec1, expec2):
    """Test lpad CLI get_fws command."""

    ret_code = lpad(["get_fws", "-d", detail])
    assert ret_code == 0

    # check correct output for empty launchpad
    stdout, stderr = capsys.readouterr()
    assert stdout == expec1
    assert stderr == ""

    test_task = ScriptTask.from_str("python -c 'print(\"test_task\")'")
    fw = Firework(test_task)
    lp.add_wf(fw)
    stdout, stderr = capsys.readouterr()  # clear stdout from lp.add_wf(fw)

    ret_code = lpad(["get_fws", "-d", detail])
    assert ret_code == 0

    # check correct output for 1 fw in launchpad
    stdout, stderr = capsys.readouterr()
    assert stdout == expec2
    assert stderr == ""


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_lpad_report_version(capsys, arg):
    """Test lpad CLI version flag."""

    with pytest.raises(SystemExit):
        ret_code = lpad([arg])
        assert ret_code == 0

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("lpad v")
    assert stderr == ""
