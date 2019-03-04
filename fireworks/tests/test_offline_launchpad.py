import pytest

import fireworks as fw
from fireworks.user_objects.firetasks.script_task import ScriptTask


def assert_fireworks_equal(a, b):
    assert a.to_dict() == b.to_dict()


def assert_workflows_equal(a, b):
    d_a, d_b = a.to_dict(), b.to_dict()
    for k in ['created_on', 'updated_on']:
        val_a, val_b = d_a.pop(k), d_b.pop(k)
    fws_a, fws_b = d_a.pop('fws'), d_b.pop('fws')
    for fw_a, fw_b in zip(sorted(fws_a, key=lambda x: x['fw_id']),
                          sorted(fws_b, key=lambda x: x['fw_id'])):
        assert fw_a == fw_b
    assert d_a == d_b


@pytest.fixture
def lp():
    lp = fw.OfflineLaunchPad()
    lp.reset()

    return lp

@pytest.fixture
def workflow():
    firework1 = fw.Firework(ScriptTask.from_str("echo '1'"))
    firework2 = fw.Firework(ScriptTask.from_str("echo '1'"),
                            parents=firework1)
    return fw.Workflow([firework1, firework2])


def test_get_new_launch_id(lp):
    assert lp.get_new_launch_id() == 1
    assert lp.get_new_launch_id() == 2
    assert lp.get_new_launch_id() == 3

    lp.reset()

    assert lp.get_new_launch_id() == 1
    assert lp.get_new_launch_id() == 2
    assert lp.get_new_launch_id() == 3

def test_get_new_fw_id(lp):
    assert lp.get_new_fw_id() == 1
    assert lp.get_new_fw_id() == 2
    assert lp.get_new_fw_id() == 3

    lp.reset()

    assert lp.get_new_fw_id() == 1
    assert lp.get_new_fw_id() == 2
    assert lp.get_new_fw_id() == 3


def test_not_run_exists(lp):
    assert not lp.run_exists()


def test_run_exists(lp, workflow):
    lp.add_wf(workflow)

    assert lp.run_exists()

def test_get_fw_by_id(lp, workflow):
    lp.add_wf(workflow)

    fw1, fw2 = workflow.fws

    firework1 = lp.get_fw_by_id(fw1.fw_id)
    firework2 = lp.get_fw_by_id(fw2.fw_id)

    assert_fireworks_equal(firework1, fw1)
    assert_fireworks_equal(firework2, fw2)

def test_get_wf_by_fw_id(lp, workflow):
    lp.add_wf(workflow)

    work = lp.get_wf_by_fw_id(workflow.fws[0].fw_id)

    assert_workflows_equal(work, workflow)
