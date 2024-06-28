import pytest

from fireworks import Firework, ScriptTask
from fireworks.core.launchpad import LaunchPad
from fireworks.scripts.lpad_run import lpad

__author__ = "Janosh Riebesell <janosh.riebesell@gmail.com>"


@pytest.fixture()
def lp(capsys):
    # prevent this fixture from polluting std{out,err} of tests that use it
    with capsys.disabled():
        lp = LaunchPad()
        lp.reset(password=None, require_password=False)

        yield lp

        lp.reset(password=None, require_password=False)


@pytest.mark.mongodb
@pytest.mark.parametrize(("detail", "expected_1", "expected_2"), [("count", "0\n", "1\n"), ("ids", "[]\n", "1\n")])
def test_lpad_get_fws(capsys, lp, detail, expected_1, expected_2) -> None:
    """Test lpad CLI get_fws command."""
    ret_code = lpad(["get_fws", "-d", detail])
    assert ret_code == 0

    # check correct output for empty launchpad
    stdout, stderr = capsys.readouterr()
    assert stdout == expected_1
    assert stderr == ""

    test_task = ScriptTask.from_str("python -c 'print(\"test_task\")'")
    fw = Firework(test_task)
    lp.add_wf(fw)
    stdout, stderr = capsys.readouterr()  # clear stdout from lp.add_wf(fw)

    ret_code = lpad(["get_fws", "-d", detail])
    assert ret_code == 0

    # check correct output for 1 fw in launchpad
    stdout, stderr = capsys.readouterr()
    assert stdout == expected_2
    assert stderr == ""


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_lpad_report_version(capsys, arg) -> None:
    """Test lpad CLI version flag."""
    with pytest.raises(SystemExit, match="0"):
        lpad([arg])

    stdout, stderr = capsys.readouterr()

    assert stdout.startswith("lpad v")
    assert stderr == ""


def test_lpad_config_file_flags() -> None:
    """Test lpad CLI throws errors on missing config file flags."""
    with pytest.raises(FileNotFoundError, match="launchpad_file '' does not exist!"):
        lpad(["-l", "", "get_fws"])

    with pytest.raises(FileNotFoundError, match="fworker_file 'missing_file' does not exist!"):
        lpad(["recover_offline", "-w", "missing_file"])
