import pytest

import fireworks as fw
from fireworks.user_objects.firetasks.script_task import ScriptTask


def assert_datetime_almost_equal(a, b, tol=0.001):
    # checks time diff between two is less than tol *seconds*
    # sometimes tzinfo is set, so just strip that out
    a = a.replace(tzinfo=None)
    b = b.replace(tzinfo=None)
    assert abs((a - b).total_seconds()) < tol


def assert_fireworks_equal(a, b):
    assert a.to_dict() == b.to_dict()


def assert_workflows_equal(a, b):
    d_a, d_b = a.to_dict(), b.to_dict()
    for k in ['created_on', 'updated_on']:
        val_a, val_b = d_a.pop(k), d_b.pop(k)
        assert_datetime_almost_equal(val_a, val_b)
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
    firework2 = fw.Firework(ScriptTask.from_str("echo '2'"))
    firework3 = fw.Firework(ScriptTask.from_str("echo '3'"),
                            parents=[firework1, firework2])
    return fw.Workflow([firework1, firework2, firework3])


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

    fw1, fw2, _ = workflow.fws

    firework1 = lp.get_fw_by_id(fw1.fw_id)
    firework2 = lp.get_fw_by_id(fw2.fw_id)

    assert_fireworks_equal(firework1, fw1)
    assert_fireworks_equal(firework2, fw2)

def test_get_wf_by_fw_id(lp, workflow):
    lp.add_wf(workflow)

    work = lp.get_wf_by_fw_id(workflow.fws[0].fw_id)

    assert_workflows_equal(work, workflow)

def test_checkout_fw(lp, workflow):
    lp.add_wf(workflow)

    firework, _ = lp.checkout_fw(fw.FWorker(), launch_dir='.')

    assert isinstance(firework, fw.Firework)

def test_checkout_fw_specific(lp, workflow):
    lp.add_wf(workflow)

    fw_to_get = workflow.fws[0]

    firework, _ = lp.checkout_fw(fw.FWorker(), launch_dir='.',
                                 fw_id=fw_to_get.fw_id)

    # fireworks aren't strictly equal any more as checking out has modified it
    # instead...
    assert firework.fw_id == fw_to_get.fw_id
    assert firework.spec == fw_to_get.spec

def test_checkout_multiple(lp, workflow):
    lp.add_wf(workflow)

    ref_fw1, ref_fw2, ref_fw3 = workflow.fws

    fw1, _ = lp.checkout_fw(fw.FWorker(), '.')
    fw2, _ = lp.checkout_fw(fw.FWorker(), '.')

    print(fw1.fw_id, fw2.fw_id)

    print(ref_fw1.fw_id, ref_fw2.fw_id)

    # at this point, we should have checked out ref_fw1 and ref_fw2
    # ref_fw3 has unsatisfied dependencies
    for ref_firework in [ref_fw1, ref_fw2]:
        assert any(firework.fw_id == ref_firework.fw_id
                   for firework in (fw1, fw2))
