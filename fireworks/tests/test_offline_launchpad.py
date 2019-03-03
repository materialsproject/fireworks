import fireworks as fw

def test_get_new_launch_id():
    lp = fw.OfflineLaunchPad()
    lp.reset()

    assert lp.get_new_launch_id() == 1
    assert lp.get_new_launch_id() == 2
    assert lp.get_new_launch_id() == 3

    lp.reset()

    assert lp.get_new_launch_id() == 1
    assert lp.get_new_launch_id() == 2
    assert lp.get_new_launch_id() == 3

def test_get_new_fw_id():
    lp = fw.OfflineLaunchPad()
    lp.reset()

    assert lp.get_new_fw_id() == 1
    assert lp.get_new_fw_id() == 2
    assert lp.get_new_fw_id() == 3

    lp.reset()

    assert lp.get_new_fw_id() == 1
    assert lp.get_new_fw_id() == 2
    assert lp.get_new_fw_id() == 3
