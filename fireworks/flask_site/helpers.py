from fireworks.core.launchpad import LaunchPad
DEFAULT_LPAD_YAML = "my_launchpad.yaml"
import traceback, os
from fireworks.fw_config import RESERVATION_EXPIRATION_SECS, \
    RUN_EXPIRATION_SECS, PW_CHECK_NUM, MAINTAIN_INTERVAL, CONFIG_FILE_DIR, \
    LAUNCHPAD_LOC

def get_lp():
    try:
        # if not args.launchpad_file and os.path.exists(os.path.join(args.config_dir, DEFAULT_LPAD_YAML)):
        launchpad_file = os.path.join(CONFIG_FILE_DIR, DEFAULT_LPAD_YAML)
        return LaunchPad.from_file(launchpad_file).to_dict()
    except:
        traceback.print_exc()
        err_message = 'FireWorks was not able to connect to MongoDB. Is the server running? The database file specified was {}.'.format(launchpad_file)
        if not launchpad_file:
            err_message += ' Type "lpad init" if you would like to set up a file that specifies location and credentials of your Mongo database (otherwise use default localhost configuration).'
        raise ValueError(err_message)

def get_totals(states, lp):
    fw_stats = {}
    wf_stats = {}
    for state in states:
        fw_stats[state] = lp.get_fw_ids(query={'state': state}, count_only=True)
        wf_stats[state] = lp.get_wf_ids(query={'state': state}, count_only=True)
    return {"fw_stats": fw_stats, "wf_stats":wf_stats}    